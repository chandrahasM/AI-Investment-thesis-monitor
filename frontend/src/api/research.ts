import apiClient, { BASE_URL } from './client'
import type { AgentState, Person, ResearchConfig, RunCreate, RunDetail, RunSummary } from '../types/research'

export const researchApi = {
  config: () => apiClient.get<ResearchConfig>('/api/research/config').then(r => r.data),
  list: () => apiClient.get<RunSummary[]>('/api/research/runs').then(r => r.data),
  get: (id: string) => apiClient.get<RunDetail>(`/api/research/runs/${id}`).then(r => r.data),
  create: (data: RunCreate) => apiClient.post<RunSummary>('/api/research/runs', data).then(r => r.data),
  remove: (id: string) => apiClient.delete(`/api/research/runs/${id}`).then(r => r.data),
  findPeople: (id: string) => apiClient.post<Person[]>(`/api/research/runs/${id}/people`).then(r => r.data),
  startAgent: (id: string, effort: string) =>
    apiClient.post<AgentState>(`/api/research/runs/${id}/agent`, { effort }).then(r => r.data),
  pollAgent: (id: string) => apiClient.get<AgentState>(`/api/research/runs/${id}/agent`).then(r => r.data),
  streamUrl: (id: string) => `${BASE_URL}/api/research/runs/${id}/stream`,
}
