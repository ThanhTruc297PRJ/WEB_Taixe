import { useEffect, useRef, useState } from 'react'
import { auth } from '../services/firebase'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const WS_URL = `${API_BASE.replace(/^http/, 'ws')}/ws/admin`

const PING_MS = 25_000
const RECONNECT_MS = 5_000

/** Kết nối WebSocket tới service, gọi `onAlert(payload)` mỗi khi có tài xế
 * vượt ngưỡng buồn ngủ. Tự ping giữ kết nối + tự kết nối lại khi rớt. */
export function useIncidentAlerts(onAlert) {
  const [connected, setConnected] = useState(false)
  const cbRef = useRef(onAlert)

  useEffect(() => {
    cbRef.current = onAlert
  }, [onAlert])

  useEffect(() => {
    let ws = null
    let pingTimer = null
    let reconnectTimer = null
    let closedByUs = false

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

    const connect = async () => {
      const user = auth.currentUser
      if (!user) {
        reconnectTimer = setTimeout(connect, RECONNECT_MS)
        return
      }
      let token
      try {
        token = await user.getIdToken()
      } catch {
        reconnectTimer = setTimeout(connect, RECONNECT_MS)
        return
      }
      if (closedByUs) return

      ws = new WebSocket(`${WS_URL}?token=${encodeURIComponent(token)}`)

      ws.onopen = () => {
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
      }

      ws.onclose = () => {
        setConnected(false)
        clearInterval(pingTimer)
        if (!closedByUs) reconnectTimer = setTimeout(connect, RECONNECT_MS)
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
