import api from './index'

export function fetchAgents(params = {}) {
  return api.get('/api/v1/agents/', { params })
}

export function createAgent(data) {
  return api.post('/api/v1/agents/', data)
}

export function updateAgentStatus(id, data) {
  return api.patch(`/api/v1/agents/${id}/status`, data)
}

export function deleteAgent(id) {
  return api.delete(`/api/v1/agents/${id}`)
}
