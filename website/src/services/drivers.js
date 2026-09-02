import { apiDelete, apiGet, apiPost, apiPut } from './api'

export const listDrivers = () => apiGet('/drivers/')
export const createDriver = (data) => apiPost('/drivers/', data)
export const updateDriver = (id, data) => apiPut(`/drivers/${id}`, data)
export const deleteDriver = (id) => apiDelete(`/drivers/${id}`)
