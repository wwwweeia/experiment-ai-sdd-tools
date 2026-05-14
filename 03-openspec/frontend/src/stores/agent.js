import { defineStore } from 'pinia'
import { ref } from 'vue'
import { fetchAgents, createAgent as apiCreate, changeAgentStatus as apiChangeStatus, deleteAgent as apiDelete } from '../api/agents'

export const useAgentStore = defineStore('agent', () => {
  const agents = ref([])
  const loading = ref(false)
  const currentFilter = ref('')

  async function loadAgents(status = '') {
    loading.value = true
    currentFilter.value = status
    try {
      const res = await fetchAgents({ status: status || undefined })
      agents.value = res.data || []
    } finally {
      loading.value = false
    }
  }

  async function createAgent(data) {
    const res = await apiCreate(data)
    await loadAgents(currentFilter.value)
    return res.data
  }

  async function changeStatus(id, status, reason) {
    const res = await apiChangeStatus(id, { status, reason })
    await loadAgents(currentFilter.value)
    return res.data
  }

  async function removeAgent(id) {
    await apiDelete(id)
    await loadAgents(currentFilter.value)
  }

  return { agents, loading, currentFilter, loadAgents, createAgent, changeStatus, removeAgent }
})
