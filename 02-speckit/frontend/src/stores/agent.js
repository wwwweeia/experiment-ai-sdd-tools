import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { fetchAgents as fetchAgentsApi, createAgent as createAgentApi, changeAgentStatus as changeStatusApi, deleteAgent as deleteAgentApi } from '../api/agents'
import { ElMessage } from 'element-plus'

export const useAgentStore = defineStore('agent', () => {
  const agents = ref([])
  const loading = ref(false)
  const statusFilter = ref('')
  const pagination = ref({ skip: 0, limit: 20, total: 0 })

  const filteredAgents = computed(() => {
    if (!statusFilter.value) return agents.value
    return agents.value.filter(a => a.status === statusFilter.value)
  })

  async function fetchAgents(status) {
    loading.value = true
    try {
      const params = { skip: pagination.value.skip, limit: pagination.value.limit }
      if (status) params.status = status
      const res = await fetchAgentsApi(params)
      agents.value = res.data || []
      pagination.value.total = agents.value.length
    } catch (e) {
      console.error('[AgentStore] 加载失败:', e)
      agents.value = []
    } finally {
      loading.value = false
    }
  }

  async function createAgent(data) {
    const res = await createAgentApi(data)
    ElMessage.success('Agent 创建成功')
    await fetchAgents(statusFilter.value)
    return res.data
  }

  async function changeStatus(id, status, reason) {
    try {
      await changeStatusApi(id, { status, reason })
      ElMessage.success(status === 'active' ? 'Agent 已激活' : 'Agent 已停用')
      await fetchAgents(statusFilter.value)
    } catch (e) {
      const msg = e.response?.data?.detail || e.message || '操作失败'
      ElMessage.error(msg)
      throw e
    }
  }

  async function deleteAgentById(id) {
    try {
      await deleteAgentApi(id)
      ElMessage.success('Agent 已删除')
      await fetchAgents(statusFilter.value)
    } catch (e) {
      const msg = e.response?.data?.detail || e.message || '删除失败'
      ElMessage.error(msg)
      throw e
    }
  }

  return {
    agents, loading, statusFilter, pagination, filteredAgents,
    fetchAgents, createAgent, changeStatus, deleteAgentById,
  }
})
