import { auth } from './firebase'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export async function apiPost(path, body) {
  const idToken = await auth.currentUser?.getIdToken()

  const res = await fetch(`${API_BASE_URL}${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(idToken ? { Authorization: `Bearer ${idToken}` } : {}),
    },
    body: JSON.stringify(body),
  })

  if (!res.ok) {
    const detail = await res.json().catch(() => null)
    throw new Error(detail?.detail || `Yêu cầu thất bại (${res.status})`)
  }

  return res.json()
}
