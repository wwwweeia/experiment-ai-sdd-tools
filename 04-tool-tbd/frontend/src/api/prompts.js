import api from './index'

export function fetchPrompts(params = {}) {
  return api.get('/api/v1/prompts/', { params })
}

export function fetchPrompt(id) {
  return api.get(`/api/v1/prompts/${id}`)
}

export function createPrompt(data) {
  return api.post('/api/v1/prompts/', data)
}

export function deletePrompt(id) {
  return api.delete(`/api/v1/prompts/${id}`)
}
