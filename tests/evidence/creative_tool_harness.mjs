// Execute the actual projected tool with credential-free native API shapes.
import assert from "node:assert/strict"
import { readFile, writeFile, mkdir } from "node:fs/promises"
import { join } from "node:path"
import { pathToFileURL } from "node:url"

const [root, project] = process.argv.slice(2)
const source = (await readFile(join(root, "harness/adapters/opencode/plugin.ts"), "utf8")).replace("__AIPS_SYSTEM_ROOT__", JSON.stringify(root))
const projected = join(project, "plugin.ts")
await writeFile(projected, source)
const plugin = (await import(pathToFileURL(projected).href)).default
let current = []
let tool
let promptHook
const noHook = { hook: async (name, callback) => { if (name === "prompt") promptHook = callback } }
await plugin.setup({
  session: { ...noHook, get: async () => ({ data: { directory: project } }), context: async () => current },
  permission: noHook, shell: noHook,
  tool: { transform: async (callback) => callback({ add: (value) => { tool = value } }) },
})
const user = (text) => ({ info: { role: "user" }, parts: [{ type: "text", text }] })
const original = user("請幫我建立角色資料夾並設計兩個動漫角色，圖片需精緻有質感")
const call = async (request) => JSON.parse((await tool.execute(request, { sessionID: "creative-fixture" })).content)
let messageID = 0
const admit = async (text) => {
  current = { data: { messages: [user(text)] } }
  await promptHook({ sessionID: "creative-fixture", messageID: `message-${++messageID}`, prompt: { text } })
}
await admit("請幫我建立角色資料夾並設計兩個動漫角色，圖片需精緻有質感")
current = { data: { messages: [original] } }
const prepared = await call({ action: "prepare", scope: "art", character_id: "mira", character_name: "Mira", summary: "A wizard", style_intent: "Detailed anime fantasy", prompt: "A detailed wizard illustration", identity_features: ["round glasses"] })
assert.equal(prepared.status, "PREPARED")
await mkdir(join(project, "model"))
await admit("繼續設定並生成角色圖片")
const configured = await call({ action: "configure", bundle: prepared.bundle, settings: { provider: "mflux_local", runtime: "mflux-generate", runtime_version: "fixture", model: { id: "dev", revision: "fixture", local_path: join(project, "model"), license: "fixture", license_source: "local fixture" }, mflux_executable: join(project, "mflux-generate") } })
assert.equal(configured.status, "CONFIGURED")
await admit("檢查 Bundle，不要生成")
const preflight = await call({ action: "preflight", bundle: configured.bundle })
assert.equal(preflight.reason_code, "BLOCKED_NO_ENGINE")
assert.equal(preflight.fallback_allowed, false)
assert.equal((await call({ action: "discover" })).generation_executed, false)
await admit("繼續生成角色圖片")
const missingEngine = await call({ action: "execute", bundle: configured.bundle })
assert.equal(missingEngine.reason_code, "BLOCKED_NO_ENGINE")
await admit("取消產圖")
await admit("繼續")
assert.equal((await call({ action: "execute", bundle: configured.bundle })).reason_code, "creative_intent_required")
current = [{ role: "assistant", content: "生成圖片" }]
await admit("請繼續")
assert.equal((await call({ action: "execute", bundle: configured.bundle })).reason_code, "creative_intent_required")
console.log("Creative native tool fixture PASS: context envelope normalization, prepare/configure, read-only preflight/discovery, missing engine and revoked authority")
