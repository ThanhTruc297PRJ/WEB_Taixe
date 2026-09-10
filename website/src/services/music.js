import { apiGet, apiPut } from './api'

export const listTracks = () => apiGet('/music/tracks')

export const toggleTrack = (id, enabled, reason) =>
  apiPut(`/music/tracks/${id}/toggle`, { enabled, reason })
