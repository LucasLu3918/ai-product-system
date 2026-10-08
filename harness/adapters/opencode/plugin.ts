import { createHash } from "node:crypto"
import { appendFile, chmod, mkdir, stat, writeFile } from "node:fs/promises"
import { homedir } from "node:os"
import { dirname, join, resolve } from "node:path"
import { spawnSync } from "node:child_process"

const SYSTEM_ROOT = __AIPS_SYSTEM_ROOT__
const MAX_CONTEXT_BYTES = 12000
const MAX_TRACE_BYTES = 512 * 1024

type ContextEntry = { key: string; at: number; root: string; prompt: string; manifest: Record<string, any> | null; reason?: string; durationMs: number }

function lastUserText(messages: any[]): string {
  for (let i = messages.length - 1; i >= 0; i -= 1) {
    const message = messages[i]
    const role = message?.info?.role ?? message?.role
    if (role !== "user") continue
    const parts = message?.parts ?? message?.content ?? []
    if (typeof parts === "string") return parts
    if (Array.isArray(parts)) return parts.map((part) => typeof part === "string" ? part : part?.text ?? "").filter(Boolean).join("\n")
    return ""
  }
  return ""
}

function invoke(binary: string, args: string[], cwd: string, timeout: number): { status: number | null; stdout: string; error?: string } {
  const result = spawnSync(binary, args, { cwd, encoding: "utf8", timeout, maxBuffer: 2 * 1024 * 1024, shell: false })
  if (result.error) return { status: result.status, stdout: "", error: result.error.message }
  return { status: result.status, stdout: result.stdout ?? "", error: result.stderr?.slice(0, 600) }
}

function hash(value: string): string { return createHash("sha256").update(value).digest("hex").slice(0, 16) }

function compactManifest(manifest: Record<string, any>): { body: string; truncated: boolean } {
  const full = JSON.stringify(manifest)
  if (Buffer.byteLength(full) <= MAX_CONTEXT_BYTES) return { body: full, truncated: false }
  const task = manifest.task
  const summary: Record<string, any> = {
    version: manifest.version,
    runtime: manifest.runtime,
    project_mode: manifest.project?.mode,
    task: task && { classification: task.classification, readiness: task.readiness },
    selected_protocols: manifest.context?.system_protocol_routes,
    intelligence_topics: manifest.context?.intelligence_topics,
    retrieval: manifest.context?.retrieval,
    creative_workspace: manifest.aips_creative_workspace,
    intelligence: manifest.intelligence && { readiness: manifest.intelligence.readiness, review: manifest.intelligence.review },
    freshness: manifest.freshness,
    instruction_resolution: manifest.instruction_resolution && {
      status: manifest.instruction_resolution.status,
      requires_resolution: manifest.instruction_resolution.requires_resolution,
    },
    fail_policy: manifest.fail_policy,
    aips_context_budget: { truncated: true, original_bytes: Buffer.byteLength(full), max_bytes: MAX_CONTEXT_BYTES },
  }
  let body = JSON.stringify(summary)
  if (Buffer.byteLength(body) > MAX_CONTEXT_BYTES) {
    summary.intelligence_topics = Array.isArray(summary.intelligence_topics) ? summary.intelligence_topics.slice(0, 8) : summary.intelligence_topics
    summary.fail_policy = summary.fail_policy && { mode: summary.fail_policy.mode, reasons: Array.isArray(summary.fail_policy.reasons) ? summary.fail_policy.reasons.slice(0, 8) : [] }
    body = JSON.stringify(summary)
  }
  return Buffer.byteLength(body) <= MAX_CONTEXT_BYTES ? { body, truncated: true } : { body: "", truncated: true }
}

function tracePath(): string {
  return join(process.env.XDG_STATE_HOME || join(homedir(), ".local/state"), "aips/opencode/events.jsonl")
}

async function trace(event: Record<string, any>): Promise<void> {
  const path = tracePath()
  try {
    await mkdir(dirname(path), { recursive: true, mode: 0o700 })
    try {
      const info = await stat(path)
      if (info.size > MAX_TRACE_BYTES) await writeFile(path, "", { mode: 0o600 })
    } catch { /* first event */ }
    await appendFile(path, JSON.stringify({ at: new Date().toISOString(), runtime: "opencode", ...event }) + "\n", { mode: 0o600 })
    await chmod(path, 0o600)
  } catch (error) {
    console.error(`AIPS trace could not be recorded: ${error instanceof Error ? error.name : "Error"}`)
  }
}

function invokeGuard(python: string, guard: string, kind: "write" | "shell", input: Record<string, any>, cwd: string): Record<string, any> {
  const args = kind === "write"
    ? [guard, "write", "--tool", String(input.action), "--resources", JSON.stringify(input.resources ?? []), "--root", String(input.root), "--manifest", JSON.stringify(input.manifest ?? {})]
    : [guard, "shell", "--command", String(input.command ?? ""), "--cwd", String(input.cwd ?? cwd), "--root", String(input.root)]
  const result = invoke(python, args, cwd, 5000)
  if (result.stdout) {
    try { return JSON.parse(result.stdout) } catch { /* fail closed below */ }
  }
  return { decision: "DENY", level: "L2", reason: result.error || "AIPS native guard unavailable" }
}

function policyReasonCode(decision: Record<string, any>): string {
  if (decision.decision === "ALLOW") return "policy_allow"
  const reason = String(decision.reason ?? "").toLowerCase()
  if (reason.includes("missing or ambiguous")) return "target_missing"
  if (reason.includes("escapes project root")) return "target_escape"
  if (reason.includes("readiness is not ready")) return "intelligence_not_ready"
  if (reason.includes("freshness is not current")) return "intelligence_stale"
  if (reason.includes("instruction authority conflict")) return "instruction_conflict"
  if (reason.includes("creative output target already exists")) return "creative_target_exists"
  if (reason.includes("supported asset extension")) return "creative_target_unsupported"
  if (reason.includes("inside git workspaces")) return "creative_git_workspace"
  if (reason.includes("outside the supported")) return "action_unsupported"
  if (reason.includes("external actions require")) return "external_approval_required"
  return "policy_deny"
}

export default {
  id: "aips-opencode",
  async setup(ctx) {
    const aips = process.env.AIPS_CLI || join(SYSTEM_ROOT, "bin/aips")
    const python = process.env.AIPS_GUARD_PYTHON || "python3"
    const guard = join(SYSTEM_ROOT, "scripts/opencode_native_guard.py")
    const cache = new Map<string, ContextEntry>()
    const maxCache = 32

    async function sessionRoot(sessionID: string): Promise<{ root: string; source: "directory" | "location_directory" | "worktree" } | null> {
      try {
        const value = await ctx.session.get({ sessionID })
        const session = value?.data ?? value
        const candidates = [
          ["directory", session?.directory],
          ["location_directory", session?.location?.directory],
          ["worktree", session?.worktree],
        ] as const
        const match = candidates.find(([, directory]) => typeof directory === "string" && directory.trim())
        if (!match) return null
        return { root: resolve(match[1] as string), source: match[0] }
      } catch {
        return null
      }
    }

    async function contextFor(sessionID: string, messages: any[], root: string, targetPath = root, force = false, promptOverride?: string): Promise<ContextEntry> {
      const prompt = promptOverride ?? lastUserText(messages)
      const key = `${root}|${sessionID}|${hash(prompt)}|${targetPath}`
      const current = cache.get(sessionID)
      if (!force && current && current.key === key) return current
      const started = performance.now()
      const result = invoke(aips, ["intelligence", "context", "--runtime", "opencode", "--project", root,
        "--prompt", prompt, "--target-path", targetPath, "--format", "json", "--compact"], root, 15000)
      let manifest: Record<string, any> | null = null
      let reason = result.error || "AIPS context command failed"
      if (result.status === 0) {
        try {
          const parsed = JSON.parse(result.stdout)
          if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
            manifest = parsed
            reason = ""
          } else reason = "AIPS context returned a non-object manifest"
        } catch { reason = "AIPS context returned invalid JSON" }
      }
      const entry = { key, at: Date.now(), root, prompt, manifest, reason, durationMs: Math.round(performance.now() - started) }
      cache.set(sessionID, entry)
      while (cache.size > maxCache) cache.delete(cache.keys().next().value as string)
      return entry
    }

    await ctx.session.hook("context", async (event) => {
      await trace({ event: "context", status: "entered" })
      const hookStarted = performance.now()
      const resolvedSession = await sessionRoot(event.sessionID)
      if (!resolvedSession) {
        event.system.push({ type: "text", text: "AIPS Turn Context unavailable: the active Session directory could not be resolved. Project writes are denied until AIPS context is restored." })
        await trace({ event: "context", status: "unavailable", session: hash(event.sessionID), reason_code: "session_directory_unavailable" })
        return
      }
      const { root } = resolvedSession
      const entry = await contextFor(event.sessionID, event.messages as any[], root)
      const classification = entry.manifest?.task?.classification ?? {}
      if (entry.manifest && entry.manifest.project?.mode === "EPHEMERAL" && classification.domain === "creative") {
        const profile = invoke(python, [join(SYSTEM_ROOT, "scripts/creative_workspace_profile.py"), "scan", "--project", root], root, 8000)
        try {
          const result = JSON.parse(profile.stdout)
          entry.manifest.aips_creative_workspace = {
            status: profile.status === 0 ? "READY" : "UNAVAILABLE",
            asset_count: result.asset_count ?? 0,
            assets: Array.isArray(result.assets) ? result.assets.slice(0, 24) : [],
            profile_files: Array.isArray(result.profile_files) ? result.profile_files.slice(0, 24) : [],
            truncated: Boolean(result.truncated || (result.assets?.length ?? 0) > 24),
            output_policy: "Use a new versioned path; do not overwrite existing assets. Run `aips creative next-version` to suggest the next free path.",
          }
        } catch {
          entry.manifest.aips_creative_workspace = { status: "UNAVAILABLE", reason_code: "read_only_scan_failed", output_policy: "Create a new versioned path; never overwrite existing assets." }
        }
      }
      const encoded = entry.manifest ? compactManifest(entry.manifest) : { body: "", truncated: false }
      const text = encoded.body
        ? `AIPS Turn Context (automatically loaded; transient):\n${encoded.body}`
        : `AIPS Turn Context unavailable: ${entry.reason || "the compact manifest exceeds its fixed size budget"}. Do not perform project writes until the required AIPS context is restored. Shell and MCP/custom-tool effects are not fully covered by the native file guard.`
      event.system.push({ type: "text", text })
      const task = entry.manifest?.task?.classification ?? {}
      await trace({
        event: "context", status: encoded.body ? "delivered" : "unavailable", session: hash(event.sessionID), project: hash(root),
        domain: task.domain ?? "unknown", intent: task.intent ?? "unknown", effect: task.effect ?? "unknown",
        readiness: entry.manifest?.intelligence?.readiness ?? "unknown", workflow_count: Array.isArray(entry.manifest?.context?.system_protocol_routes?.protocols) ? entry.manifest.context.system_protocol_routes.protocols.length : 0,
        project_mode: entry.manifest?.project?.mode ?? "UNKNOWN",
        session_root_source: resolvedSession.source,
        duration_ms: Math.round(performance.now() - hookStarted), context_command_ms: entry.durationMs,
        context_bytes: encoded.body ? Buffer.byteLength(encoded.body) : 0, truncated: encoded.truncated,
        creative_asset_count: entry.manifest?.aips_creative_workspace?.asset_count ?? 0,
      })
    })
    await ctx.permission.hook("evaluate", async (event) => {
      if (!["edit", "write", "patch", "apply_patch"].includes(event.action)) return
      const resolvedSession = await sessionRoot(event.sessionID)
      if (!resolvedSession) {
        event.effect = "deny"
        event.message = "AIPS native write guard: active Session directory could not be resolved"
        await trace({ event: "permission", decision: "DENY", level: "L2", session: hash(event.sessionID), action: event.action, reason_code: "session_directory_unavailable" })
        return
      }
      const { root } = resolvedSession
      const messages = await ctx.session.context({ sessionID: event.sessionID })
      const recent = cache.get(event.sessionID)
      const prompt = recent?.root === root ? recent.prompt : undefined
      const entry = await contextFor(event.sessionID, messages as any[], root, event.resources[0] ?? root, true, prompt)
      const decision = invokeGuard(python, guard, "write", { action: event.action, resources: [...event.resources], manifest: entry.manifest ?? {}, root }, root)
      if (decision.decision !== "ALLOW") {
        event.effect = "deny"
        event.message = `AIPS ${decision.level ?? "L2"} native write guard: ${decision.reason ?? "context unavailable"}`
      }
      const task = entry.manifest?.task?.classification ?? {}
      await trace({ event: "permission", decision: decision.decision, level: decision.level ?? "L0", session: hash(event.sessionID), project: hash(root), action: event.action, domain: task.domain ?? "unknown", intent: task.intent ?? "unknown", readiness: entry.manifest?.intelligence?.readiness ?? "unknown", project_mode: entry.manifest?.project?.mode ?? "UNKNOWN", session_root_source: resolvedSession.source, reason_code: policyReasonCode(decision) })
    })

    await ctx.shell.hook("create.before", async (event) => {
      const cwd = resolve(event.cwd || process.cwd())
      // This hook contract has no session ID; cwd is the narrowest live scope
      // available and prevents falling back to the plugin setup directory.
      const decision = invokeGuard(python, guard, "shell", { command: event.command, cwd, root: cwd }, cwd)
      if (decision.decision !== "ALLOW") {
        console.error(`AIPS native Shell guard: ${decision.reason ?? "unsupported command"}`)
        event.command = "false"
      }
      await trace({ event: "shell", decision: decision.decision, level: decision.level ?? "L0", project: hash(cwd), reason_code: policyReasonCode(decision) })
    })
    await trace({ event: "plugin", status: "ready" })
  },
}
