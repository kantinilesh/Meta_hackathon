'use client'

import { useState } from 'react'
import clsx from 'clsx'
import { AlertTriangle, Send } from 'lucide-react'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import type { Observation, Clause, Action, ActionType, ClauseLabel } from '@/types'

interface NegotiatePanelProps {
  observation: Observation | null
  selectedClause: Clause | null
  onSelectClause: (clause: Clause) => void
  onStep: (action: Action) => void
  isLoading: boolean
  taskId: string
}

const ACTION_TYPES: ActionType[] = ['flag', 'propose', 'accept', 'reject']
const LABELS: ClauseLabel[] = ['fair', 'unfair', 'neutral']
const REASONS = ['scope', 'duration', 'ip', 'liability', 'jurisdiction', 'payment', 'termination']

export default function NegotiatePanel({
  observation,
  selectedClause,
  onSelectClause,
  onStep,
  isLoading,
  taskId,
}: NegotiatePanelProps) {
  const [actionType, setActionType] = useState<ActionType>('flag')
  const [label, setLabel] = useState<ClauseLabel>('unfair')
  const [reason, setReason] = useState('')
  const [proposedText, setProposedText] = useState('')

  if (!observation) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center space-y-3">
          <div className="w-16 h-16 rounded-full bg-surface flex items-center justify-center mx-auto">
            <Send className="w-7 h-7 text-text-muted" />
          </div>
          <p className="text-text-secondary text-sm">Reset an episode to start negotiating</p>
        </div>
      </div>
    )
  }

  const handleSubmit = () => {
    if (!selectedClause) return
    const action: Action = {
      clause_id: selectedClause.id,
      action_type: actionType,
      label,
      reason: reason || undefined,
      proposed_text: proposedText || undefined,
    }
    onStep(action)
  }

  // Track which clauses agent has already acted on
  const actedClauseIds = new Set(
    observation.negotiation_history
      .filter(t => t.speaker.includes('agent'))
      .map(t => t.clause_id)
  )

  return (
    <div className="flex-1 flex gap-4 p-4 overflow-hidden">
      {/* ── Left: Contract + Clauses ── */}
      <div className="flex-[3] flex flex-col gap-4 min-w-0 overflow-y-auto">
        {/* Contract header */}
        <div className="bg-card rounded-lg border border-border p-4">
          <h2 className="text-sm font-semibold text-text-primary">{observation.contract_title}</h2>
          <p className="text-xs text-text-muted mt-1 font-mono">
            Turn {observation.turn} / {observation.max_turns} · {observation.agreements_reached} / {observation.total_clauses} agreements
          </p>
          <div className="mt-3 max-h-28 overflow-y-auto rounded bg-surface p-3 text-xs text-text-secondary leading-relaxed font-mono">
            {observation.contract_text}
          </div>
        </div>

        {/* Clause list */}
        <div className="space-y-2">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-text-muted">Clauses</p>
          {observation.clauses.map(clause => {
            const isSelected = selectedClause?.id === clause.id
            const isActed = actedClauseIds.has(clause.id)
            return (
              <button
                key={clause.id}
                onClick={() => onSelectClause(clause)}
                className={clsx(
                  'w-full text-left p-3 rounded-lg border transition-colors',
                  isSelected
                    ? 'border-accent bg-accent/10'
                    : isActed
                      ? 'border-emerald-500/30 bg-emerald-500/5'
                      : 'border-border hover:bg-surface'
                )}
              >
                <div className="flex items-center gap-2">
                  <span className="font-mono text-[10px] text-text-muted">{clause.id}</span>
                  <span className="text-xs font-medium text-text-primary truncate">{clause.title}</span>
                  {clause.is_deal_breaker && <Badge variant={'danger' as any}>deal-breaker</Badge>}
                  <Badge variant="neutral">{clause.category}</Badge>
                  {isActed && <Badge variant={'success' as any}>done</Badge>}
                </div>
                <p className="text-[11px] text-text-muted mt-1 line-clamp-2">{clause.text}</p>
              </button>
            )
          })}
        </div>

        {/* Negotiation chat (task3) */}
        {taskId === 'task3' && observation.negotiation_history.length > 0 && (
          <div className="bg-card rounded-lg border border-border p-4 space-y-2">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-text-muted">Negotiation</p>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {observation.negotiation_history.map((turn, i) => (
                <div
                  key={i}
                  className={clsx(
                    'flex',
                    turn.speaker.includes('agent') ? 'justify-end' : 'justify-start'
                  )}
                >
                  <div
                    className={clsx(
                      'max-w-[80%] rounded-lg px-3 py-2 text-xs',
                      turn.speaker.includes('agent')
                        ? 'bg-accent/20 text-blue-300'
                        : 'bg-surface text-text-secondary'
                    )}
                  >
                    <p className="text-[10px] text-text-muted mb-0.5">
                      {turn.speaker} · {turn.action_type} · {turn.clause_id}
                    </p>
                    <p>{turn.content}</p>
                    {turn.speaker.includes('agent') && turn.reward_delta !== undefined && turn.reward_delta !== 0 && (
                      <p className={clsx(
                        'text-[10px] mt-1 font-mono',
                        turn.reward_delta > 0 ? 'text-emerald-400' : 'text-red-400'
                      )}>
                        {turn.reward_delta > 0 ? '+' : ''}{turn.reward_delta.toFixed(2)}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* ── Right: Action Panel ── */}
      <div className="flex-[2] flex flex-col gap-4 min-w-[280px] max-w-[360px]">
        {selectedClause ? (
          <div className="bg-card rounded-lg border border-border p-4 space-y-4">
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-wider text-text-muted">Selected Clause</p>
              <p className="text-sm font-medium text-text-primary mt-1">{selectedClause.title}</p>
              <div className="flex gap-1.5 mt-1">
                <Badge variant="neutral">{selectedClause.category}</Badge>
                {selectedClause.is_deal_breaker && <Badge variant={'danger' as any}>deal-breaker</Badge>}
              </div>
            </div>

            {/* Action type selector */}
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-wider text-text-muted mb-2">Action</p>
              <div className="grid grid-cols-4 gap-1">
                {ACTION_TYPES.map(at => (
                  <button
                    key={at}
                    onClick={() => setActionType(at)}
                    className={clsx(
                      'px-2 py-1.5 rounded text-xs font-medium transition-colors capitalize',
                      actionType === at
                        ? 'bg-accent text-white'
                        : 'bg-surface text-text-secondary hover:text-text-primary'
                    )}
                  >
                    {at}
                  </button>
                ))}
              </div>
            </div>

            {/* Conditional fields */}
            {actionType === 'flag' && (
              <>
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-text-muted mb-2">Label</p>
                  <div className="flex gap-1">
                    {LABELS.map(l => (
                      <button
                        key={l}
                        onClick={() => setLabel(l)}
                        className={clsx(
                          'px-3 py-1.5 rounded text-xs font-medium transition-colors capitalize',
                          label === l
                            ? l === 'unfair' ? 'bg-red-500/20 text-red-400' : l === 'fair' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-500/20 text-slate-400'
                            : 'bg-surface text-text-secondary hover:text-text-primary'
                        )}
                      >
                        {l}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-text-muted mb-2">Reason</p>
                  <select
                    value={reason}
                    onChange={e => setReason(e.target.value)}
                    className="w-full bg-surface border border-border rounded px-3 py-2 text-xs text-text-primary focus:outline-none focus:ring-1 focus:ring-accent"
                  >
                    <option value="">Select reason…</option>
                    {REASONS.map(r => (
                      <option key={r} value={r}>{r}</option>
                    ))}
                  </select>
                </div>
              </>
            )}

            {actionType === 'propose' && (
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-wider text-text-muted mb-2">Proposed Text</p>
                <textarea
                  value={proposedText}
                  onChange={e => setProposedText(e.target.value)}
                  rows={4}
                  placeholder="Enter your proposed replacement clause text…"
                  className="w-full bg-surface border border-border rounded px-3 py-2 text-xs text-text-primary placeholder-text-muted resize-none focus:outline-none focus:ring-1 focus:ring-accent"
                />
                <p className="text-[10px] text-text-muted mt-1">
                  {proposedText.length} chars · Include: duration, scope, carve-out
                </p>
              </div>
            )}

            {(actionType === 'accept' || actionType === 'reject') && (
              <div className="bg-surface rounded p-3">
                <p className="text-xs text-text-secondary">
                  {actionType === 'accept' ? '✓ Accept' : '✗ Reject'} the current terms for{' '}
                  <span className="text-text-primary font-medium">{selectedClause.title}</span>
                </p>
              </div>
            )}

            <Button onClick={handleSubmit} isLoading={isLoading} className="w-full">
              <Send className="w-3.5 h-3.5" /> Submit Action
            </Button>
          </div>
        ) : (
          <div className="bg-card rounded-lg border border-border p-6 flex items-center justify-center">
            <div className="text-center space-y-2">
              <AlertTriangle className="w-8 h-8 text-text-muted mx-auto" />
              <p className="text-xs text-text-secondary">Select a clause to take action</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
