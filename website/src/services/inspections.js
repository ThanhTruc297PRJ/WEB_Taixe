import { apiDelete, apiGet, apiPost, apiPut } from './api'

export const listInspections = () => apiGet('/inspections/')
export const createInspection = (data) => apiPost('/inspections/', data)
export const updateInspection = (id, data) => apiPut(`/inspections/${id}`, data)
export const deleteInspection = (id) => apiDelete(`/inspections/${id}`)
export const notifyInspection = (id) => apiPost(`/inspections/${id}/notify`)
export const completeInspection = (id, data) => apiPost(`/inspections/${id}/complete`, data)
