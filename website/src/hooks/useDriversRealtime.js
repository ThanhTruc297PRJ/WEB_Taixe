import { useEffect, useState } from 'react'
import { collection, onSnapshot } from 'firebase/firestore'
import { db } from '../services/firebase'

/** Nghe realtime collection `drivers` bằng Firestore onSnapshot (TASK-C05).
 * Mọi thay đổi document (kể cả do backend ghi qua Admin SDK) đẩy về đây ngay,
 * không cần reload trang. Trả về danh sách đã sắp theo tên. */
export function useDriversRealtime() {
  const [drivers, setDrivers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [pendingCount, setPendingCount] = useState(0)

  useEffect(() => {
    const unsubscribe = onSnapshot(
      collection(db, 'drivers'),
      (snapshot) => {
        const rows = snapshot.docs.map((doc) => ({ id: doc.id, ...doc.data() }))
        rows.sort((a, b) => (a.name ?? '').localeCompare(b.name ?? '', 'vi'))
        setDrivers(rows)
        setPendingCount(rows.filter((d) => d.status === 'pending').length)
        setError(null)
        setLoading(false)
      },
      (err) => {
        setError(err)
        setLoading(false)
      },
    )
    return unsubscribe
  }, [])

  return { drivers, loading, error, pendingCount }
}

/** Firestore Timestamp | ISO string | null -> Date | null */
export function toDate(value) {
  if (!value) return null
  if (typeof value.toDate === 'function') return value.toDate()
  const d = new Date(value)
  return Number.isNaN(d.getTime()) ? null : d
}
