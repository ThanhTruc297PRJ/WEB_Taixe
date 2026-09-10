import { useEffect, useMemo, useState } from 'react'
import { collection, onSnapshot } from 'firebase/firestore'
import { db } from '../services/firebase'
import { DriversContext } from './driversContextValue'

// Một listener Firestore duy nhất cho collection `drivers`, chia sẻ cho Sidebar
// + trang Tổng quan + trang Quản lý tài xế (trước đây mỗi nơi tự mở 1 listener).

export function DriversProvider({ children }) {
  const [drivers, setDrivers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const unsubscribe = onSnapshot(
      collection(db, 'drivers'),
      (snapshot) => {
        const rows = snapshot.docs.map((doc) => ({ id: doc.id, ...doc.data() }))
        rows.sort((a, b) => (a.name ?? '').localeCompare(b.name ?? '', 'vi'))
        setDrivers(rows)
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

  const value = useMemo(
    () => ({
      drivers,
      loading,
      error,
      pendingCount: drivers.filter((d) => d.status === 'pending').length,
    }),
    [drivers, loading, error],
  )

  return (
    <DriversContext.Provider value={value}>{children}</DriversContext.Provider>
  )
}
