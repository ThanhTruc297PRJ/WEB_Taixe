import { apiGet, apiPut } from './api'

export const listDriverReports = () => apiGet('/driver-reports/')
export const resolveDriverReport = (id) => apiPut(`/driver-reports/${id}/resolve`)
