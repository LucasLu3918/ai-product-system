import { Plugin } from "@opencode/plugin"
import { createHash } from "node:crypto"
import { spawnSync } from "node:child_process"
import { statSync } from "node:fs"
import { join, resolve } from "node:path"

const SYSTEM_ROOT = __AIPS_SYSTEM_ROOT__
const CACHE_MS = 30000
const MAX_CACHE = 32

type ContextEntry = { key: string; at: number; manifest: Record<string, any> | null; reason?: string }

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

function fileStamp(path: string): string {
  try {
    const value = statSync(path)
    return `${value.mtimeMs}:${value.size}`
  } catch {
    return "missing"
  }
}

function projectFingerprint(root: string, targetPath: string): string {
  const status = spawnSync("git", ["-C", root, "status", "--porcelain=v1", "--untracked-files=all"], { encoding: "utf8", timeout: 3000, maxBuffer: 1024 * 1024 })
  const diff = spawnSync("git", ["-C", root, "diff", "--binary", "HEAD", "--"], { encoding: "utf8", timeout: 5000, maxBuffer: 4 * 1024 * 1024 })
  const gitState = status.status === 0 ? `${status.stdout}\n${diff.stdout}` : "not-a-git-project"
  const instructions = ["AGENTS.md", "CLAUDE.md", "SYSTEM.md"].map((name) => `${name}:${fileStamp(join(root, name))}`).join("|")
  return `${createHash("sha256").update(gitState).digest("hex")}|${instructions}|target:${fileStamp(targetPath)}`
}

function invoke(binary: string, args: string[], cwd: string, timeout: number): { status: number | null; stdout: string; error?: string } {
  const result = spawnSync(binary, args, { cwd, encoding: "utf8", timeout, maxBuffer: 2 * 1024 * 1024, shell: false })
  if (result.error) return { status: result.status, stdout: "", error: result.error.message }
  return { status: result.status, stdout: result.stdout ?? "", error: result.stderr?.slice(0, 600) }
}

export default Plugin.define({
  id: "aips-opencode",
  async setup(ctx) {
    const root = resolve(ctx.location.project.directory)
    const aips = process.env.AIPS_CLI || join(SYSTEM_ROOT, "bin/aips")
    const python = process.env.AIPS_GUARD_PYTHON || "python3"
    const guard = join(SYSTEM_ROOT, "scripts/opencode_native_guard.py")
    const cache = new Map<string, ContextEntry>()

    async function contextFor(sessionID: string, messages: any[], targetPath = root): Promise<ContextEntry> {
      const prompt = lastUserText(messages)
      const promptHash = createHash("sha256").update(prompt).digest("hex")
      const key = `${root}|${sessionID}|${promptHash}|${targetPath}|${projectFingerprint(root, targetPath)}`
      const current = cache.get(sessionID)
      if (current && current.key === key && Date.now() - current.at < CACHE_MS) return current
      const result = invoke(aips, ["intelligence", "context", "--runtime", "opencode", "--project", root,
        "--prompt", prompt, "--target-path", targetPath, "--format", "json", "--compact"], root, 15000)
      let manifest: Record<string, any> | null = null
      let reason = result.error || "AIPS context command failed"
      if (result.status === 0) {
        try {
          manifest = JSON.parse(result.stdout)
          reason = ""
        } catch {
          reason = "AIPS context returned invalid JSON"
        }
      }
      const entry = { key, at: Date.now(), manifest, reason }
      cache.set(sessionID, entry)
      while (cache.size > MAX_CACHE) cache.delete(cache.keys().next().value as string)
      return entry
    }

    function guardDecision(kind: "write" | "shell", input: Record<string, any>): Record<string, any> {
      const args = kind === "write"
        ? [guard, "write", "--tool", String(input.action), "--resources", JSON.stringify(input.resources ?? []), "--root", root, "--manifest", JSON.stringify(input.manifest ?? {})]
        : [guard, "shell", "--command", String(input.command ?? ""), "--cwd", String(input.cwd ?? root), "--root", root]
      const result = invoke(python, args, root, 5000)
      if (result.stdout) {
        try { return JSON.parse(result.stdout) } catch { /* fail closed below */ }
      }
      return { decision: "DENY", level: "L2", reason: result.error || "AIPS native guard unavailable" }
    }

    await ctx.session.hook("context", async (event) => {
      const entry = await contextFor(event.sessionID, event.messages as any[])
      const text = entry.manifest
        ? `AIPS Turn Context (automatically loaded; transient):\n${JSON.stringify(entry.manifest)}`
        : `AIPS Turn Context unavailable: ${entry.reason}. Do not perform project writes until the required AIPS context is restored. Shell and MCP/custom-tool effects are not covered by the native file guard.`
      event.system.push({ type: "text", text })
    })

    await ctx.permission.hook("evaluate", async (event) => {
      if (!["edit", "write", "patch", "apply_patch"].includes(event.action)) return
      let entry: ContextEntry | undefined = cache.get(event.sessionID)
      if (!entry || !entry.manifest || Date.now() - entry.at >= CACHE_MS) {
        const messages = await ctx.session.context({ sessionID: event.sessionID })
        entry = await contextFor(event.sessionID, messages as any[], event.resources[0] ?? root)
      }
      const decision = guardDecision("write", { action: event.action, resources: [...event.resources], manifest: entry.manifest ?? {} })
      if (decision.decision !== "ALLOW") {
        event.effect = "deny"
        event.message = `AIPS ${decision.level ?? "L2"} native write guard: ${decision.reason ?? "context unavailable"}`
      }
    })

    await ctx.shell.hook("create.before", (event) => {
      const decision = guardDecision("shell", { command: event.command, cwd: event.cwd })
      if (decision.decision !== "ALLOW") {
        console.error(`AIPS native Shell guard: ${decision.reason ?? "unsupported command"}`)
        event.command = "false"
      }
    })
  },
})
