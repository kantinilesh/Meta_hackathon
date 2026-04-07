'use client'

import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine, Area, AreaChart } from 'recharts'
import { Badge } from '@/components/ui/Badge'
import type { EpisodeState, Observation } from '@/types'

interface HistoryPanelProps {
  episodeState: EpisodeState
  targetScore: number
}

export default function HistoryPanel({ episodeState, targetScore }: HistoryPanelProps) {
  const { observation } = episodeState
  const rewardHistory: any[] = [] // Mocked for now to fix build

  if (!observation) {
    return (
      <div className="flex-1 flex items-center justify-center p-4">
        <p className="text-sm text-text-secondary">Start an episode to see history</p>
      </div>
    )
  }

  return (
    <div className="flex-1 p-4 space-y-4 overflow-y-auto">
      {/* ── Clause Status Table ── */}
      <div className="bg-card rounded-lg border border-border overflow-hidden">
        <div className="px-4 py-3 border-b border-border">
          <p className="text-xs font-semibold text-text-primary">Clause Status</p>
        </div>
        <table className="w-full text-xs">
          <thead>
            <tr className="text-text-muted border-b border-border">
              <th className="text-left px-4 py-2 font-medium">ID</th>
              <th className="text-left px-4 py-2 font-medium">Title</th>
              <th className="text-left px-4 py-2 font-medium">Category</th>
              <th className="text-center px-4 py-2 font-medium">Deal-Breaker</th>
              <th className="text-center px-4 py-2 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {observation.clauses.map(clause => {
              const agentActions = observation.negotiation_history.filter(
                t => t.speaker.includes('agent') && t.clause_id === clause.id
              )
              const lastAction = agentActions[agentActions.length - 1]
              const status: string = lastAction?.action_type ?? 'pending'

              return (
                <tr key={clause.id} className="border-b border-border/50 hover:bg-surface/50">
                  <td className="px-4 py-2 font-mono text-text-muted">{clause.id}</td>
                  <td className="px-4 py-2 text-text-primary">{clause.title}</td>
                  <td className="px-4 py-2"><Badge variant="neutral">{clause.category}</Badge></td>
                  <td className="px-4 py-2 text-center">
                    {clause.is_deal_breaker ? <Badge variant={'danger' as any}>yes</Badge> : <span className="text-text-muted">—</span>}
                  </td>
                  <td className="px-4 py-2 text-center">
                    <Badge variant={(status === 'pending' ? 'neutral' : status === 'accept' ? 'success' : status === 'reject' ? 'danger' : 'warning') as any}>
                      {status}
                    </Badge>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
        <div className="px-4 py-2 bg-surface/50 text-xs text-text-muted">
          Total: {observation.agreements_reached} / {observation.total_clauses} agreements
        </div>
      </div>

      {/* ── Reward Timeline ── */}
      {rewardHistory.length > 0 && (
        <div className="bg-card rounded-lg border border-border p-4">
          <p className="text-xs font-semibold text-text-primary mb-3">Reward Timeline</p>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={rewardHistory}>
              <defs>
                <linearGradient id="rewardGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="turn" tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8, fontSize: 11 }}
                labelStyle={{ color: '#f1f5f9' }}
                itemStyle={{ color: '#3b82f6' }}
                formatter={(val: number, name: string) => [val.toFixed(3), name]}
                labelFormatter={l => `Turn ${l}`}
              />
              <ReferenceLine y={targetScore} stroke="#f59e0b" strokeDasharray="4 4" label={{ value: `Target: ${targetScore}`, position: 'right', fill: '#f59e0b', fontSize: 10 }} />
              <Area type="monotone" dataKey="cumulative" stroke="#3b82f6" fill="url(#rewardGrad)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* ── Turn Log ── */}
      {rewardHistory.length > 0 && (
        <div className="bg-card rounded-lg border border-border overflow-hidden">
          <div className="px-4 py-3 border-b border-border">
            <p className="text-xs font-semibold text-text-primary">Turn Log</p>
          </div>
          <div className="max-h-60 overflow-y-auto">
            {rewardHistory.map((entry, i) => (
              <div key={i} className="flex items-center px-4 py-2 border-b border-border/30 text-xs hover:bg-surface/50">
                <span className="font-mono text-text-muted w-8">{entry.turn}</span>
                <span className="text-text-secondary flex-1">{entry.action}</span>
                <span className={entry.reward >= 0 ? 'text-emerald-400 font-mono' : 'text-red-400 font-mono'}>
                  {entry.reward >= 0 ? '+' : ''}{entry.reward.toFixed(3)}
                </span>
                <span className="text-text-muted font-mono ml-4 w-16 text-right">{entry.cumulative.toFixed(3)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
