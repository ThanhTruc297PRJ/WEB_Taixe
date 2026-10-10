import { toDate } from './firestore'

// Ngày tính chi phí vào tháng nào — dùng chung cho biểu đồ chi phí ở Tổng quan
// và trang Báo cáo chi phí (bấm cột tháng -> báo cáo đúng tháng đó).
// Ưu tiên ngày quản lý xác nhận hoàn tất; lịch cũ chưa có thì lấy ngày hẹn.

export const maintenanceCostDate = (m) => toDate(m.confirmed_at) || toDate(m.scheduled_date)

export const inspectionCostDate = (i) =>
  toDate(i.confirmed_at) || toDate(i.appointment_at) || toDate(i.old_sticker_expiry)
