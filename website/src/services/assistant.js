import { apiDelete, apiGet } from './api'

export const listChatLogs = () => apiGet('/assistant/logs')
export const deleteChatLog = (id) => apiDelete(`/assistant/logs/${id}`)
