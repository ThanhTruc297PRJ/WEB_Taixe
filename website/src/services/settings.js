import { apiDelete, apiGet, apiPost, apiPut } from './api'

export const getSettings = () => apiGet('/settings/')
export const updateSettings = (data) => apiPut('/settings/', data)

export const listAdmins = () => apiGet('/settings/admins')
export const grantAdmin = (email) => apiPost('/settings/admins', { email })
export const revokeAdmin = (uid) => apiDelete(`/settings/admins/${uid}`)
