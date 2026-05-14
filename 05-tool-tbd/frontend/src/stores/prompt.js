import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { fetchPrompts as fetchPromptsApi } from '../api/prompts'

/**
 * 解析 tags 字段：JSON 字符串 / null / 数组 -> 统一为数组
 * 后端 tags 可能为 JSON 字符串、原生数组或 null
 */
function parseTags(raw) {
  if (raw == null) return []
  if (Array.isArray(raw)) return raw
  try {
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

export const usePromptStore = defineStore('prompt', () => {
  // ==================== State ====================
  const prompts = ref([])
  const loading = ref(false)
  const searchForm = ref({
    keyword: '',
    tags: [],
  })

  // ==================== Getters ====================

  /** 规范化数据：将 tags 字段统一解析为数组，映射后端字段名 */
  const normalizedPrompts = computed(() =>
    prompts.value.map((item) => ({
      ...item,
      tags: parseTags(item.tags),
      createdTime: item.created_at || item.createdTime,
    }))
  )

  /** 所有可用标签（去重排序） */
  const allTags = computed(() => {
    const tagSet = new Set()
    normalizedPrompts.value.forEach((item) => {
      item.tags.forEach((tag) => tagSet.add(tag))
    })
    return Array.from(tagSet).sort()
  })

  /** 按搜索条件筛选后的列表 */
  const filteredPrompts = computed(() => {
    const keyword = searchForm.value.keyword.trim().toLowerCase()
    const selectedTags = searchForm.value.tags

    return normalizedPrompts.value.filter((item) => {
      if (keyword && !item.title.toLowerCase().includes(keyword)) {
        return false
      }
      if (selectedTags.length > 0) {
        const itemTagSet = new Set(item.tags)
        if (!selectedTags.every((tag) => itemTagSet.has(tag))) {
          return false
        }
      }
      return true
    })
  })

  // ==================== Actions ====================

  async function fetchPrompts() {
    loading.value = true
    try {
      const res = await fetchPromptsApi()
      prompts.value = res.data || []
    } catch (e) {
      console.error('[PromptStore] 加载失败:', e)
      prompts.value = []
    } finally {
      loading.value = false
    }
  }

  /** 更新搜索条件（getter 自动触发筛选） */
  function search(keyword, tags) {
    searchForm.value.keyword = keyword
    searchForm.value.tags = tags
  }

  /** 重置搜索条件 */
  function resetSearch() {
    searchForm.value.keyword = ''
    searchForm.value.tags = []
  }

  return {
    prompts,
    loading,
    searchForm,
    normalizedPrompts,
    allTags,
    filteredPrompts,
    fetchPrompts,
    search,
    resetSearch,
  }
})
