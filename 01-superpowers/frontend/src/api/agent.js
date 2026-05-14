import api from './index'

export function fetchAgents(params = {}) {
  return api.get('/api/v1/agents/', { params })
}

export function fetchAgent(id) {
  return api.get(`/api/v1/agents/${id}`)
}

export function createAgent(data) {
  return api.post('/api/v1/agents/', data)
}

export function changeAgentStatus(id, status, reason = '') {
  return api.patch(`/api/v1/agents/${id}/status`, { status, reason })
}

export function deleteAgent(id) {
  return api.delete(`/api/v1/agents/${id}`)
}
