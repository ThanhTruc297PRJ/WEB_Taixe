import dayjs from 'dayjs'
import { toDate } from './firestore'

// Một định dạng ngày giờ cho toàn web admin: "21/09/2026 05:25".
export const DATETIME_FORMAT = 'DD/MM/YYYY HH:mm'

/** Nhận Date / chuỗi ISO / Timestamp Firestore; trống thì trả `fallback`. */
export function formatDateTime(value, fallback = '—') {
  if (!value) return fallback
  const d = toDate(value) ?? value
  const parsed = dayjs(d)
  return parsed.isValid() ? parsed.format(DATETIME_FORMAT) : fallback
}
