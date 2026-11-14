<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { withBase } from 'vitepress'

type Skill = {
  id: string
  title_en: string
  title_zh: string
  description_en: string
  description_zh: string
  category: string
  source: 'aips' | 'upstream'
  source_path: string
  upstream_path?: string
  upstream_commit?: string | null
  status: string
  installable: boolean
  disposition: string
  reason: string
  targets: string[]
  example: string
}

const skills = ref<Skill[]>([])
const loading = ref(true)
const loadError = ref('')
const query = ref('')
const category = ref('')
const source = ref('')
const status = ref('')
const installable = ref('')
const copiedId = ref('')
const copyError = ref('')

const categoryNames: Record<string, string> = {
  engineering: '工程', productivity: '生產力', 'in-progress': '開發中', misc: '其他',
  database: '資料庫', 'delivery-planning': '交付規劃', infrastructure: '基礎設施',
  operations: '維運', performance: '效能', product: '產品', quality: '品質',
  security: '安全', design: '設計', testing: '測試',
  planning: '規劃',
  documentation: '文件', 'code-quality': '程式品質'
}
const statusNames: Record<string, string> = {
  enabled: 'AIPS 可用', 'auto-routed': '自動路由', experimental: '實驗／選用',
  integrated: '已整合', adopted: '已採納', optional: '選用', workflow: '流程整合',
  deferred: '延後評估', excluded: '排除', reference: '來源參考', 'not-adopted': '不導入'
}

const categories = computed(() => [...new Set(skills.value.map((skill) => skill.category))].sort())
const filtered = computed(() => {
  const terms = query.value.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean)
  return skills.value.filter((skill) => {
    const haystack = [skill.id, skill.title_en, skill.title_zh, skill.description_en,
      skill.description_zh, skill.category, skill.source, skill.disposition,
      skill.reason, skill.targets.join(' '), skill.example].join(' ').toLocaleLowerCase()
    return terms.every((term) => haystack.includes(term))
      && (!category.value || skill.category === category.value)
      && (!source.value || skill.source === source.value)
      && (!status.value || skill.status === status.value)
      && (!installable.value || String(skill.installable) === installable.value)
  })
})

async function loadCatalog() {
  loading.value = true
  loadError.value = ''
  try {
    const response = await fetch(withBase('/skill-catalog.json'))
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    const data = await response.json()
    if (!Array.isArray(data.skills)) throw new Error('目錄資料格式不正確')
    skills.value = data.skills
  } catch (error) {
    loadError.value = `無法載入 Skill 目錄（${error instanceof Error ? error.message : '未知錯誤'}）。`
  } finally {
    loading.value = false
  }
}

async function copyExample(skill: Skill) {
  copyError.value = ''
  try {
    await navigator.clipboard.writeText(skill.example)
    copiedId.value = skill.id
    window.setTimeout(() => { copiedId.value = '' }, 1500)
  } catch {
    copyError.value = '瀏覽器未允許剪貼簿存取，請從下方文字手動複製。'
  }
}

onMounted(loadCatalog)
</script>

<template>
  <section class="skill-explorer" aria-label="Skill 探索器">
    <p class="explorer-intro">依名稱、用途、ID 或來源搜尋。處置狀態與安裝資格分開篩選。</p>
    <div class="explorer-controls">
      <label class="explorer-search">搜尋
        <input v-model="query" type="search" placeholder="例如：測試、debug、writing-shape" autocomplete="off">
      </label>
      <label>分類
        <select v-model="category"><option value="">全部分類</option><option v-for="item in categories" :key="item" :value="item">{{ categoryNames[item] || item }}</option></select>
      </label>
      <label>來源
        <select v-model="source"><option value="">全部來源</option><option value="aips">AIPS canonical</option><option value="upstream">上游參考</option></select>
      </label>
      <label>狀態
        <select v-model="status"><option value="">全部狀態</option><option v-for="(label, key) in statusNames" :key="key" :value="key">{{ label }}</option></select>
      </label>
      <label>安裝資格
        <select v-model="installable"><option value="">全部</option><option value="true">可安裝上游</option><option value="false">AIPS canonical／不可安裝</option></select>
      </label>
      <button class="explorer-clear" type="button" @click="query = ''; category = ''; source = ''; status = ''; installable = ''">清除篩選</button>
    </div>
    <p class="explorer-count" aria-live="polite">{{ loading ? '載入技能目錄…' : `顯示 ${filtered.length} / ${skills.length} 項` }}</p>
    <div v-if="loading" class="explorer-state" role="status">正在載入目錄…</div>
    <div v-else-if="loadError" class="explorer-state explorer-error" role="alert">
      <p>{{ loadError }}</p><button type="button" @click="loadCatalog">重新載入</button>
      <p><a :href="withBase('/skill-catalog.html')">開啟靜態目錄備援</a></p>
    </div>
    <p v-else-if="filtered.length === 0" class="explorer-state" role="status">找不到符合條件的 Skill，請調整搜尋或清除篩選。</p>
    <div v-else class="skill-grid">
      <article v-for="skill in filtered" :key="`${skill.source}:${skill.id}`" class="skill-card">
        <div class="skill-badges">
          <span class="skill-badge">{{ categoryNames[skill.category] || skill.category }}</span>
          <span class="skill-badge" :class="`status-${skill.status}`">{{ statusNames[skill.status] || skill.status }}</span>
          <span v-if="skill.source === 'upstream'" class="skill-badge">上游原文</span>
        </div>
        <h2>{{ skill.title_zh || skill.title_en }} <small v-if="skill.title_zh">{{ skill.title_en }}</small></h2>
        <code>{{ skill.id }}</code>
        <p>{{ skill.description_zh || skill.description_en }}<small v-if="skill.source === 'upstream'" class="translation-note">（上游英文原文）</small></p>
        <dl>
          <template v-if="skill.source === 'upstream'"><dt>AIPS 處置</dt><dd>{{ skill.reason || skill.disposition }}</dd><dt>安裝資格</dt><dd>{{ skill.installable ? '使用者可選擇安裝' : '使用 AIPS canonical' }}</dd></template>
          <dt>來源</dt><dd>{{ skill.source === 'aips' ? 'AIPS canonical' : `上游 · ${skill.upstream_commit}` }}</dd>
          <dt>本機路徑</dt><dd><code>{{ skill.source_path }}</code></dd>
        </dl>
        <details><summary>使用範例</summary><pre>{{ skill.example }}</pre><button type="button" @click="copyExample(skill)">{{ copiedId === skill.id ? '已複製' : '複製範例' }}</button><p v-if="copyError" class="copy-error">{{ copyError }}</p></details>
      </article>
    </div>
  </section>
</template>
