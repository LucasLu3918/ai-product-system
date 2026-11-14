import DefaultTheme from 'vitepress/theme'
import SkillExplorer from './components/SkillExplorer.vue'
import './custom.css'

export default {
  ...DefaultTheme,
  enhanceApp({ app }) {
    app.component('SkillExplorer', SkillExplorer)
  }
}
