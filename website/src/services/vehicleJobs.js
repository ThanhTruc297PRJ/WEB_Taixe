import { apiPost } from './api'

// kind: 'maintenance' | 'inspection'
export const confirmJob = (kind, id) => apiPost(`/vehicle-jobs/${kind}/${id}/confirm`)

export const rejectJob = (kind, id, reason) =>
  apiPost(`/vehicle-jobs/${kind}/${id}/reject`, { reason })
