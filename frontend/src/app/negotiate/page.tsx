'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Navbar } from '@/components/layout/Navbar'
import { Footer } from '@/components/layout/Footer'
import { ProgressSteps } from '@/components/ui/ProgressSteps'
import { Button } from '@/components/ui/Button'
import { InviteCard } from '@/components/session/InviteCard'
import { WaitingRoom } from '@/components/session/WaitingRoom'
import { api } from '@/lib/api'
import { Check, Shield, AlertTriangle, EyeOff, Eye, Globe, Bomb, Plus, Trash2 } from 'lucide-react'
import clsx from 'clsx'

const DEAL_META = {
  title: 'Strategic Acquisition & Enterprise Partnership',
  subtitle: 'A complex, multi-layered deal with high-stakes variables.',
  description: 'This negotiation covers acquisition valuation, global software licensing, and past liability settlements. You can choose to include specific "Wildcard" mechanics to increase the stakes.',
}

export default function NegotiateSetup() {
  const router = useRouter()
  const [step, setStep] = useState(0)

  const [companyName, setCompanyName] = useState('')
  const [agentStyle, setAgentStyle] = useState<'balanced' | 'aggressive' | 'cooperative'>('balanced')
  
  // Wildcard Toggles
  const [lawsuitHidden, setLawsuitHidden] = useState(false)
  const [syriaTrap, setSyriaTrap] = useState(false)
  const [evidenceBomb, setEvidenceBomb] = useState(false)
  
  const [constraints, setConstraints] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [sessionInfo, setSessionInfo] = useState<any>(null)
  
  const [newConstraint, setNewConstraint] = useState('')

  // Load Combined Constraints when toggles change
  useEffect(() => {
    const params = new URLSearchParams({
      role: 'seller',
      lawsuit_hidden: lawsuitHidden.toString(),
      syria_deployment: syriaTrap.toString(),
      evidence_bomb: evidenceBomb.toString()
    })
    fetch(`http://localhost:7860/tasks/master/constraints?${params.toString()}`)
      .then(r => r.json())
      .then(data => {
        if (data.constraints) {
           setConstraints(data.constraints)
        }
      })
      .catch((e) => {
        console.error("Failed to fetch constraints:", e)
        setConstraints([])
      })
  }, [lawsuitHidden, syriaTrap, evidenceBomb])

  const handleAddConstraint = () => {
    if (!newConstraint.trim()) return
    setConstraints([
      ...constraints,
      {
        constraint_id: `custom_${Date.now()}`,
        description: newConstraint,
        clause_category: 'custom',
        is_deal_breaker: false,
        priority: 5
      }
    ])
    setNewConstraint('')
  }

  const handleRemoveConstraint = (id: string) => {
    setConstraints(constraints.filter(c => c.constraint_id !== id))
  }

  const handleToggleDealBreaker = (id: string) => {
    setConstraints(constraints.map(c => 
      c.constraint_id === id ? { ...c, is_deal_breaker: !c.is_deal_breaker } : c
    ))
  }

  const handleCreateSession = async () => {
    setLoading(true)
    try {
      // Pass the flags to the backend
      const { data } = await api.session.create({
        contract_id: 'master',
        seller_company_name: companyName,
        seller_constraints: constraints,
        seller_agent_style: agentStyle,
        seller_context: `Strategic Deal. Wildcards: ${lawsuitHidden ? 'Hidden Lawsuit, ' : ''}${syriaTrap ? 'Syria Trap, ' : ''}${evidenceBomb ? 'Evidence Bomb' : ''}`,
        lawsuit_hidden: lawsuitHidden,
        syria_deployment: syriaTrap,
        evidence_bomb_enabled: evidenceBomb
      })
      setSessionInfo({ ...data, lawsuitHidden, syriaTrap, evidenceBomb })
      setStep(3)
    } catch (e) {
      console.error("Session creation failed:", e)
      alert("Failed to create session. Is the backend running at port 7860?")
    } finally {
      setLoading(false)
    }
  }

  const handleStart = async () => {
    setLoading(true)
    try {
      await api.session.start(sessionInfo.session_id)
      const params = new URLSearchParams({
        role: 'seller',
        task: 'master',
        lawsuit: lawsuitHidden ? '1' : '0',
        syria: syriaTrap ? '1' : '0',
        bomb: evidenceBomb ? '1' : '0'
      })
      router.push(`/session/${sessionInfo.session_id}?${params.toString()}`)
    } catch (e) {
      console.error(e)
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-charcoal">
      <Navbar />

      <main className="flex-1 py-12 px-4 max-w-4xl mx-auto w-full">
        <ProgressSteps steps={['Deal Setup', 'Agent Strategy', 'Invite Client']} currentStep={step} />

        {/* STEP 0 — Basic Setup */}
        {step === 0 && (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="bg-white border border-pink-200 rounded-3xl p-8 shadow-sm">
              <div className="flex items-center gap-4 mb-4">
                <div className="w-12 h-12 bg-pink-100 rounded-2xl flex items-center justify-center text-2xl">🤝</div>
                <div>
                  <h2 className="font-display font-bold text-2xl text-charcoal">{DEAL_META.title}</h2>
                  <p className="text-slate-500 text-sm">{DEAL_META.subtitle}</p>
                </div>
              </div>
              <p className="text-slate-600 text-sm leading-relaxed mb-6">{DEAL_META.description}</p>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-semibold text-slate mb-2">Your Company Name (Seller)</label>
                  <input
                    value={companyName}
                    onChange={e => setCompanyName(e.target.value)}
                    placeholder="e.g. Nexus Systems"
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-pink-400 text-charcoal placeholder:text-slate-400"
                  />
                </div>
              </div>
            </div>

            {/* Wildcard Selection */}
            <div className="grid md:grid-cols-3 gap-4">
              <button
                onClick={() => setLawsuitHidden(!lawsuitHidden)}
                className={clsx(
                  'text-left p-5 rounded-2xl border-2 transition-all group relative overflow-hidden',
                  lawsuitHidden ? 'border-rose-400 bg-rose-50 shadow-md' : 'border-slate-200 bg-white hover:border-rose-200'
                )}
              >
                <div className="flex justify-between items-start mb-3">
                  <div className="text-2xl">🦴</div>
                  {lawsuitHidden && <Check className="w-5 h-5 text-rose-500" />}
                </div>
                <div className="font-bold text-charcoal text-sm mb-1">Hidden Lawsuit</div>
                <div className="text-[10px] text-slate-500 leading-tight">Buries a $2.5M liability in the Data Room under vague filenames.</div>
              </button>

              <button
                onClick={() => setSyriaTrap(!syriaTrap)}
                className={clsx(
                  'text-left p-5 rounded-2xl border-2 transition-all group relative overflow-hidden',
                  syriaTrap ? 'border-amber-400 bg-amber-50 shadow-md' : 'border-slate-200 bg-white hover:border-amber-200'
                )}
              >
                <div className="flex justify-between items-start mb-3">
                  <div className="text-2xl">⚖️</div>
                  {syriaTrap && <Check className="w-5 h-5 text-amber-500" />}
                </div>
                <div className="font-bold text-charcoal text-sm mb-1">Syria Compliance Trap</div>
                <div className="text-[10px] text-slate-500 leading-tight">Client reveals a sanctioned deployment. Your agent MUST terminate.</div>
              </button>

              <button
                onClick={() => setEvidenceBomb(!evidenceBomb)}
                className={clsx(
                  'text-left p-5 rounded-2xl border-2 transition-all group relative overflow-hidden',
                  evidenceBomb ? 'border-orange-400 bg-orange-50 shadow-md' : 'border-slate-200 bg-white hover:border-orange-200'
                )}
              >
                <div className="flex justify-between items-start mb-3">
                  <div className="text-2xl">💣</div>
                  {evidenceBomb && <Check className="w-5 h-5 text-orange-500" />}
                </div>
                <div className="font-bold text-charcoal text-sm mb-1">Evidence Bomb</div>
                <div className="text-[10px] text-slate-500 leading-tight">Enables regulator to release forensic logs mid-negotiation.</div>
              </button>
            </div>

            <div className="pt-2 flex justify-end">
              <Button onClick={() => setStep(1)} disabled={!companyName}>Configure Agent Strategy →</Button>
            </div>
          </div>
        )}

        {/* STEP 1 — Strategy */}
        {step === 1 && (
          <div className="bg-white border border-pink-200 rounded-3xl p-8 shadow-sm space-y-8 animate-in fade-in slide-in-from-right-4 duration-500">
            <div>
              <h2 className="font-display font-bold text-2xl text-charcoal mb-1">Agent Strategy</h2>
              <p className="text-sm text-slate-500">Customize how your AI agent should handle the negotiation landmines.</p>
            </div>

            <div>
              <h3 className="font-semibold text-slate mb-3 text-sm">Negotiation Temperament</h3>
              <div className="flex gap-3">
                {(['aggressive', 'balanced', 'cooperative'] as const).map(style => (
                  <button
                    key={style}
                    onClick={() => setAgentStyle(style)}
                    className={clsx(
                      'flex-1 py-3 rounded-xl border-2 font-medium capitalize transition-colors text-xs',
                      agentStyle === style
                        ? 'border-pink-400 bg-pink-50 text-pink-600 shadow-sm'
                        : 'border-slate-100 text-slate hover:border-pink-200'
                    )}
                  >
                    {style}
                  </button>
                ))}
              </div>
            </div>

            {/* Constraints Customizer */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Shield className="w-4 h-4 text-pink-400" />
                  <h3 className="font-semibold text-slate text-sm">Agent Directives</h3>
                </div>
                <span className="text-[10px] text-slate-400 font-medium">{constraints.length} Active</span>
              </div>
              
              <div className="space-y-2 max-h-[300px] overflow-y-auto pr-2 custom-scrollbar">
                {constraints.map((c: any) => (
                  <div key={c.constraint_id} className={clsx(
                    'group flex items-start gap-3 p-4 rounded-2xl border transition-all',
                    c.is_deal_breaker ? 'bg-red-50/50 border-red-100' : 'bg-slate-50/50 border-slate-100'
                  )}>
                    <button 
                      onClick={() => handleToggleDealBreaker(c.constraint_id)}
                      className={clsx(
                        'mt-0.5 p-1 rounded-md transition-colors',
                        c.is_deal_breaker ? 'bg-red-100 text-red-600' : 'bg-slate-200 text-slate-400 hover:bg-red-100 hover:text-red-600'
                      )}
                      title="Toggle Deal Breaker"
                    >
                      <AlertTriangle className="w-3.5 h-3.5" />
                    </button>
                    <div className="flex-1">
                      <p className={clsx('text-[11px] leading-relaxed font-medium', c.is_deal_breaker ? 'text-red-900' : 'text-slate-700')}>
                        {c.description}
                      </p>
                    </div>
                    <button 
                      onClick={() => handleRemoveConstraint(c.constraint_id)}
                      className="opacity-0 group-hover:opacity-100 p-1 text-slate-300 hover:text-red-500 transition-all"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
              </div>

              <div className="flex gap-2">
                <input 
                  value={newConstraint}
                  onChange={e => setNewConstraint(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleAddConstraint()}
                  placeholder="Add a custom directive..."
                  className="flex-1 bg-white border border-slate-200 rounded-xl px-4 py-2 text-[11px] focus:outline-none focus:ring-2 focus:ring-pink-400"
                />
                <button 
                  onClick={handleAddConstraint}
                  className="bg-pink-500 text-white p-2 rounded-xl hover:bg-pink-600 transition-colors"
                >
                  <Plus className="w-4 h-4" />
                </button>
              </div>
            </div>

            <div className="flex justify-between pt-2">
              <Button variant="outline" onClick={() => setStep(0)}>Back</Button>
              <Button onClick={() => setStep(2)}>Review & Invite →</Button>
            </div>
          </div>
        )}

        {/* STEP 2 — Final Review */}
        {step === 2 && (
          <div className="bg-white border border-pink-200 rounded-3xl p-10 shadow-sm text-center space-y-6 animate-in zoom-in duration-500">
            <div className="w-20 h-20 bg-pink-50 rounded-full flex items-center justify-center mx-auto text-4xl shadow-inner border border-pink-100">🏁</div>
            <h2 className="font-display font-bold text-2xl text-charcoal">Deal is Ready</h2>
            <div className="flex justify-center gap-2">
              {lawsuitHidden && <span className="bg-rose-100 text-rose-600 px-3 py-1 rounded-full text-[10px] font-bold border border-rose-200">LAWSUIT</span>}
              {syriaTrap && <span className="bg-amber-100 text-amber-600 px-3 py-1 rounded-full text-[10px] font-bold border border-amber-200">SYRIA TRAP</span>}
              {evidenceBomb && <span className="bg-orange-100 text-orange-600 px-3 py-1 rounded-full text-[10px] font-bold border border-orange-200">EVIDENCE BOMB</span>}
            </div>
            <p className="text-slate-500 text-sm max-w-sm mx-auto">
              Your agent is briefed on the <strong>{constraints.length} directives</strong> and ready to handle the high-stakes wildcards.
            </p>
            <div className="flex justify-center gap-3 pt-4">
              <Button variant="outline" onClick={() => setStep(1)}>Back</Button>
              <Button onClick={handleCreateSession} isLoading={loading}>Generate Invite Link →</Button>
            </div>
          </div>
        )}

        {/* STEP 3 — Invite Card */}
        {step === 3 && sessionInfo && (
          <div className="space-y-8 animate-in fade-in duration-500">
            <InviteCard inviteUrl={sessionInfo.invite_url} />
            <WaitingRoom sessionId={sessionInfo.session_id} onReady={() => setStep(4)} />
          </div>
        )}

        {/* STEP 4 — Start Negotiation */}
        {step === 4 && sessionInfo && (
          <div className="bg-white border border-pink-200 rounded-3xl p-10 shadow-sm text-center max-w-sm mx-auto animate-bounce-in">
            <div className="w-16 h-16 bg-emerald-100 text-emerald-500 rounded-full flex items-center justify-center mx-auto mb-6 shadow-inner">
              <Check className="w-8 h-8" />
            </div>
            <h2 className="font-display font-bold text-2xl mb-2 text-charcoal">Client Joined!</h2>
            <p className="text-slate text-sm mb-8">Both parties are ready for the multi-layered negotiation.</p>
            <Button onClick={handleStart} isLoading={loading} className="w-full">
              Start Negotiation →
            </Button>
          </div>
        )}
      </main>

      <Footer />
    </div>
  )
}
