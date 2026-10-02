import { apiDelete, apiGet, apiPost, apiPut } from './api'

export const listStations = () => apiGet('/radio/stations/all')

export const createStation = (data) => apiPost('/radio/stations', data)

export const updateStation = (id, data) => apiPut(`/radio/stations/${id}`, data)

export const toggleStation = (id, enabled) =>
  apiPut(`/radio/stations/${id}/toggle`, { enabled })

export const deleteStation = (id) => apiDelete(`/radio/stations/${id}`)
