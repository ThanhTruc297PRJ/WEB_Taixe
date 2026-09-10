import { useContext } from 'react'
import { DriversContext } from './driversContextValue'

/** Danh sách tài xế realtime (1 listener Firestore dùng chung). */
export function useDrivers() {
  const ctx = useContext(DriversContext)
  if (!ctx) throw new Error('useDrivers phải nằm trong <DriversProvider>')
  return ctx
}
