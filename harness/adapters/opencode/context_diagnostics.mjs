export const MAX_CONTEXT_BYTES = 12000

const SECTION_ORDER = [
  "task",
  "selected_protocols",
  "intelligence_topics",
  "retrieval",
  "creative_workspace",
  "intelligence",
  "freshness",
  "instruction_resolution",
  "fail_policy",
]

function serializedBytes(value) {
  return Buffer.byteLength(JSON.stringify(value))
}

function largestSections(summary) {
  return SECTION_ORDER
    .filter((section) => summary[section] !== undefined)
    .map((section) => ({ section, bytes: serializedBytes(summary[section]) }))
    .sort((left, right) => right.bytes - left.bytes || left.section.localeCompare(right.section))
    .slice(0, 3)
}

export function compactManifest(manifest, maxBytes = MAX_CONTEXT_BYTES) {
  const full = JSON.stringify(manifest)
  const originalBytes = Buffer.byteLength(full)
  if (originalBytes <= maxBytes) {
    return { body: full, truncated: false, originalBytes, compactBytes: originalBytes, largestSections: [] }
  }

  const task = manifest.task
  const summary = {
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
    aips_context_budget: { truncated: true, original_bytes: originalBytes, max_bytes: maxBytes },
  }
  let body = JSON.stringify(summary)
  if (Buffer.byteLength(body) > maxBytes) {
    summary.intelligence_topics = Array.isArray(summary.intelligence_topics) ? summary.intelligence_topics.slice(0, 8) : summary.intelligence_topics
    summary.fail_policy = summary.fail_policy && { mode: summary.fail_policy.mode, reasons: Array.isArray(summary.fail_policy.reasons) ? summary.fail_policy.reasons.slice(0, 8) : [] }
    body = JSON.stringify(summary)
  }
  const compactBytes = Buffer.byteLength(body)
  return compactBytes <= maxBytes
    ? { body, truncated: true, originalBytes, compactBytes, largestSections: [] }
    : {
      body: "",
      truncated: true,
      originalBytes,
      compactBytes,
      reasonCode: "context_compaction_over_budget",
      largestSections: largestSections(summary),
    }
}

export function formatContextFailure(diagnostic) {
  const sections = diagnostic.largestSections.length
    ? diagnostic.largestSections.map(({ section, bytes }) => `${section}=${bytes}`).join(", ")
    : "no section breakdown available"
  return `AIPS Turn Context unavailable [${diagnostic.reasonCode}]: the compact projection is ${diagnostic.compactBytes} bytes (source ${diagnostic.originalBytes} bytes), above the ${MAX_CONTEXT_BYTES}-byte limit. Largest sections by serialized size: ${sections}. Review \`aips intelligence context --runtime opencode --project "$PWD" --prompt "<task>" --full --explain --format json\` and \`aips intelligence refresh-plan --project "$PWD"\`; refresh only affected topics, then retry. Project writes remain denied until Context fits.`
}
