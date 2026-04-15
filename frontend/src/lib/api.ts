import axios from 'axios'

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7860'
const WS_BASE = BASE_URL.replace('http', 'ws').replace('https', 'wss')

const client = axios.create({ 
  baseURL: BASE_URL, 
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' } 
})

const multipartClient = axios.create({
  baseURL: BASE_URL,
  timeout: 60000,
})

export const api = {
  health: () => client.get('/health'),
  reset: (taskId: string, sessionId?: string) => client.post('/reset', { task_id: taskId, session_id: sessionId }),
  step: (sessionId: string, action: any) => client.post('/step', { session_id: sessionId, action }),
  state: (sessionId: string) => client.get('/state', { params: { session_id: sessionId } }),
  tasks: () => client.get('/tasks'),
  grade: (sessionId: string, taskId: string) => client.post('/grade', { session_id: sessionId, task_id: taskId }),
  document: {
    upload: async (file: File, sessionId: string, documentType: string, extractTerms: boolean = true) => {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('session_id', sessionId)
      formData.append('document_type', documentType)
      formData.append('extract_terms', String(extractTerms))
      return multipartClient.post('/document/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
    },
    list: (sessionId: string) => client.get('/session/documents', { params: { session_id: sessionId } }),
    link: (sessionId: string, role: string, documentIds: string[]) => 
      client.post('/session/link-documents', { session_id: sessionId, role, document_ids: documentIds }),
  },
  session: {
    create: (data: any) => client.post('/session/create', data),
    join: (data: any) => client.post('/session/join', data),
    start: (sessionId: string) => client.post('/session/start', { session_id: sessionId }),
    status: (sessionId?: string, inviteToken?: string, role?: string) => 
      client.get('/session/status', { params: { session_id: sessionId, invite_token: inviteToken, role } }),
    sign: (sessionId: string, role: string) => client.post('/session/sign', { session_id: sessionId, role }),
    contract: (sessionId: string) => client.get('/session/contract', { params: { session_id: sessionId } }),
  },
}

export const WS_URL = (sessionId: string, role: string) => `${WS_BASE}/ws/${sessionId}?role=${role}`

export const generateSessionId = () => `session_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`
