'use client'

import clsx from 'clsx'
import { ScoreBar } from '@/components/ui/ScoreBar'
import type { EpisodeState, Observation } from '@/types'

interface RewardSidebarProps {
  episodeState: EpisodeState
  targetScore: number
}

export default function RewardSidebar({ episodeState, targetScore }: RewardSidebarProps) {
  const { observation, reward } = episodeState
  const lastReward = reward
  const totalReward = reward?.value || 0
  const steps = observation?.turn || 0

  return (
    <aside className="w-72 flex-shrink-0 bg-primary border-l border-border h-screen overflow-y-auto">
      {/* ── Turn Counter ── */}
      <div className="p-4 border-b border-border text-center">
        <p className="text-[10px] font-semibold uppercase tracking-wider text-text-muted">Turn</p>
        <p className="text-4xl font-mono font-bold text-text-primary mt-1">
          {observation?.turn ?? 0}
        </p>
        <p className="text-xs text-text-muted">/ {observation?.max_turns ?? 0}</p>
        {observation && (
          <div className="mt-2 h-1 rounded-full bg-surface overflow-hidden">
            <div
              className="h-full rounded-full bg-accent transition-all duration-500"
              style={{ width: `${((observation.turn) / (observation.max_turns || 1)) * 100}%` }}
            />
          </div>
        )}
      </div>

      {/* ── Score Meters ── */}
      <div className="p-4 space-y-3 border-b border-border">
        <p className="text-[10px] font-semibold uppercase tracking-wider text-text-muted">Score</p>
        <ScoreBar value={totalReward} targetScore={targetScore} />
      </div>

      {/* ── Last Reward Breakdown ── */}
      {lastReward && (
        <div className="p-4 space-y-2 border-b border-border">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-text-muted">Last Reward</p>
          <p className={clsx(
            'text-lg font-mono font-bold',
            lastReward.value >= 0 ? 'text-emerald-400' : 'text-red-400'
          )}>
            {lastReward.value >= 0 ? '+' : ''}{lastReward.value.toFixed(3)}
          </p>
          <div className="space-y-1">
            {Object.entries(lastReward.breakdown || {}).map(([key, val]) => {
              const v = typeof val === 'number' ? val : 0
              if (v === 0) return null
              return (
                <div key={key} className="flex items-center justify-between text-[11px]">
                  <span className="text-text-muted">{key.replace(/_/g, ' ')}</span>
                  <span className={clsx('font-mono', v > 0 ? 'text-emerald-400' : 'text-red-400')}>
                    {v > 0 ? '+' : ''}{v.toFixed(3)}
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* ── Clause Status Mini-list ── */}
      {observation && (
        <div className="p-4 space-y-2">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-text-muted">Clauses</p>
          {observation.clauses.map(clause => {
            const acted = observation.negotiation_history.some(
              t => t.speaker.includes('agent') && t.clause_id === clause.id
            )
            const cpAccepted = observation.negotiation_history.some(
              t => !t.speaker.includes('agent') && t.speaker !== 'system' && t.clause_id === clause.id && t.action_type === 'accept'
            )

            let dotColor = 'bg-slate-500'          // pending
            if (cpAccepted) dotColor = 'bg-emerald-400' // agreed
            else if (acted) dotColor = 'bg-amber-400'   // in progress

            return (
              <div key={clause.id} className="flex items-center gap-2 text-xs">
                <div className={clsx('w-2 h-2 rounded-full', dotColor)} />
                <span className="font-mono text-text-muted w-6">{clause.id}</span>
                <span className="text-text-secondary truncate flex-1">{clause.title}</span>
                {clause.is_deal_breaker && (
                  <span className="text-[9px] text-red-400 font-medium">DB</span>
                )}
              </div>
            )
          })}
        </div>
      )}

      {/* ── Summary Stats ── */}
      <div className="p-4 border-t border-border">
        <div className="grid grid-cols-2 gap-3 text-xs">
          <div>
            <p className="text-text-muted">Total Reward</p>
            <p className={clsx('font-mono font-bold', totalReward >= 0 ? 'text-emerald-400' : 'text-red-400')}>
              {totalReward.toFixed(3)}
            </p>
          </div>
          <div>
            <p className="text-text-muted">Steps</p>
            <p className="font-mono font-bold text-text-primary">{steps}</p>
          </div>
        </div>
      </div>
    </aside>
  )
}
