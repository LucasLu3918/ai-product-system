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
const comfySchema = tool.input.properties.settings.properties.comfyui
assert.equal(comfySchema.additionalProperties, false)
assert.deepEqual(comfySchema.properties.model_profile.enum, ["z-image-turbo"])
assert(tool.input.properties.action.enum.includes("review-assist"), "OpenCode schema omitted bounded local visual review")
for (const field of ["unet_name", "clip_name", "vae_name"]) {
  assert.equal(comfySchema.properties[field].type, "string", `OpenCode schema omitted ${field}`)
}
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
assert.equal(prepared.status, "PREPARED", `explicit prepare request was blocked: ${JSON.stringify(prepared)}`)
await admit("A佈局＋B質感，獨立立繪")
const continued = await call({ action: "prepare", scope: "art", character_id: "mira-continuation", character_name: "Mira", summary: "A wizard", style_intent: "Detailed anime fantasy", prompt: "A detailed wizard illustration", identity_features: ["round glasses"] })
assert.equal(continued.status, "PREPARED", `bounded selection response did not receive a fresh scoped grant: ${JSON.stringify(continued)}`)
await admit("生成一張森林插畫")
const scopeExpansion = await call({ action: "prepare", scope: "art", character_id: "forest", character_name: "Forest", summary: "A forest", style_intent: "Landscape", prompt: "A forest illustration", identity_features: ["pine trees"] })
assert.equal(scopeExpansion.reason_code, "creative_scope_expansion", `new creative subject inherited the prior task: ${JSON.stringify(scopeExpansion)}`)
await mkdir(join(project, "model"))
await admit("請幫我設定並生成角色立繪")
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
assert.equal(missingEngine.fallback_allowed, false)
assert.equal(typeof missingEngine.details.providers, "object", "provider-specific recovery reasons were hidden")
assert.match(missingEngine.next_action, /per-provider command, runtime, and model status/)
assert.equal(JSON.stringify(missingEngine).includes(project), false, "provider recovery leaked a local path")
const reviewWithoutGrant = await call({ action: "review-assist", manifest: "missing/creative-execution-manifest.json", vision_model: "vision-local" })
assert.equal(reviewWithoutGrant.reason_code, "creative_intent_required", "generation permission must not imply visual review permission")
await admit("請檢查角色圖片品質")
const reviewWithGrant = await call({ action: "review-assist", manifest: "missing/creative-execution-manifest.json", vision_model: "vision-local" })
assert.notEqual(reviewWithGrant.reason_code, "creative_admission_grant_missing", "explicit review intent did not authorize the bounded review action")
await admit("取消產圖")
await admit("繼續")
assert.equal((await call({ action: "execute", bundle: configured.bundle })).reason_code, "creative_intent_required")
current = [{ role: "assistant", content: "生成圖片" }]
await admit("請繼續")
assert.equal((await call({ action: "execute", bundle: configured.bundle })).reason_code, "creative_intent_required")
console.log("Creative native tool fixture PASS: context envelope normalization, Z-Image schema, prepare/configure, read-only preflight/discovery, provider recovery and revoked authority")
