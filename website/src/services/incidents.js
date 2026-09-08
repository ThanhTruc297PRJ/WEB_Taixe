import { apiDelete, apiGet } from './api'

export const listIncidents = (driverId) =>
  apiGet(driverId ? `/incidents/?driver_id=${encodeURIComponent(driverId)}` : '/incidents/')

export const deleteIncident = (id) => apiDelete(`/incidents/${id}`)
