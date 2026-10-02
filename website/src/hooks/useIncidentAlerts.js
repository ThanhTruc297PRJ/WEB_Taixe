import { useEffect, useRef, useState } from 'react'
import { auth } from '../services/firebase'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const WS_URL = `${API_BASE.replace(/^http/, 'ws')}/ws/admin`

const PING_MS = 25_000
const RECONNECT_MIN_MS = 3_000
const RECONNECT_MAX_MS = 30_000

/** Kết nối WebSocket tới service, gọi `onAlert(payload)` mỗi khi có tài xế
 * vượt ngưỡng buồn ngủ, `onDriverReport(payload)` khi tài xế tự gửi báo cáo,
 * `onJobSubmitted(payload)` khi tài xế báo đã bảo trì / đăng kiểm xong.
 * Tự ping giữ kết nối + tự kết nối lại (backoff) khi rớt. */
export function useIncidentAlerts(onAlert, onDriverReport, onJobSubmitted) {
  const [connected, setConnected] = useState(false)
  const cbRef = useRef(onAlert)
  const reportCbRef = useRef(onDriverReport)
  const jobCbRef = useRef(onJobSubmitted)

  useEffect(() => {
    cbRef.current = onAlert
    reportCbRef.current = onDriverReport
    jobCbRef.current = onJobSubmitted
  }, [onAlert, onDriverReport, onJobSubmitted])

  useEffect(() => {
    let ws = null
    let pingTimer = null
    let reconnectTimer = null
    let closedByUs = false
    let retryMs = RECONNECT_MIN_MS

    const cleanup = () => {
      clearInterval(pingTimer)
      clearTimeout(reconnectTimer)
      if (ws) {
        ws.onopen = ws.onclose = ws.onerror = ws.onmessage = null
        try {
          ws.close()
        } catch {
          /* ignore */
        }
      }
    }

    const scheduleReconnect = () => {
      if (closedByUs) return
      reconnectTimer = setTimeout(connect, retryMs)
      // Backoff: 3s -> 6s -> 12s -> 24s -> 30s (trần), tránh spam khi server sập.
      retryMs = Math.min(retryMs * 2, RECONNECT_MAX_MS)
    }

    const connect = async () => {
      const user = auth.currentUser
      if (!user) {
        scheduleReconnect()
        return
      }
      let token
      try {
        token = await user.getIdToken()
      } catch {
        scheduleReconnect()
        return
      }
      if (closedByUs) return

      ws = new WebSocket(`${WS_URL}?token=${encodeURIComponent(token)}`)

      ws.onopen = () => {
        retryMs = RECONNECT_MIN_MS // kết nối lại được -> reset backoff
        setConnected(true)
        pingTimer = setInterval(() => {
          if (ws?.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }))
          }
        }, PING_MS)
      }

      ws.onmessage = (event) => {
        let msg
        try {
          msg = JSON.parse(event.data)
        } catch {
          return
        }
        if (msg.type === 'alert') cbRef.current?.(msg)
        else if (msg.type === 'driver_report') reportCbRef.current?.(msg)
        else if (msg.type === 'job_submitted') jobCbRef.current?.(msg)
      }

      ws.onclose = () => {
        setConnected(false)
        clearInterval(pingTimer)
        scheduleReconnect()
      }

      ws.onerror = () => {
        try {
          ws.close()
        } catch {
          /* onclose sẽ lo phần kết nối lại */
        }
      }
    }

    connect()

    return () => {
      closedByUs = true
      cleanup()
    }
  }, [])

  return { connected }
}
