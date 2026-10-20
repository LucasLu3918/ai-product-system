import { defineConfig } from 'vitepress'

export default defineConfig({
  lang: 'zh-Hant',
  title: 'AI Product System',
  description: '以可追溯專案脈絡、風險導向驗證與人類授權協助 Agent 協作的軟體工程系統。',
  base: '/ai-product-system/',
  cleanUrls: true,
  lastUpdated: true,
  vite: {
    server: { host: '127.0.0.1', cors: false, allowedHosts: [] }
  },
  themeConfig: {
    nav: [
      { text: '開始使用', link: '/GETTING_STARTED' },
      { text: '使用指南', link: '/USER_GUIDE' },
      { text: '系統架構', link: '/ARCHITECTURE_OVERVIEW' },
      { text: '更多', items: [
        { text: 'Skill 探索器', link: '/skill-catalog.html' },
        { text: '專案脈絡', link: '/PROJECT_INTELLIGENCE' },
        { text: '系統參考', link: '/SYSTEM_REFERENCE' },
        { text: '技術指南', link: '/TECHNOLOGY_GUIDE' }
      ] }
    ],
    sidebar: [
      { text: '開始使用', items: [
        { text: '總覽', link: '/' }, { text: '快速上手', link: '/GETTING_STARTED' }, { text: '安裝／更新／解除', link: '/INSTALLATION' }
      ]},
      { text: '使用 AIPS', items: [
        { text: '使用指南', link: '/USER_GUIDE' }, { text: 'Skill 探索器', link: '/skill-catalog.html' }, { text: 'Agent 整合與 MCP', link: '/HARNESS' }, { text: '專案脈絡', link: '/PROJECT_INTELLIGENCE' }, { text: '安全保證', link: '/SECURITY_ASSURANCE' }
      ]},
      { text: '架構與技術', items: [
        { text: '系統架構', link: '/ARCHITECTURE_OVERVIEW' }, { text: '系統參考', link: '/SYSTEM_REFERENCE' }, { text: '技術指南', link: '/TECHNOLOGY_GUIDE' }, { text: '演進雷達', link: '/EVOLUTION_RADAR' }, { text: '演進流程圖', link: '/EVOLUTION_RADAR_OVERVIEW' }
      ]},
      { text: '驗證與維護', items: [
        { text: '情境驗證紀錄', link: '/CONFORMANCE' }, { text: '系統維護', link: '/MAINTENANCE' }, { text: '文件一致性', link: '/DOCUMENTATION_SYNC' }, { text: '文件導覽', link: '/DOCUMENTATION_MAP' }
      ]}
    ],
    search: {
      provider: 'local',
      options: {
        translations: {
          button: { buttonText: '搜尋文件', buttonAriaLabel: '搜尋文件' },
          modal: {
            displayDetails: '顯示詳細內容',
            resetButtonTitle: '清除搜尋',
            backButtonTitle: '返回',
            noResultsText: '找不到相符的文件',
            footer: {
              selectText: '選取', selectKeyAriaLabel: '按 Enter 選取',
              navigateText: '切換', navigateUpKeyAriaLabel: '向上移動',
              navigateDownKeyAriaLabel: '向下移動', closeText: '關閉',
              closeKeyAriaLabel: '按 Escape 關閉'
            }
          }
        }
      }
    },
    outline: { level: [2, 3], label: '本頁內容' },
    socialLinks: [{ icon: 'github', link: 'https://github.com/LucasLu3918/ai-product-system' }],
    footer: { message: '以 docs/human 中的 Markdown 文件為網站來源。', copyright: 'AI Product System' }
  }
})
