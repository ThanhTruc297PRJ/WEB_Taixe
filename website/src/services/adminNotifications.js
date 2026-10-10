import { apiGet } from './api'

// limit: số mục mỗi nhóm (chuông lấy 5, trang Thông báo lấy toàn bộ).
export const getAdminNotifications = (limit) =>
  apiGet(`/admin/notifications/${limit ? `?limit=${limit}` : ''}`)
