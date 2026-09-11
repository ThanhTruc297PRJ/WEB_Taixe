import { apiDelete, apiGet, apiPost, apiPut } from './api'

export const listKbDocuments = () => apiGet('/kb/documents')
export const createKbDocument = (data) => apiPost('/kb/documents', data)
export const updateKbDocument = (id, data) => apiPut(`/kb/documents/${id}`, data)
export const deleteKbDocument = (id) => apiDelete(`/kb/documents/${id}`)
