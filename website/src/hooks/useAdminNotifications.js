import { useCallback, useEffect, useRef, useState } from 'react'
import { getAdminNotifications } from '../services/adminNotifications'

const POLL_MS = 45_000

const EMPTY_SECTION = { count: 0, items: [] }

const EMPTY_DATA = {
  pending_drivers: EMPTY_SECTION,
  maintenance_due: EMPTY_SECTION,
  inspections_due: EMPTY_SECTION,
  recent_incidents: EMPTY_SECTION,
  driver_reports: EMPTY_SECTION,
  awaiting_confirmation: EMPTY_SECTION,
  reported_music: EMPTY_SECTION,
  total: 0,
}

const SEEN_STORAGE_KEY = 'admin_notifications_seen_v1'

// Lưu trên trình duyệt (không cần bấm gì thêm để "đánh dấu đã đọc" từng cái) —
// đơn giản, đủ dùng cho quy mô vài admin. Nếu đăng nhập trình duyệt khác thì
// badge sẽ hiện lại như mới, chấp nhận được cho tính năng phụ trợ này.
function loadSeen() {
  try {
    const raw = localStorage.getItem(SEEN_STORAGE_KEY)
    if (!raw) return { ids: [], total: 0 }
    const parsed = JSON.parse(raw)
    return { ids: Array.isArray(parsed.ids) ? parsed.ids : [], total: parsed.total ?? 0 }
  } catch {
    return { ids: [], total: 0 }
  }
}

function saveSeen(ids, total) {
  try {
    localStorage.setItem(SEEN_STORAGE_KEY, JSON.stringify({ ids, total }))
  } catch {
    /* localStorage có thể bị chặn (chế độ ẩn danh...) — bỏ qua, không chặn UI */
  }
}

function collectIds(data) {
  return Object.keys(EMPTY_DATA)
    .filter((k) => k !== 'total')
    .flatMap((k) => (data[k]?.items ?? []).map((item) => item.id))
}

/** Tải + polling định kỳ danh sách việc cần admin chú ý (chuông thông báo).
 * `refreshSignal` đổi giá trị (VD: có cảnh báo buồn ngủ mới) -> tải lại ngay,
 * không cần chờ hết chu kỳ poll.
 *
 * Có thêm cơ chế "đã xem": `unseenCount` chỉ tính các mục CHƯA từng hiện ra
 * lúc admin mở chuông lần gần nhất (hoặc tổng số tăng lên so với lần đó) —
 * để badge đỏ không nhắc mãi những việc admin đã biết nhưng chưa xử lý xong.
 * Danh sách trong panel vẫn hiển thị đủ, chỉ badge là được "làm dịu". Gọi
 * `markSeen()` khi admin mở panel ra xem. */
export function useAdminNotifications(refreshSignal) {
  const [data, setData] = useState(EMPTY_DATA)
  const [error, setError] = useState(null)
  // true tới khi tải xong lần đầu (thành công hay lỗi) — để UI hiện vòng xoay.
  const [loading, setLoading] = useState(true)
  const [seen, setSeen] = useState(loadSeen)
  const mountedRef = useRef(true)

  const refresh = useCallback(async () => {
    try {
      const res = await getAdminNotifications()
      if (mountedRef.current) {
        setData(res)
        setError(null)
      }
    } catch (e) {
      // Không làm phiền admin bằng toast, nhưng vẫn phải phân biệt được với
      // "thật sự không có gì" — nếu không, một lỗi gọi API (backend chưa
      // restart, mất mạng...) trông giống hệt trạng thái rỗng bình thường.
      if (mountedRef.current) setError(e?.message || 'Không tải được thông báo')
    } finally {
      if (mountedRef.current) setLoading(false)
    }
  }, [])

  useEffect(() => {
    mountedRef.current = true
    // eslint-disable-next-line react-hooks/set-state-in-effect -- nạp dữ liệu 1 lần khi mount + polling định kỳ
    refresh()
    const timer = setInterval(refresh, POLL_MS)
    return () => {
      mountedRef.current = false
      clearInterval(timer)
    }
  }, [refresh])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- tải lại ngay khi có cảnh báo mới, không chờ hết chu kỳ poll
    if (refreshSignal) refresh()
  }, [refreshSignal, refresh])

  const markSeen = useCallback(() => {
    setData((current) => {
      const ids = collectIds(current)
      const next = { ids, total: current.total }
      saveSeen(next.ids, next.total)
      setSeen(next)
      return current
    })
  }, [])

  const currentIds = collectIds(data)
  const seenIdSet = new Set(seen.ids)
  const hasNewSinceSeen =
    currentIds.some((id) => !seenIdSet.has(id)) || data.total > seen.total
  const unseenCount = hasNewSinceSeen ? data.total : 0

  return { data, error, loading, refresh, unseenCount, markSeen, seenIds: seen.ids }
}
