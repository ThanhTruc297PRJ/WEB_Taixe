import { apiGet } from './api'

export const getAdminNotifications = () => apiGet('/admin/notifications/')
