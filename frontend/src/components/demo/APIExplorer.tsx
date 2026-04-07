'use client'

import React, { useState } from 'react'
import { api } from '@/lib/api'
import { JsonViewer } from '@/components/ui/JsonViewer'
import { Play, ChevronRight } from 'lucide-react'

const ENDPOINTS = [
  {
    id: 'health',
    method: 'GET',
    path: '/health',
    description: 'Liveness probe',
    call: () => api.health(),
  },
  {
    id: 'tasks',
    method: 'GET',
    path: '/tasks',
    description: 'List available tasks',
    call: () => api.tasks(),
  },
  {
    id: 'reset',
    method: 'POST',
    path: '/reset',
    description: 'Start a new episode',
    call: () => api.reset('task1'),
  },
]

export default function APIExplorer() {
  const [selectedEndpoint, setSelectedEndpoint] = useState<string>('health')
  const [response, setResponse] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const endpoint = ENDPOINTS.find(e => e.id === selectedEndpoint)

  const handleRun = async () => {
    if (!endpoint) return
    setLoading(true)
    setError(null)
    try {
      const res = await endpoint.call()
      setResponse(res.data)
    } catch (err: any) {
      setError(err.message || 'Request failed')
      setResponse(null)
    } finally {
      setLoading(false)
    }
  }

  const getCurlCommand = () => {
    if (!endpoint) return ''
    const base = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7860'
    if (endpoint.method === 'GET') {
      return `curl -s ${base}${endpoint.path}`
    }
    return `curl -s -X POST ${base}${endpoint.path} -H "Content-Type: application/json" -d '{}'`
  }

  return (
    <div className="h-full flex flex-col gap-4">
      <div className="flex gap-4 flex-1 min-h-0">
        {/* Endpoint list */}
        <div className="w-48 flex-shrink-0">
          <p className="text-xs font-semibold tracking-widest uppercase text-pink-400 mb-3">
            Endpoints
          </p>
          <div className="space-y-1">
            {ENDPOINTS.map(ep => (
              <button
                key={ep.id}
                onClick={() => setSelectedEndpoint(ep.id)}
                className={`w-full text-left px-3 py-2.5 rounded-xl transition-all ${
                  selectedEndpoint === ep.id
                    ? 'bg-pink-100 border border-pink-300'
                    : 'hover:bg-pink-50 border border-transparent'
                }`}
              >
                <div className="flex items-center gap-2">
                  <span
                    className={`text-xs font-mono font-bold ${
                      ep.method === 'GET' ? 'text-emerald-600' : 'text-amber-600'
                    }`}
                  >
                    {ep.method}
                  </span>
                  <span className="text-xs font-mono text-charcoal">{ep.path}</span>
                </div>
                <p className="text-xs text-muted mt-0.5">{ep.description}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Request/Response */}
        <div className="flex-1 flex flex-col gap-3">
          {endpoint && (
            <div className="bg-pink-50 border border-pink-200 rounded-xl p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span
                    className={`text-sm font-mono font-bold ${
                      endpoint.method === 'GET' ? 'text-emerald-600' : 'text-amber-600'
                    }`}
                  >
                    {endpoint.method}
                  </span>
                  <span className="text-sm font-mono text-charcoal">{endpoint.path}</span>
                </div>
                <button
                  onClick={handleRun}
                  disabled={loading}
                  className="flex items-center gap-2 bg-pink-400 text-white rounded-xl px-4 py-2 text-sm font-semibold hover:bg-pink-500 disabled:opacity-50 transition-all"
                >
                  {loading ? (
                    <div className="w-3 h-3 border border-white/30 border-t-white rounded-full animate-spin" />
                  ) : (
                    <Play className="w-3 h-3" />
                  )}
                  Run
                </button>
              </div>
              <p className="text-xs font-mono text-muted">{getCurlCommand()}</p>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-4">
              <p className="text-sm text-red-600 font-medium">Error: {error}</p>
            </div>
          )}

          {response && (
            <div className="flex-1 overflow-auto">
              <p className="text-xs font-semibold tracking-widest uppercase text-pink-400 mb-2">
                Response
              </p>
              <JsonViewer data={response} />
            </div>
          )}

          {!response && !error && !loading && (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <ChevronRight className="w-8 h-8 text-pink-200 mx-auto mb-2" />
                <p className="text-sm text-muted">Hit &quot;Run&quot; to see the API response</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
