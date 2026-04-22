'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useNegotiationSocket } from '@/hooks/useNegotiationSocket'
import { api } from '@/lib/api'
import { ClauseTabBar } from '@/components/negotiation/ClauseTabBar'
import { ClauseCard } from '@/components/negotiation/ClauseCard'
import { ChatFeed } from '@/components/negotiation/ChatFeed'
import { PrivateConstraintPanel } from '@/components/negotiation/PrivateConstraintPanel'
import { ScoreMeter } from '@/components/negotiation/ScoreMeter'
import { LiveBadge } from '@/components/ui/LiveBadge'
import { Button } from '@/components/ui/Button'
import { InterventionModal } from '@/components/session/InterventionModal'
import { AlertTriangle, Pause } from 'lucide-react'

export default function SessionRoom({ params }: { params: { sessionId: string } }) {
  const router = useRouter()
  // Mock determining role for demo purposes. In prod, use auth context.
  const role = 'seller' // or client
  
  const { turns, isConnected, isComplete } = useNegotiationSocket(params.sessionId, role)
  const [sessionData, setSessionData] = useState<any>(null)
  const [activeClauseId, setActiveClauseId] = useState<string>('c1')
  const [showIntervention, setShowIntervention] = useState(false)
  const [isPaused, setIsPaused] = useState(false)

  useEffect(() => {
    // Initial fetch
    api.session.status(params.sessionId, undefined, role).then(res => {
      setSessionData(res.data)
      if (res.data.clauses?.length > 0) setActiveClauseId(res.data.clauses[0].id)
      if (res.data.status === 'paused') setIsPaused(true)
    })
  }, [params.sessionId, role])

  // Process data for UI
  const me = role === 'seller' ? sessionData?.seller_config : sessionData?.client_config
  const otherName = role === 'seller' ? 'Client' : sessionData?.seller_config?.company_name
  
  // Reconstruct clause state from turns (simulated local state update based on socket events)
  const clauses = sessionData?.clauses || []
  const clauseState = [...clauses]
  turns.forEach(t => {
    const c = clauseState.find(x => x.id === t.clause_id)
    if (c) {
      if (t.proposed_text) c.current_proposed_text = t.proposed_text
      if (t.action_type === 'accept') c.status = 'agreed'
    }
  })

  // Next speaker guess for typing indicator
  let nextSpeaker: any = 'seller_agent'
  if (turns.length > 0) {
    const last = turns[turns.length - 1].speaker
    nextSpeaker = last === 'seller_agent' ? 'client_agent' : 'seller_agent'
  }

  // derive metrics
  const total = clauses.length || 1
  const agreedCount = clauseState.filter(c => c.status === 'agreed').length
  const agreementPct = agreedCount / total

  const handleIntervene = async (rewindToTurn: number, updatedConstraints: any[]) => {
    await api.session.intervene(params.sessionId, role, rewindToTurn, updatedConstraints)
    setIsPaused(true)
  }

  const handleResume = async () => {
    await api.session.resume(params.sessionId)
    setIsPaused(false)
    setShowIntervention(false)
  }

  if (!sessionData) return <div className="h-screen bg-pink-50 flex items-center justify-center text-charcoal">Loading...</div>

  if (isComplete || sessionData.status === 'completed') {
    return (
      <div className="h-screen bg-pink-50 flex flex-col items-center justify-center p-8 text-center text-charcoal">
        <h1 className="font-display font-bold text-4xl mb-4">Negotiation Complete</h1>
        <p className="text-slate mb-8 max-w-xl">Both agents have reached an agreement on all possible clauses.</p>
        <Button onClick={() => router.push(`/session/${params.sessionId}/sign`)}>
          Review &amp; Sign Final Contract &rarr;
        </Button>
      </div>
    )
  }

  return (
    <div className="h-screen bg-pink-50 flex flex-row overflow-hidden text-charcoal">
      
      {/* LEFT PANEL */}
      <div className="w-72 bg-white border-r border-pink-200 p-5 flex flex-col flex-shrink-0">
        <div className="mb-8">
          <h2 className="font-display font-bold text-xl">{me?.company_name || 'Your Company'}</h2>
          <span className="bg-pink-100 text-pink-600 text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider">{role}</span>
        </div>
        
        <div className="flex-1 overflow-y-auto">
          <PrivateConstraintPanel constraints={me?.constraints || []} />
        </div>

        {/* HUMAN INTERVENTION BUTTON */}
        <div className="mt-4 pt-4 border-t border-pink-100">
          <button
            onClick={() => setShowIntervention(true)}
            className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-amber-500 to-orange-500 text-white px-4 py-3 rounded-xl font-semibold text-sm hover:from-amber-600 hover:to-orange-600 transition-all shadow-lg shadow-amber-200 hover:shadow-amber-300 active:scale-[0.98]"
          >
            {isPaused ? (
              <><Pause className="w-4 h-4" /> Paused — Edit Constraints</>
            ) : (
              <><AlertTriangle className="w-4 h-4" /> Intervene</>
            )}
          </button>
        </div>
        
        <div className="mt-4 pt-4 border-t border-pink-100">
          <div className="text-xs font-semibold text-slate mb-1">Turn Budget</div>
          <div className="text-sm font-mono text-pink-600 font-medium">Turn {turns.length} / {sessionData.max_turns}</div>
          <div className="h-1.5 w-full bg-pink-100 rounded-full overflow-hidden mt-2">
            <div className="h-full bg-pink-400 rounded-full" style={{width: `${(turns.length/sessionData.max_turns)*100}%`}} />
          </div>
        </div>
      </div>

      {/* CENTER PANEL */}
      <div className="flex-1 flex flex-col relative overflow-hidden bg-cream">
        <div className="px-6 py-4 bg-white/80 backdrop-blur border-b border-pink-200 flex items-center justify-between z-10">
          <h1 className="font-display text-xl font-bold">{me?.company_name} <span className="text-pink-300 font-normal italic mx-2">vs</span> {otherName}</h1>
          <div className="flex items-center gap-3">
            {isPaused && (
              <span className="bg-amber-100 text-amber-700 text-xs font-bold px-3 py-1 rounded-full animate-pulse flex items-center gap-1">
                <Pause className="w-3 h-3" /> PAUSED
              </span>
            )}
            <LiveBadge />
          </div>
        </div>
        
        <ClauseTabBar clauses={clauseState} activeId={activeClauseId} onChange={setActiveClauseId} />
        
        <div className="p-4 z-10 shadow-sm bg-cream/50 pointer-events-none">
          {clauseState.filter(c => c.id === activeClauseId).map(c => 
            <ClauseCard key={c.id} clause={c} isActive={true} />
          )}
        </div>
        
        <ChatFeed turns={turns} isComplete={isComplete} nextSpeaker={nextSpeaker} />
        
        <div className="px-6 py-4 bg-white border-t border-pink-200 text-center">
          {isPaused ? (
            <p className="text-sm text-amber-600 font-semibold">⏸️ Negotiation paused. Edit your constraints and resume.</p>
          ) : (
            <p className="text-sm text-slate animate-pulse font-medium">AI agents are negotiating automatically...</p>
          )}
        </div>
      </div>

      {/* RIGHT PANEL */}
      <div className="w-64 bg-white border-l border-pink-200 p-5 flex flex-col flex-shrink-0">
        <h3 className="text-xs font-bold tracking-widest uppercase text-pink-400 mb-6">Status Overlay</h3>
        
        <ScoreMeter label="Agreement Reached" value={agreementPct} />
        <ScoreMeter label="Seller Satisfaction" value={0.85} /> 
        <ScoreMeter label="Client Satisfaction" value={0.72} /> 
        
        <div className="mt-8">
          <h4 className="text-xs font-semibold text-slate uppercase tracking-wider mb-3">Recent Agreements</h4>
          <div className="space-y-2">
            {turns.filter(t => t.action_type === 'accept').map((t, i) => (
              <div key={i} className="text-xs text-emerald-700 bg-emerald-50 px-2 py-1.5 rounded flex items-center gap-2 font-medium">
                <span className="text-[10px]">✓</span> {t.clause_id} agreed (Turn {t.turn_number})
              </div>
            ))}
            {turns.filter(t => t.action_type === 'accept').length === 0 && (
              <div className="text-xs text-muted italic">None yet</div>
            )}
          </div>
        </div>
      </div>

      {/* INTERVENTION MODAL */}
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
    </div>
  )
}
