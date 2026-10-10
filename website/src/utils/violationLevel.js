// Mức vi phạm theo tổng điểm tích luỹ — dùng chung cho biểu đồ Tổng quan và
// trang Tài xế (bấm vào lát biểu đồ -> danh sách đúng các tài xế đó).

export const DEFAULT_THRESHOLDS = { reminder: 10, warning: 22, suspend: 30 }

export const LEVELS = ['normal', 'reminder', 'warning', 'suspend']

export const LEVEL_META = {
  normal: { label: 'Bình thường', color: 'green' },
  reminder: { label: 'Nhắc nhở', color: 'gold' },
  warning: { label: 'Cảnh cáo', color: 'orange' },
  suspend: { label: 'Đình chỉ', color: 'red' },
}

/** { driver_id: tổng điểm } từ danh sách sự cố. */
export function pointsByDriver(incidents) {
  const points = {}
  for (const i of incidents) {
    if (!i.driver_id) continue
    points[i.driver_id] = (points[i.driver_id] || 0) + (i.points ?? 0)
  }
  return points
}

export function levelOf(points, thresholds = DEFAULT_THRESHOLDS) {
  if (points >= thresholds.suspend) return 'suspend'
  if (points >= thresholds.warning) return 'warning'
  if (points >= thresholds.reminder) return 'reminder'
  return 'normal'
}

/** Mô tả ngưỡng ngắn, VD "từ 22 điểm" / "dưới 10 điểm". */
export function levelRange(level, thresholds = DEFAULT_THRESHOLDS) {
  if (level === 'normal') return `dưới ${thresholds.reminder} điểm`
  return `từ ${thresholds[level]} điểm`
}
