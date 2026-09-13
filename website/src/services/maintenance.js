import { apiDelete, apiGet, apiPost, apiPut } from './api'

export const listMaintenance = () => apiGet('/maintenance/')
export const createMaintenance = (data) => apiPost('/maintenance/', data)
export const updateMaintenance = (id, data) => apiPut(`/maintenance/${id}`, data)
export const deleteMaintenance = (id) => apiDelete(`/maintenance/${id}`)
export const notifyMaintenance = (id) => apiPost(`/maintenance/${id}/notify`)
export const scanReminders = () => apiPost('/maintenance/scan-reminders')
