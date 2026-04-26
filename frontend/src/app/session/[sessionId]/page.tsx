'use client'

import { useEffect, useState, useRef } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useNegotiationSocket } from '@/hooks/useNegotiationSocket'
import { api } from '@/lib/api'
import { InterventionModal } from '@/components/session/InterventionModal'
import { NegotiationSession, NegotiationTurn, Clause } from '@/types'
import { AlertTriangle, CheckCircle2, Clock, Pause, Play, FileText, Zap, Shield, Bomb } from 'lucide-react'
import clsx from 'clsx'

/* ── helpers ── */
function ActionBadge({ type }: { type: string }) {
  const map: Record<string, string> = {
    propose: 'bg-blue-100 text-blue-700 border-blue-200',
    accept:  'bg-emerald-100 text-emerald-700 border-emerald-200',
    reject:  'bg-red-100 text-red-600 border-red-200',
    counter: 'bg-amber-100 text-amber-700 border-amber-200',
    skip:    'bg-slate-100 text-slate-500 border-slate-200',
  }
  return (
    <span className={clsx('text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border', map[type] || map.skip)}>
      {type}
    </span>
  )
}

function ClauseStatusDot({ status }: { status: string }) {
  const map: Record<string, string> = {
    agreed: 'bg-emerald-400',
    in_negotiation: 'bg-amber-400 animate-pulse',
    rejected: 'bg-red-400',
    pending: 'bg-slate-300',
  }
  return <span className={clsx('w-2.5 h-2.5 rounded-full flex-shrink-0', map[status] || 'bg-slate-300')} />
}

function TurnBubble({ turn, isSeller }: { turn: NegotiationTurn, isSeller: boolean }) {
  if (turn.speaker === 'system') {
    return (
      <div className="flex justify-center my-3">
        <div className="flex items-center gap-2 bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs font-semibold px-4 py-1.5 rounded-full shadow-sm">
          <CheckCircle2 className="w-3.5 h-3.5" />
          {turn.content}
        </div>
      </div>
    )
  }

  const isSpeakerSeller = turn.speaker === 'seller_agent'

  return (
    <div className={clsx('flex gap-3 my-3', isSpeakerSeller ? 'justify-start' : 'justify-end')}>
      {isSpeakerSeller && (
        <div className="w-9 h-9 rounded-full bg-gradient-to-br from-pink-400 to-rose-500 text-white flex items-center justify-center font-bold text-sm shadow-md flex-shrink-0">
          S
        </div>
      )}
      <div className={clsx('flex flex-col gap-1.5 max-w-[78%]', !isSpeakerSeller && 'items-end')}>
        <div className={clsx(
          'px-4 py-3 rounded-2xl shadow-sm text-sm leading-relaxed',
          isSpeakerSeller
            ? 'bg-pink-50 border border-pink-200 rounded-tl-sm text-slate-800'
            : 'bg-blue-50 border border-blue-200 text-slate-800 rounded-tr-sm'
        )}>
          <p>{turn.content}</p>
          {turn.proposed_text && (
            <div className={clsx(
              'mt-3 border-l-4 pl-3 py-2 rounded-r-lg text-xs',
              isSpeakerSeller
                ? 'bg-pink-100/60 border-pink-400 text-pink-900'
                : 'bg-blue-100/60 border-blue-400 text-blue-900'
            )}>
              <p className="text-[10px] font-bold uppercase tracking-wider mb-1 opacity-70">📝 Proposed Redline</p>
              <p className="italic leading-relaxed">&ldquo;{turn.proposed_text}&rdquo;</p>
            </div>
          )}
        </div>
        <div className={clsx('flex items-center gap-2 text-[10px] text-slate-400 px-1', !isSpeakerSeller && 'flex-row-reverse')}>
          <ActionBadge type={turn.action_type} />
          <span>Clause {turn.clause_id}</span>
          <span>·</span>
          <span>Turn {turn.turn_number}</span>
        </div>
      </div>
      {!isSpeakerSeller && (
        <div className="w-9 h-9 rounded-full bg-gradient-to-br from-blue-400 to-indigo-600 text-white flex items-center justify-center font-bold text-sm shadow-md flex-shrink-0">
          C
        </div>
      )}
    </div>
  )
}

function TypingDots({ speaker }: { speaker: string }) {
  const isSeller = speaker === 'seller_agent'
  return (
    <div className={clsx('flex gap-3 my-2', isSeller ? 'justify-start' : 'justify-end')}>
      {isSeller && <div className="w-9 h-9 rounded-full bg-gradient-to-br from-pink-400 to-rose-500 flex-shrink-0" />}
      <div className={clsx('px-4 py-3 rounded-2xl flex items-center gap-1.5', isSeller ? 'bg-pink-50 border border-pink-200' : 'bg-blue-50 border border-blue-200')}>
        {[0, 1, 2].map(i => (
          <span key={i} className={clsx('w-2 h-2 rounded-full', isSeller ? 'bg-pink-400' : 'bg-blue-400')}
            style={{ animation: `bounce 1.2s ease-in-out ${i * 0.2}s infinite` }} />
        ))}
      </div>
      {!isSeller && <div className="w-9 h-9 rounded-full bg-gradient-to-br from-slate-600 to-slate-800 flex-shrink-0" />}
    </div>
  )
}

/* ── Main Page ── */
export default function SessionRoom({ params }: { params: { sessionId: string } }) {
  const router = useRouter()
  const searchParams = useSearchParams()
  const role = (searchParams.get('role') as 'seller' | 'client') || 'seller'
  const taskId = searchParams.get('task') || 'task1'
  const syriaEnabled = searchParams.get('syria') === '1'

  const { turns, isConnected, isComplete } = useNegotiationSocket(params.sessionId, role)
  const [sessionData, setSessionData] = useState<NegotiationSession | null>(null)
  const [activeClauseId, setActiveClauseId] = useState<string>('c2')
  const [showIntervention, setShowIntervention] = useState(false)
  const [isPaused, setIsPaused] = useState(false)
  const [evidenceBombUsed, setEvidenceBombUsed] = useState(false)
  const [evidenceBombLoading, setEvidenceBombLoading] = useState(false)
  const chatBottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await api.session.status(params.sessionId, undefined, role)
        setSessionData(res.data)
        if (res.data.status === 'paused') setIsPaused(true)
        else setIsPaused(false)
        
        const clauses = res.data.clauses || []
        if (clauses.length > 0 && !activeClauseId) setActiveClauseId(clauses[0].id)
      } catch (err) {
        console.error("Status poll failed", err)
      }
    }

    fetchStatus()
    const interval = setInterval(fetchStatus, 5000)
    return () => clearInterval(interval)
  }, [params.sessionId, role])

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [turns])

  // Merge socket turns into clause state
  const clauses: Clause[] = sessionData ? [...sessionData.clauses] : []
  turns.forEach(t => {
    const c = clauses.find(x => x.id === t.clause_id)
    if (c) {
      if (t.proposed_text) c.current_proposed_text = t.proposed_text
      if (t.action_type === 'accept') c.status = 'agreed'
      else if (t.action_type === 'propose' && t.proposed_text) c.status = 'in_negotiation'
    }
  })

  const me = role === 'seller' ? sessionData?.seller_config : sessionData?.client_config
  const otherName = role === 'seller'
    ? sessionData?.client_config?.company_name || 'Waiting for Client...'
    : sessionData?.seller_config?.company_name || 'Seller'

  const total = clauses.length || 1
  const agreedCount = clauses.filter(c => c.status === 'agreed').length
  const inNegCount = clauses.filter(c => c.status === 'in_negotiation').length
  const agreementPct = Math.round((agreedCount / total) * 100)

  const activeClause = clauses.find(c => c.id === activeClauseId)
  const nextSpeaker = turns.length > 0
    ? (turns[turns.length - 1].speaker === 'seller_agent' ? 'client_agent' : 'seller_agent')
    : 'seller_agent'

  const handleIntervene = async (rewindToTurn: number, updatedConstraints: any[]) => {
    await api.session.intervene(params.sessionId, role, rewindToTurn, updatedConstraints)
    setIsPaused(true)
  }
  const handleResume = async () => {
    await api.session.resume(params.sessionId)
    setIsPaused(false)
    setShowIntervention(false)
  }

  // Evidence Bomb — Master session with bomb wildcard enabled, for client only, when agreement rate < 50%
  const evidenceBombEnabled = searchParams.get('bomb') === '1'
  const canUseEvidenceBomb = role === 'client' && taskId === 'master' && evidenceBombEnabled && !evidenceBombUsed
  const handleEvidenceBomb = async () => {
    setEvidenceBombLoading(true)
    try {
      await fetch(`http://localhost:7860/session/${params.sessionId}/evidence-bomb`, { method: 'POST' })
      setEvidenceBombUsed(true)
    } catch (e) {
      console.error(e)
    } finally {
      setEvidenceBombLoading(false)
    }
  }

  if (!sessionData) {
    return (
      <div className="h-screen bg-gradient-to-br from-pink-50 to-rose-50 flex items-center justify-center">
        <div className="text-center space-y-3">
          <div className="w-12 h-12 border-4 border-pink-300 border-t-pink-600 rounded-full animate-spin mx-auto" />
          <p className="text-slate-600 font-medium">Loading session...</p>
        </div>
      </div>
    )
  }

  if (isComplete || sessionData.status === 'completed') {
    return (
      <div className="h-screen bg-gradient-to-br from-emerald-50 to-teal-50 flex flex-col items-center justify-center p-8 text-center">
        <div className="w-20 h-20 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-6 shadow-lg">
          <CheckCircle2 className="w-10 h-10 text-emerald-500" />
        </div>
        <h1 className="font-bold text-4xl text-slate-800 mb-3">Negotiation Complete</h1>
        <p className="text-slate-500 mb-2 text-lg">{agreedCount}/{total} clauses agreed</p>
        <p className="text-slate-400 mb-8 max-w-md">Both AI agents have concluded negotiations. Review and sign the final agreement.</p>
        <button
          onClick={() => router.push(`/session/${params.sessionId}/sign`)}
          className="bg-gradient-to-r from-emerald-500 to-teal-500 text-white px-8 py-3 rounded-xl font-semibold shadow-lg hover:shadow-emerald-200 hover:scale-[1.02] transition-all"
        >
          Review & Sign Final Contract →
        </button>
      </div>
    )
  }

  if (sessionData.status === 'failed') {
    return (
      <div className="h-screen bg-gradient-to-br from-red-50 to-rose-50 flex flex-col items-center justify-center p-8 text-center">
        <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6 shadow-lg">
          <span className="text-4xl">🚫</span>
        </div>
        <h1 className="font-bold text-4xl text-slate-800 mb-3">Negotiation Terminated</h1>
        <p className="text-slate-500 mb-2 text-lg">The deal has collapsed.</p>
        <p className="text-slate-400 mb-8 max-w-md">One of the agents triggered a deal-breaker constraint and terminated the negotiations. The session is closed.</p>
        <button
          onClick={() => router.push(`/`)}
          className="bg-gradient-to-r from-slate-500 to-slate-700 text-white px-8 py-3 rounded-xl font-semibold shadow-lg hover:shadow-slate-200 hover:scale-[1.02] transition-all"
        >
          Return Home
        </button>
      </div>
    )
  }

  return (
    <div className="h-screen bg-slate-100 flex flex-col overflow-hidden font-sans">
      {/* Top Header Bar */}
      <div className="bg-white border-b border-slate-200 px-6 py-3 flex items-center justify-between shadow-sm flex-shrink-0">
        <div className="flex items-center gap-3">
          <FileText className="w-5 h-5 text-pink-500" />
          <div>
            <h1 className="font-bold text-slate-800 text-sm leading-none">
              {sessionData.contract_title}
            </h1>
            <p className="text-xs text-slate-400 mt-0.5">
              {me?.company_name} <span className="text-pink-400 mx-1">vs</span> {otherName}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* Agreement progress pill */}
          <div className="flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-full px-4 py-1.5">
            <div className="w-24 h-1.5 bg-slate-200 rounded-full overflow-hidden">
              <div className="h-full bg-gradient-to-r from-pink-400 to-rose-500 rounded-full transition-all duration-500"
                style={{ width: `${agreementPct}%` }} />
            </div>
            <span className="text-xs font-semibold text-slate-600">{agreedCount}/{total} agreed</span>
          </div>

          {/* Turn counter */}
          <div className="flex items-center gap-1.5 text-xs text-slate-500">
            <Clock className="w-3.5 h-3.5" />
            <span>Turn {turns.filter(t => t.speaker !== 'system').length} / {sessionData.max_turns}</span>
          </div>

          {/* Live indicator */}
          {isConnected && !isPaused && (
            <div className="flex items-center gap-1.5 bg-emerald-50 border border-emerald-200 text-emerald-600 text-xs font-bold px-3 py-1 rounded-full">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              LIVE
            </div>
          )}
          {isPaused && (
            <div className="flex items-center gap-1.5 bg-amber-50 border border-amber-200 text-amber-600 text-xs font-bold px-3 py-1 rounded-full">
              <Pause className="w-3 h-3" />
              PAUSED
            </div>
          )}
        </div>
      </div>

      {/* Main 3-panel layout */}
      <div className="flex-1 flex overflow-hidden">

        {/* ── LEFT: Clauses Panel ── */}
        <div className="w-72 bg-white border-r border-slate-200 flex flex-col flex-shrink-0">
          <div className="px-4 py-3 border-b border-slate-100">
            <p className="text-[11px] font-bold uppercase tracking-widest text-slate-400">Clauses</p>
          </div>
          <div className="flex-1 overflow-y-auto py-2 px-3 space-y-1">
            {clauses.map(c => (
              <button
                key={c.id}
                onClick={() => setActiveClauseId(c.id)}
                className={clsx(
                  'w-full text-left px-3 py-3 rounded-xl border transition-all',
                  activeClauseId === c.id
                    ? 'border-pink-300 bg-pink-50 shadow-sm'
                    : 'border-transparent hover:bg-slate-50 hover:border-slate-200'
                )}
              >
                <div className="flex items-center gap-2 mb-1">
                  <ClauseStatusDot status={c.status} />
                  <span className="text-xs font-semibold text-slate-700 truncate">{c.title}</span>
                </div>
                <div className="flex items-center gap-2 pl-4">
                  <span className={clsx(
                    'text-[10px] font-medium px-2 py-0.5 rounded-full',
                    c.status === 'agreed' ? 'bg-emerald-100 text-emerald-700'
                    : c.status === 'in_negotiation' ? 'bg-amber-100 text-amber-700'
                    : 'bg-slate-100 text-slate-500'
                  )}>
                    {c.status.replace('_', ' ')}
                  </span>
                  {c.is_deal_breaker && (
                    <span className="text-[10px] font-bold text-red-500">⚠ DB</span>
                  )}
                </div>
              </button>
            ))}
          </div>

          {/* Private Constraints */}
          <div className="border-t border-slate-100 px-4 py-3">
            <p className="text-[11px] font-bold uppercase tracking-widest text-slate-400 mb-2 flex items-center gap-1">
              <Shield className="w-3 h-3" /> Your Constraints
            </p>
            <div className="space-y-1 max-h-32 overflow-y-auto">
              {(me?.constraints || []).slice(0, 4).map((con: any, i: number) => (
                <div key={i} className="text-[11px] text-slate-600 flex items-start gap-1.5 leading-tight">
                  {con.is_deal_breaker
                    ? <span className="text-red-500 mt-0.5 flex-shrink-0">⚠</span>
                    : <span className="text-slate-300 mt-0.5 flex-shrink-0">•</span>
                  }
                  <span>{con.description}</span>
                </div>
              ))}
              {(!me?.constraints || me.constraints.length === 0) && (
                <p className="text-[11px] text-slate-400 italic">No constraints set</p>
              )}
            </div>
          </div>

          {/* Intervene button */}
          <div className="px-3 py-3 border-t border-slate-100 space-y-2">
            <button
              onClick={() => setShowIntervention(true)}
              className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-amber-500 to-orange-500 text-white px-4 py-2.5 rounded-xl font-semibold text-sm hover:from-amber-600 hover:to-orange-600 transition-all shadow-md"
            >
              {isPaused
                ? <><Play className="w-4 h-4" /> Resume / Edit</>
                : <><AlertTriangle className="w-4 h-4" /> Human Intervene</>
              }
            </button>

            {/* Evidence Bomb — Task 3 client only when losing */}
            {role === 'client' && taskId === 'task3' && (
              <button
                onClick={handleEvidenceBomb}
                disabled={!canUseEvidenceBomb || evidenceBombLoading}
                className={clsx(
                  'w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl font-semibold text-sm transition-all shadow-md',
                  canUseEvidenceBomb
                    ? 'bg-gradient-to-r from-red-600 to-rose-700 text-white hover:from-red-700 hover:to-rose-800 animate-pulse'
                    : 'bg-slate-100 text-slate-400 cursor-not-allowed'
                )}
              >
                <Bomb className="w-4 h-4" />
                {evidenceBombUsed ? 'Evidence Released ✓' : canUseEvidenceBomb ? '💣 Release Evidence Bomb' : 'Evidence Bomb (score ≥50%)'}
              </button>
            )}
          </div>
        </div>

        {/* ── CENTER: Active Clause + Chat ── */}
        <div className="flex-1 flex flex-col overflow-hidden bg-slate-50">
          {/* Active clause card */}
          {activeClause && (
            <div className="bg-white border-b border-slate-200 px-6 py-4 shadow-sm flex-shrink-0">
              <div className="flex items-start justify-between mb-2">
                <div>
                  <h2 className="font-bold text-slate-800 text-base">{activeClause.title}</h2>
                  <span className="text-[11px] text-slate-400 font-mono uppercase">{activeClause.id} · {activeClause.category}</span>
                </div>
                <div className="flex items-center gap-2">
                  {activeClause.is_deal_breaker && (
                    <span className="text-[11px] font-bold text-red-500 bg-red-50 border border-red-200 px-2 py-0.5 rounded-full">
                      ⚠ Deal-Breaker
                    </span>
                  )}
                  <span className={clsx(
                    'text-[11px] font-bold px-3 py-1 rounded-full border',
                    activeClause.status === 'agreed' ? 'bg-emerald-50 border-emerald-200 text-emerald-700'
                    : activeClause.status === 'in_negotiation' ? 'bg-amber-50 border-amber-200 text-amber-700'
                    : 'bg-slate-50 border-slate-200 text-slate-500'
                  )}>
                    {activeClause.status.replace('_', ' ').toUpperCase()}
                  </span>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3 mt-3">
                <div className="bg-slate-50 rounded-xl p-3 border border-slate-200">
                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Original</p>
                  <p className={clsx('text-xs text-slate-600 leading-relaxed', activeClause.current_proposed_text && 'line-through opacity-60')}>
                    {activeClause.text}
                  </p>
                </div>
                {activeClause.current_proposed_text ? (
                  <div className={clsx(
                    'rounded-xl p-3 border',
                    activeClause.status === 'agreed'
                      ? 'bg-emerald-50 border-emerald-200'
                      : 'bg-amber-50 border-amber-200'
                  )}>
                    <p className="text-[10px] font-bold uppercase tracking-wider mb-1 text-amber-600">
                      {activeClause.status === 'agreed' ? '✅ Agreed Text' : '📝 Proposed'}
                    </p>
                    <p className="text-xs leading-relaxed text-slate-700 font-medium">{activeClause.current_proposed_text}</p>
                  </div>
                ) : (
                  <div className="bg-slate-50 rounded-xl p-3 border border-dashed border-slate-300 flex items-center justify-center">
                    <p className="text-xs text-slate-400 italic">No proposal yet</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Chat feed */}
          <div className="flex-1 overflow-y-auto px-6 py-4">
            {turns.length === 0 && (
              <div className="flex flex-col items-center justify-center h-full space-y-3 text-slate-400">
                <Zap className="w-8 h-8 opacity-40" />
                <p className="text-sm font-medium">AI agents are warming up...</p>
                <p className="text-xs">Negotiation will begin momentarily</p>
              </div>
            )}
            {turns.map((t, i) => (
              <TurnBubble key={i} turn={t} isSeller={role === 'seller'} />
            ))}
            {!isPaused && !isComplete && turns.length > 0 && (
              <TypingDots speaker={nextSpeaker} />
            )}
            <div ref={chatBottomRef} />
          </div>

          {/* Footer status */}
          <div className="bg-white border-t border-slate-200 px-6 py-3 flex items-center justify-between flex-shrink-0">
            <p className="text-xs text-slate-400">
              {isPaused
                ? '⏸ Negotiation paused — edit constraints and resume'
                : isConnected
                ? '🤖 AI agents are negotiating automatically in real-time...'
                : '⟳ Reconnecting to live stream...'}
            </p>
            <div className="flex items-center gap-3 text-xs text-slate-400">
              <span>{inNegCount} clause{inNegCount !== 1 ? 's' : ''} in negotiation</span>
              <span>·</span>
              <span>{agreedCount} agreed</span>
            </div>
          </div>
        </div>

        {/* ── RIGHT: Stats Panel ── */}
        <div className="w-64 bg-white border-l border-slate-200 flex flex-col flex-shrink-0">
          <div className="px-4 py-3 border-b border-slate-100">
            <p className="text-[11px] font-bold uppercase tracking-widest text-slate-400">Live Analytics</p>
          </div>

          <div className="p-4 space-y-4 overflow-y-auto flex-1">
            {/* Agreement gauge */}
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-xs font-semibold text-slate-600">Agreement Rate</span>
                <span className="text-xs font-bold text-pink-600">{agreementPct}%</span>
              </div>
              <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                <div className="h-full bg-gradient-to-r from-pink-400 to-rose-500 rounded-full transition-all duration-700"
                  style={{ width: `${agreementPct}%` }} />
              </div>
            </div>

            {/* Clause breakdown */}
            <div className="space-y-2">
              {[
                { label: 'Agreed', count: agreedCount, color: 'bg-emerald-400' },
                { label: 'In Negotiation', count: inNegCount, color: 'bg-amber-400' },
                { label: 'Pending', count: clauses.filter(c => c.status === 'pending').length, color: 'bg-slate-300' },
              ].map(({ label, count, color }) => (
                <div key={label} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className={clsx('w-2.5 h-2.5 rounded-full', color)} />
                    <span className="text-xs text-slate-600">{label}</span>
                  </div>
                  <span className="text-xs font-bold text-slate-700">{count}</span>
                </div>
              ))}
            </div>

            {/* Recent agreements */}
            <div>
              <p className="text-[11px] font-bold uppercase tracking-widest text-slate-400 mb-2">Recent Agreements</p>
              <div className="space-y-1.5">
                {turns.filter(t => t.action_type === 'accept' && t.speaker === 'system').slice(-5).map((t, i) => (
                  <div key={i} className="text-xs text-emerald-700 bg-emerald-50 px-2.5 py-2 rounded-lg flex items-center gap-2 font-medium border border-emerald-100">
                    <CheckCircle2 className="w-3.5 h-3.5 flex-shrink-0" />
                    <span className="truncate">{t.content}</span>
                  </div>
                ))}
                {turns.filter(t => t.action_type === 'accept' && t.speaker === 'system').length === 0 && (
                  <p className="text-[11px] text-slate-400 italic">None yet</p>
                )}
              </div>
            </div>

            {/* Turn history mini list */}
            <div>
              <p className="text-[11px] font-bold uppercase tracking-widest text-slate-400 mb-2">Turn Log</p>
              <div className="space-y-1 max-h-48 overflow-y-auto">
                {turns.filter(t => t.speaker !== 'system').slice(-10).map((t, i) => (
                  <div key={i} className="flex items-center gap-2 text-[11px]">
                    <span className={clsx('w-5 h-5 rounded-full flex items-center justify-center text-white text-[9px] font-bold flex-shrink-0',
                      t.speaker === 'seller_agent' ? 'bg-pink-400' : 'bg-slate-600'
                    )}>
                      {t.speaker === 'seller_agent' ? 'S' : 'C'}
                    </span>
                    <span className="text-slate-500 truncate">{t.clause_id}</span>
                    <ActionBadge type={t.action_type} />
                  </div>
                ))}
                {turns.filter(t => t.speaker !== 'system').length === 0 && (
                  <p className="text-[11px] text-slate-400 italic">Waiting for first turn...</p>
                )}
              </div>
            </div>
          </div>

          {/* Session info */}
          <div className="border-t border-slate-100 px-4 py-3 space-y-1">
            <p className="text-[11px] text-slate-400">Session ID</p>
            <p className="text-[11px] font-mono text-slate-600 truncate">{params.sessionId}</p>
          </div>
        </div>
      </div>

      <InterventionModal
        isOpen={showIntervention}
        onClose={() => setShowIntervention(false)}
        role={role}
        currentTurn={turns.length}
        maxTurns={sessionData.max_turns}
        currentConstraints={me?.constraints || []}
        onIntervene={handleIntervene}
        onResume={handleResume}
        isPaused={isPaused}
      />

      <style jsx global>{`
        @keyframes bounce {
          0%, 80%, 100% { transform: translateY(0); }
          40% { transform: translateY(-6px); }
        }
      `}</style>
    </div>
  )
}
