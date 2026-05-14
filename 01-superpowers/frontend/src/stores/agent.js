import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  fetchAgents as fetchAgentsApi,
  createAgent as createAgentApi,
  changeAgentStatus as changeAgentStatusApi,
  deleteAgent as deleteAgentApi,
} from '../api/agent'

export const useAgentStore = defineStore('agent', () => {
  const agents = ref([])
  const loading = ref(false)
  const pagination = ref({ skip: 0, limit: 20, total: 0 })
  const filterStatus = ref('')

  const statusLabel = { draft: '草稿', active: '已激活', inactive: '已停用' }
  const statusTagType = { draft: 'info', active: 'success', inactive: 'danger' }

  async function fetchAgents() {
    loading.value = true
    try {
      const params = { skip: pagination.value.skip, limit: pagination.value.limit }
      if (filterStatus.value) params.status = filterStatus.value
      const res = await fetchAgentsApi(params)
      const body = res.data
      agents.value = body.items || []
      pagination.value.total = body.total || 0
    } catch {
      agents.value = []
    } finally {
      loading.value = false
    }
  }

  async function createAgent(data) {
    await createAgentApi(data)
    await fetchAgents()
  }

  async function changeStatus(id, status, reason = '') {
    await changeAgentStatusApi(id, status, reason)
    await fetchAgents()
  }

  async function deleteAgent(id) {
    await deleteAgentApi(id)
    await fetchAgents()
  }

  function setFilter(status) {
    filterStatus.value = status
    pagination.value.skip = 0
  }

  function setPage(skip) {
    pagination.value.skip = skip
  }

  return {
    agents,
    loading,
    pagination,
    filterStatus,
    statusLabel,
    statusTagType,
    fetchAgents,
    createAgent,
    changeStatus,
    deleteAgent,
    setFilter,
    setPage,
  }
})
