import { auth } from './firebase'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

async function request(method, path, body) {
  const idToken = await auth.currentUser?.getIdToken()
  const hasBody = body !== undefined

  const res = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers: {
      ...(hasBody ? { 'Content-Type': 'application/json' } : {}),
      ...(idToken ? { Authorization: `Bearer ${idToken}` } : {}),
    },
    ...(hasBody ? { body: JSON.stringify(body) } : {}),
  })

  if (!res.ok) {
    const detail = await res.json().catch(() => null)
    throw new Error(detail?.detail || `Yêu cầu thất bại (${res.status})`)
  }

  if (res.status === 204) return null
  return res.json()
}

export const apiGet = (path) => request('GET', path)
export const apiPost = (path, body) => request('POST', path, body ?? {})
export const apiPut = (path, body) => request('PUT', path, body ?? {})
export const apiDelete = (path) => request('DELETE', path)
