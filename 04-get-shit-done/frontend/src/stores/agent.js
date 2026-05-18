import { defineStore } from 'pinia'
import { ref } from 'vue'
import { fetchAgents, createAgent as createAgentApi, updateAgentStatus, deleteAgent as deleteAgentApi } from '../api/agents'

export const useAgentStore = defineStore('agent', () => {
  const agents = ref([])
  const loading = ref(false)
  const statusFilter = ref(null)
  const currentPage = ref(1)
  const pageSize = ref(10)

  async function loadAgents() {
    loading.value = true
    try {
      const res = await fetchAgents({
        skip: (currentPage.value - 1) * pageSize.value,
        limit: pageSize.value,
        status: statusFilter.value || undefined,
      })
      agents.value = res.data || []
    } catch (e) {
      console.error('[AgentStore] 加载失败:', e)
      agents.value = []
    } finally {
      loading.value = false
    }
  }

  function setStatusFilter(status) {
    statusFilter.value = status
    currentPage.value = 1
    loadAgents()
  }

  function setCurrentPage(page) {
    currentPage.value = page
    loadAgents()
  }

  async function createAgent(data) {
    try {
      await createAgentApi(data)
      loadAgents()
    } catch (e) {
      console.error('[AgentStore] 创建失败:', e)
    }
  }

  async function updateStatus(id, targetStatus) {
    try {
      await updateAgentStatus(id, { status: targetStatus })
      loadAgents()
    } catch (e) {
      console.error('[AgentStore] 状态更新失败:', e)
    }
  }

  async function deleteAgent(id) {
    try {
      await deleteAgentApi(id)
      loadAgents()
    } catch (e) {
      console.error('[AgentStore] 删除失败:', e)
    }
  }

  return {
    agents,
    loading,
    statusFilter,
    currentPage,
    pageSize,
    loadAgents,
    setStatusFilter,
    setCurrentPage,
    createAgent,
    updateStatus,
    deleteAgent,
  }
})
