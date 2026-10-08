import { createHash } from "node:crypto"
import { appendFile, chmod, mkdir, stat, writeFile } from "node:fs/promises"
import { homedir } from "node:os"
import { dirname, join, resolve } from "node:path"
import { spawn, spawnSync } from "node:child_process"

const SYSTEM_ROOT = __AIPS_SYSTEM_ROOT__
const MAX_CONTEXT_BYTES = 12000
const MAX_TRACE_BYTES = 512 * 1024

type ContextEntry = { key: string; at: number; root: string; prompt: string; manifest: Record<string, any> | null; reason?: string; durationMs: number }
type CreativeToolInput = {
  action: "prepare" | "configure" | "discover" | "preflight" | "execute"
  settings?: Record<string, unknown>
  bundle?: string
  scope?: string
  character_id?: string
  character_name?: string
  summary?: string
  style_intent?: string
  prompt?: string
  identity_features?: string[]
}

function contextMessages(value: any): any[] {
  if (Array.isArray(value)) return value
  if (Array.isArray(value?.messages)) return value.messages
  if (Array.isArray(value?.data)) return value.data
  if (Array.isArray(value?.data?.messages)) return value.data.messages
  return []
}

function lastUserText(value: any): string {
  const messages = contextMessages(value)
  for (let i = messages.length - 1; i >= 0; i -= 1) {
    const message = messages[i]
    const role = message?.info?.role ?? message?.role ?? message?.type
    if (role !== "user") continue
    const parts = message?.parts ?? message?.content ?? message?.text ?? []
    if (typeof parts === "string") return parts
    if (Array.isArray(parts)) return parts.map((part) => typeof part === "string" ? part : part?.text ?? "").filter(Boolean).join("\n")
    return ""
  }
  return ""
}

function invoke(binary: string, args: string[], cwd: string, timeout: number, input?: string): { status: number | null; stdout: string; error?: string } {
  const result = spawnSync(binary, args, { cwd, input, encoding: "utf8", timeout, maxBuffer: 2 * 1024 * 1024, shell: false })
  if (result.error) return { status: result.status, stdout: "", error: result.error.message }
  return { status: result.status, stdout: result.stdout ?? "", error: result.stderr?.slice(0, 600) }
}

function invokeAsync(binary: string, args: string[], cwd: string, timeout: number, signal?: AbortSignal, input?: string): Promise<{ status: number | null; stdout: string; error?: string }> {
  return new Promise((resolvePromise) => {
    const child = spawn(binary, args, { cwd, stdio: [input === undefined ? "ignore" : "pipe", "pipe", "pipe"], shell: false })
    child.stdin?.on("error", () => { /* process error/close owns failure reporting */ })
    child.stdin?.end(input)
    const chunks: Buffer[] = []
    let size = 0
    let settled = false
    let outputError = ""
    const finish = (value: { status: number | null; stdout: string; error?: string }) => {
      if (settled) return
      settled = true
      clearTimeout(timer)
      signal?.removeEventListener("abort", abort)
      resolvePromise(value)
    }
    const abort = () => { child.kill("SIGTERM"); finish({ status: null, stdout: "", error: "Creative execution was cancelled" }) }
    const timer = setTimeout(() => { child.kill("SIGTERM"); finish({ status: null, stdout: "", error: "Creative execution timed out" }) }, timeout)
    signal?.addEventListener("abort", abort, { once: true })
    child.stdout.on("data", (chunk: Buffer) => {
      size += chunk.length
      if (size > 64 * 1024) { child.kill("SIGTERM"); finish({ status: null, stdout: "", error: "AIPS creative response exceeded its output limit" }); return }
      chunks.push(chunk)
    })
    child.stderr.on("data", (chunk: Buffer) => { outputError += chunk.toString("utf8").slice(0, 512 - outputError.length) })
    child.on("error", (error) => finish({ status: null, stdout: "", error: error.name }))
    child.on("close", (status) => finish({ status, stdout: Buffer.concat(chunks).toString("utf8"), error: outputError.slice(0, 512) || undefined }))
  })
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
  if (typeof decision.reason_code === "string") return decision.reason_code
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
    const dispatchMessages = new Map<string, { root: string; messages: any[] }>()
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
      dispatchMessages.set(event.sessionID, { root, messages: contextMessages(event.messages).slice(-64) })
      while (dispatchMessages.size > maxCache) dispatchMessages.delete(dispatchMessages.keys().next().value as string)
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
    await ctx.tool.transform((editor) => {
      editor.add({
        name: "creative_execution",
        description: "Discover installed local commands, prepare character profiles, configure a new validated Bundle version, run read-only preflight, or explicitly generate raster artwork. Never replace requested detailed illustration with hand-written SVG when blocked. Load creative-calibration, visual-direction and visual-quality-review at their stages. No cloud provider or model download; file validity, visual quality and user acceptance are separate.",
        input: {
          type: "object",
          properties: {
            action: { type: "string", enum: ["prepare", "configure", "discover", "preflight", "execute"] },
            settings: {
              type: "object", additionalProperties: false,
              description: "Create a configured Bundle version; observed provenance only. No install, download, cloud or arbitrary output-path fields.",
              properties: {
                provider: { type: "string", enum: ["mflux_local", "comfyui_local"] },
                runtime: { type: "string", minLength: 1, maxLength: 240 },
                runtime_version: { type: "string", minLength: 1, maxLength: 240 },
                mflux_executable: { type: "string", minLength: 1, maxLength: 1000 },
                model: { type: "object", additionalProperties: false, properties: {
                  id: { type: "string", minLength: 1, maxLength: 240 },
                  revision: { type: "string", minLength: 1, maxLength: 240 },
                  local_path: { type: "string", minLength: 1, maxLength: 1000 },
                  license: { type: "string", minLength: 1, maxLength: 1000 },
                  license_source: { type: "string", minLength: 1, maxLength: 2000 },
                } },
                comfyui: { type: "object", additionalProperties: false, properties: {
                  base_url: { type: "string" }, workflow_path: { type: "string" },
                  checkpoint_node_id: { type: "string" }, checkpoint_name: { type: "string" }, model_id: { type: "string" },
                  prompt_node_id: { type: "string" }, latent_node_id: { type: "string" }, sampler_node_id: { type: "string" },
                  save_node_id: { type: "string" }, input_image_node_id: { type: "string" }, input_image_name: { type: "string" },
                } },
                width: { type: "integer", minimum: 64, maximum: 2048 }, height: { type: "integer", minimum: 64, maximum: 2048 },
                steps: { type: "integer", minimum: 1, maximum: 100 }, seed: { type: "integer" },
                max_retries: { type: "integer", minimum: 0, maximum: 2 }, timeout_seconds: { type: "integer", minimum: 1, maximum: 3600 },
                prompt: { type: "string", minLength: 1, maxLength: 4000 }, operation: { type: "string", enum: ["generate", "edit"] },
                input_image: { type: "string" }, input_images: { type: "array", maxItems: 8, items: { type: "string" } },
              },
            },
            bundle: { type: "string", minLength: 1, maxLength: 240 },
            scope: { type: "string", minLength: 1, maxLength: 240 },
            character_id: { type: "string", minLength: 1, maxLength: 64, pattern: "^[a-z0-9][a-z0-9_-]{0,63}$" },
            character_name: { type: "string", minLength: 1, maxLength: 120 },
            summary: { type: "string", minLength: 1, maxLength: 600 },
            style_intent: { type: "string", minLength: 1, maxLength: 600 },
            prompt: { type: "string", minLength: 1, maxLength: 4000 },
            identity_features: { type: "array", minItems: 1, maxItems: 12, items: { type: "string", minLength: 1, maxLength: 160 } },
          },
          required: ["action"],
          additionalProperties: false,
        },
        async execute(input, toolContext) {
          const request = input as CreativeToolInput
          const validAction = request && ["prepare", "configure", "discover", "preflight", "execute"].includes(request.action)
          const validBundle = typeof request?.bundle === "string" && request.bundle.length > 0 && request.bundle.length <= 240 && !request.bundle.startsWith("/") && !request.bundle.split(/[\\/]/).includes("..")
          const validPrepare = typeof request?.scope === "string" && request.scope.length > 0 && request.scope.length <= 240 && !request.scope.startsWith("/") && !request.scope.split(/[\\/]/).includes("..")
            && typeof request.character_id === "string" && /^[a-z0-9][a-z0-9_-]{0,63}$/.test(request.character_id)
            && typeof request.character_name === "string" && request.character_name.length > 0 && request.character_name.length <= 120
            && typeof request.summary === "string" && request.summary.length > 0 && request.summary.length <= 600
            && typeof request.style_intent === "string" && request.style_intent.length > 0 && request.style_intent.length <= 600
            && typeof request.prompt === "string" && request.prompt.length > 0 && request.prompt.length <= 4000
            && Array.isArray(request.identity_features) && request.identity_features.length > 0 && request.identity_features.length <= 12
            && request.identity_features.every((item) => typeof item === "string" && item.length > 0 && item.length <= 160)
          const validConfigure = request.settings && typeof request.settings === "object" && !Array.isArray(request.settings) && Buffer.byteLength(JSON.stringify(request.settings)) <= 32 * 1024
          if (!validAction || (request.action === "prepare" ? (!validPrepare || validBundle) : request.action === "discover" ? (validBundle || request.scope !== undefined) : (!validBundle || request.scope !== undefined)) || (request.action === "configure" ? !validConfigure : request.settings !== undefined)) {
            return { content: JSON.stringify({ status: "BLOCKED", reason_code: "creative_bundle_invalid" }) }
          }
          const resolvedSession = await sessionRoot(toolContext.sessionID)
          if (!resolvedSession) return { content: JSON.stringify({ status: "BLOCKED", reason_code: "session_directory_unavailable" }) }
          const { root } = resolvedSession
          const nativeContext = await ctx.session.context({ sessionID: toolContext.sessionID })
          const dispatched = dispatchMessages.get(toolContext.sessionID)
          const messages = (dispatched?.root === root ? dispatched.messages : contextMessages(nativeContext)).slice(-64)
          const policy = invoke(python, [join(SYSTEM_ROOT, "scripts/creative_request_policy.py")], root, 5000, JSON.stringify({ action: request.action, messages }))
          let authorization: Record<string, any> = { allowed: false, reason_code: "creative_authorization_unavailable" }
          try { authorization = JSON.parse(policy.stdout) } catch { /* fail closed */ }
          if (policy.status !== 0 || authorization.allowed !== true) {
            await trace({ event: "creative_execution", decision: "DENY", project: hash(root), reason_code: authorization.reason_code })
            return { content: JSON.stringify({ status: "BLOCKED", reason_code: authorization.reason_code, next_action: "clarify_current_creative_request", fallback_allowed: false,
              context_diagnostic: { message_count: messages.length, source: dispatched?.root === root ? "active_dispatch" : "session_context" } }) }
          }
          const entry = await contextFor(toolContext.sessionID, messages, root, root, true, authorization.basis_prompt || undefined)
          if (!entry.manifest || entry.manifest.project?.mode !== "EPHEMERAL") {
            await trace({ event: "creative_execution", decision: "DENY", project: hash(root), reason_code: "creative_ephemeral_required" })
            return { content: JSON.stringify({ status: "BLOCKED", reason_code: "creative_ephemeral_required" }) }
          }
          const classification = entry.manifest.task?.classification ?? {}
          if (!["preflight", "discover"].includes(request.action) && (classification.domain !== "creative" || (request.action === "prepare" ? classification.intent !== "create" : !["create", "modify"].includes(classification.intent)))) {
            return { content: JSON.stringify({ status: "BLOCKED", reason_code: "creative_intent_required" }) }
          }
          if (request.action === "execute") {
            const preflight = await invokeAsync(aips, ["creative", "preflight", "--project", root, "--bundle", request.bundle], root, 20_000, toolContext.signal)
            let check: Record<string, any> = { status: "BLOCKED", reason_code: "creative_preflight_failed" }
            try { check = JSON.parse(preflight.stdout) } catch { /* fail closed */ }
            if (preflight.status !== 0 || check.status !== "READY") return { content: JSON.stringify(check) }
          }
          const executable = request.action === "execute"
          const maximum = executable ? 3_600_000 : 20_000
          const command = request.action === "prepare"
            ? ["creative", "prepare", "--project", root, "--scope", request.scope!, "--character-id", request.character_id!, "--character-name", request.character_name!, "--summary", request.summary!, "--style-intent", request.style_intent!, "--prompt", request.prompt!, ...request.identity_features!.flatMap((item) => ["--identity-feature", item])]
            : request.action === "discover" ? ["creative", "discover", "--project", root]
            : ["creative", request.action, "--project", root, "--bundle", request.bundle!]
          const started = performance.now()
          const result = await invokeAsync(aips, command, root, maximum, toolContext.signal, request.action === "configure" ? JSON.stringify(request.settings) : undefined)
          let payload: Record<string, any>
          try { payload = JSON.parse(result.stdout) } catch { payload = { status: "BLOCKED", reason_code: "creative_response_invalid" } }
          if (result.status !== 0 && payload.status !== "BLOCKED") payload = { status: "BLOCKED", reason_code: result.error?.includes("timed out") ? "creative_timeout" : "creative_execution_failed" }
          if (payload.status === "BLOCKED") payload.fallback_allowed = false
          await trace({ event: "creative_execution", decision: payload.status === "BLOCKED" ? "BLOCKED" : "ALLOW", project: hash(root), reason_code: "creative_tool_result", duration_ms: Math.min(600000, Math.round(performance.now() - started)), provider: payload.provider ?? "unknown", operation: payload.operation ?? "unknown" })
          return { content: JSON.stringify(payload) }
        },
      })
    })
    await trace({ event: "plugin", status: "ready" })
  },
}
