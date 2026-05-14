import DefaultTheme from 'vitepress/theme'
import mediumZoom from 'medium-zoom'
import { nextTick, onMounted, watch } from 'vue'
import { useRoute } from 'vitepress'
import './style.css'

export default {
  extends: DefaultTheme,
  setup() {
    const route = useRoute()
    const init = () =>
      mediumZoom('.main img', {
        background: 'var(--vp-c-bg)',
        margin: 24,
      })
    onMounted(init)
    watch(
      () => route.path,
      () => nextTick(init),
    )
  },
}
