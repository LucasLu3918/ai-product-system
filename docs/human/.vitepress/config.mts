import { defineConfig } from 'vitepress'

export default defineConfig({
  lang: 'zh-Hant',
  title: 'AI Product System',
  description: '跨 Agent Software Engineering Harness',
  base: '/ai-product-system/',
  cleanUrls: true,
  lastUpdated: true,
  themeConfig: {
    nav: [
      { text: '開始使用', link: '/GETTING_STARTED' },
      { text: '使用指南', link: '/USER_GUIDE' },
      { text: '架構', link: '/ARCHITECTURE_OVERVIEW' },
      { text: 'Technology', link: '/TECHNOLOGY_GUIDE' }
    ],
    sidebar: [
      { text: '開始使用', items: [
        { text: '總覽', link: '/' }, { text: '快速上手', link: '/GETTING_STARTED' }, { text: '安裝 / 更新 / 解除', link: '/INSTALLATION' }
      ]},
      { text: '使用 AIPS', items: [
        { text: '使用指南', link: '/USER_GUIDE' }, { text: 'Global Harness / MCP', link: '/HARNESS' }, { text: 'Project Intelligence', link: '/PROJECT_INTELLIGENCE' }, { text: 'Security Assurance', link: '/SECURITY_ASSURANCE' }
      ]},
      { text: '架構與技術', items: [
        { text: '系統架構', link: '/ARCHITECTURE_OVERVIEW' }, { text: 'Technology Guide', link: '/TECHNOLOGY_GUIDE' }, { text: 'Evolution Radar', link: '/EVOLUTION_RADAR' }, { text: 'Evolution 流程圖解', link: '/EVOLUTION_RADAR_OVERVIEW' }
      ]},
      { text: 'Reference / Maintainers', items: [
        { text: 'Scenario Conformance', link: '/CONFORMANCE' }, { text: 'System Maintenance', link: '/MAINTENANCE' }, { text: 'Documentation Consistency', link: '/DOCUMENTATION_SYNC' }, { text: '文件導覽', link: '/DOCUMENTATION_MAP' }
      ]}
    ],
    search: { provider: 'local' },
    outline: { level: [2, 3], label: '本頁內容' },
    socialLinks: [{ icon: 'github', link: 'https://github.com/LucasLu3918/ai-product-system' }],
    footer: { message: 'Rendered from canonical docs/human Markdown sources.', copyright: 'AI Product System' }
  }
})
