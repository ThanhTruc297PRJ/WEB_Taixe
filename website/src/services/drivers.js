import { apiDelete, apiGet, apiPost, apiPut } from './api'

export const listDrivers = () => apiGet('/drivers/')
export const createDriver = (data) => apiPost('/drivers/', data)
export const updateDriver = (id, data) => apiPut(`/drivers/${id}`, data)
export const deleteDriver = (id) => apiDelete(`/drivers/${id}`)

// Duyệt tài khoản tài xế
export const approveDriver = (id) => apiPut(`/drivers/${id}/approve`)
export const rejectDriver = (id, reason) => apiPut(`/drivers/${id}/reject`, { reason })
export const lockDriver = (id) => apiPut(`/drivers/${id}/lock`)
export const unlockDriver = (id) => apiPut(`/drivers/${id}/unlock`)

// Đặt lại mật khẩu (hỗ trợ tài xế quên mật khẩu, không vào được email) — trả
// {temp_password} chỉ hiện đúng 1 lần.
export const resetDriverPassword = (id) => apiPost(`/drivers/${id}/reset-password`)
