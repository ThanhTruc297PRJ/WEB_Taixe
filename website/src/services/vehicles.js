import { apiDelete, apiGet, apiPost, apiPut } from './api'

export const listVehicles = () => apiGet('/vehicles/')
export const createVehicle = (data) => apiPost('/vehicles/', data)
export const updateVehicle = (id, data) => apiPut(`/vehicles/${id}`, data)
export const deleteVehicle = (id) => apiDelete(`/vehicles/${id}`)
