'use client'

import { useState } from 'react'
import clsx from 'clsx'
import { Send, Copy, Check } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { JsonViewer } from '@/components/ui/JsonViewer'
import { Badge } from '@/components/ui/Badge'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7860'

interface Endpoint {
  method: 'GET' | 'POST'
  path: string
  description: string
  body?: string
}

const ENDPOINTS: Endpoint[] = [
  { method: 'GET', path: '/health', description: 'Liveness probe' },
  { method: 'GET', path: '/tasks', description: 'List available tasks' },
  { method: 'POST', path: '/reset', description: 'Start a new episode', body: '{\n  "task_id": "task1"\n}' },
  { method: 'POST', path: '/step', description: 'Submit an action', body: '{\n  "session_id": "YOUR_SESSION_ID",\n  "action": {\n    "clause_id": "c1",\n    "action_type": "flag",\n    "label": "unfair",\n    "reason": "IP clause too broad"\n  }\n}' },
  { method: 'GET', path: '/state', description: 'Get current state (add ?session_id=…)' },
  { method: 'POST', path: '/grade', description: 'Grade episode', body: '{\n  "session_id": "YOUR_SESSION_ID",\n  "task_id": "task1"\n}' },
]

export default function APIPanel() {
  const [selected, setSelected] = useState(0)
  const [body, setBody] = useState(ENDPOINTS[0].body ?? '')
  const [response, setResponse] = useState<any>(null)
  const [status, setStatus] = useState<number | null>(null)
  const [duration, setDuration] = useState<number | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [copiedCurl, setCopiedCurl] = useState(false)

  const ep = ENDPOINTS[selected]

  const handleSelect = (i: number) => {
    setSelected(i)
    setBody(ENDPOINTS[i].body ?? '')
    setResponse(null)
    setStatus(null)
    setDuration(null)
  }

  const handleSend = async () => {
    setIsLoading(true)
    const start = performance.now()
    try {
      const opts: RequestInit = {
        method: ep.method,
        headers: { 'Content-Type': 'application/json' },
      }
      if (ep.method === 'POST' && body) opts.body = body
      const url = ep.method === 'GET' && ep.path === '/state'
        ? `${API_URL}${ep.path}?session_id=test`
        : `${API_URL}${ep.path}`
      const res = await fetch(url, opts)
      setStatus(res.status)
      setDuration(Math.round(performance.now() - start))
      const data = await res.json()
      setResponse(data)
    } catch (err) {
      setStatus(0)
      setDuration(Math.round(performance.now() - start))
      setResponse({ error: String(err) })
    } finally {
      setIsLoading(false)
    }
  }

  const curlCmd = ep.method === 'POST'
    ? `curl -X POST ${API_URL}${ep.path} \\\n  -H "Content-Type: application/json" \\\n  -d '${(body || '{}').replace(/\n/g, '')}'`
    : `curl ${API_URL}${ep.path}`

  const handleCopyCurl = () => {
    navigator.clipboard.writeText(curlCmd)
    setCopiedCurl(true)
    setTimeout(() => setCopiedCurl(false), 2000)
  }

  return (
    <div className="flex-1 flex gap-4 p-4 overflow-hidden">
      {/* ── Endpoint List ── */}
      <div className="w-56 flex-shrink-0 space-y-1.5">
        <p className="text-[10px] font-semibold uppercase tracking-wider text-text-muted mb-2">Endpoints</p>
        {ENDPOINTS.map((e, i) => (
          <button
            key={i}
            onClick={() => handleSelect(i)}
            className={clsx(
              'w-full text-left px-3 py-2 rounded-lg border text-xs transition-colors',
              selected === i ? 'border-accent bg-accent/10' : 'border-border hover:bg-surface'
            )}
          >
            <div className="flex items-center gap-2">
              <Badge variant={e.method === 'GET' ? 'success' as any : 'info' as any}>{e.method}</Badge>
              <span className="font-mono text-text-primary">{e.path}</span>
            </div>
            <p className="text-[10px] text-text-muted mt-0.5">{e.description}</p>
          </button>
        ))}
      </div>

      {/* ── Request / Response ── */}
      <div className="flex-1 flex flex-col gap-4 min-w-0">
        {/* Request */}
        <div className="bg-card rounded-lg border border-border p-4 space-y-3">
          <div className="flex items-center gap-2">
            <Badge variant={ep.method === 'GET' ? 'success' as any : 'info' as any}>{ep.method}</Badge>
            <span className="font-mono text-sm text-text-primary">{API_URL}{ep.path}</span>
          </div>
          {ep.method === 'POST' && (
            <textarea
              value={body}
              onChange={e => setBody(e.target.value)}
              rows={6}
              className="w-full bg-surface border border-border rounded px-3 py-2 text-xs font-mono text-text-primary resize-none focus:outline-none focus:ring-1 focus:ring-accent"
            />
          )}
          <Button onClick={handleSend} isLoading={isLoading}>
            <Send className="w-3.5 h-3.5" /> Send Request
          </Button>
        </div>

        {/* Response */}
        {response !== null && (
          <div className="bg-card rounded-lg border border-border p-4 space-y-2">
            <div className="flex items-center gap-3">
              <Badge variant={status && status >= 200 && status < 300 ? 'success' as any : 'danger' as any}>
                {status}
              </Badge>
              {duration !== null && <span className="text-xs text-text-muted">{duration}ms</span>}
            </div>
            <JsonViewer data={response} />
          </div>
        )}

        {/* Curl */}
        <div className="bg-card rounded-lg border border-border p-4">
          <div className="flex items-center justify-between mb-2">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-text-muted">cURL</p>
            <button onClick={handleCopyCurl} className="text-text-muted hover:text-text-primary transition-colors">
              {copiedCurl ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            </button>
          </div>
          <pre className="text-xs font-mono text-text-secondary whitespace-pre-wrap">{curlCmd}</pre>
        </div>
      </div>
    </div>
  )
}

