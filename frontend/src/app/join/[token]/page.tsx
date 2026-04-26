'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter, useSearchParams } from 'next/navigation'
import { Navbar } from '@/components/layout/Navbar'
import { Footer } from '@/components/layout/Footer'
import { ProgressSteps } from '@/components/ui/ProgressSteps'
import { Button } from '@/components/ui/Button'
import { api } from '@/lib/api'
import { Check, Shield, AlertTriangle, Globe, Bomb, Eye } from 'lucide-react'
import clsx from 'clsx'

export default function JoinSetup() {
  const params = useParams()
  const searchParams = useSearchParams()
  const router = useRouter()
  const [step, setStep] = useState(0)

  const [companyName, setCompanyName] = useState('')
  const [agentStyle, setAgentStyle] = useState<'balanced' | 'aggressive' | 'cooperative'>('balanced')
  const [constraints, setConstraints] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [sessionData, setSessionData] = useState<any>(null)
  const [sessionId, setSessionId] = useState<string>('')

  // Wildcards are passed via URL from the invite or fetched from session
  const lawsuitHidden = searchParams.get('lawsuit') === '1'
  const syriaTrap = searchParams.get('syria') === '1'
  const evidenceBomb = searchParams.get('bomb') === '1'

  useEffect(() => {
    // Fetch combined constraints for client
    const p = new URLSearchParams({
      role: 'client',
      lawsuit_hidden: lawsuitHidden.toString(),
      syria_deployment: syriaTrap.toString(),
      evidence_bomb: evidenceBomb.toString()
    })
    fetch(`http://localhost:7860/tasks/master/constraints?${p.toString()}`)
      .then(r => r.json())
      .then(data => setConstraints(data.constraints || []))
      .catch(() => setConstraints([]))
  }, [lawsuitHidden, syriaTrap, evidenceBomb])

  const handleJoin = async () => {
    setLoading(true)
    try {
      const { data } = await api.session.join({
        invite_token: params.token as string,
        client_company_name: companyName,
        client_constraints: constraints,
        client_agent_style: agentStyle,
        client_context: `Client mission for Strategic Deal.`,
      })
      setSessionId(data.session_id)
      setStep(2)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const handleEnterSession = () => {
    // Redirect to session page with same flags
    const q = new URLSearchParams({
      role: 'client',
      task: 'master',
      lawsuit: lawsuitHidden ? '1' : '0',
      syria: syriaTrap ? '1' : '0',
      bomb: evidenceBomb ? '1' : '0'
    })
    // Note: session_id is needed here, we might need to fetch it via token
    // For now, let's assume api.session.join handles the backend state.
    // We'll need the sessionId.
    router.push(`/session/${sessionId}?${q.toString()}`)
  }

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <Navbar />
      <main className="flex-1 py-12 px-4 max-w-4xl mx-auto w-full">
        <ProgressSteps steps={['Briefing', 'Agent Strategy', 'Entering Deal']} currentStep={step} />

        {step === 0 && (
          <div className="space-y-6">
            <div className="bg-white border border-pink-200 rounded-3xl p-8 shadow-sm">
              <h2 className="font-display font-bold text-2xl text-charcoal mb-4">Strategic Acquisition Briefing</h2>
              <div className="p-4 bg-pink-50 rounded-2xl border border-pink-100 mb-6">
                <p className="text-pink-800 text-sm leading-relaxed">
                  You are the Buyer/Client. You are negotiating a high-stakes acquisition and enterprise licensing deal.
                  The Seller has enabled specific <strong>High-Stakes Wildcards</strong> for this session.
                </p>
              </div>

              <div className="grid md:grid-cols-3 gap-3 mb-6">
                {lawsuitHidden && (
                  <div className="p-3 bg-rose-50 border border-rose-100 rounded-xl">
                    <div className="flex items-center gap-2 mb-1">
                      <Eye className="w-3.5 h-3.5 text-rose-500" />
                      <span className="font-bold text-[10px] text-rose-700 uppercase">Hidden Lawsuit</span>
                    </div>
                    <p className="text-[10px] text-rose-600 leading-tight">Seller may have buried liabilities. Check Data Room.</p>
                  </div>
                )}
                {syriaTrap && (
                  <div className="p-3 bg-amber-50 border border-amber-100 rounded-xl">
                    <div className="flex items-center gap-2 mb-1">
                      <Globe className="w-3.5 h-3.5 text-amber-500" />
                      <span className="font-bold text-[10px] text-amber-700 uppercase">Syria Reveal</span>
                    </div>
                    <p className="text-[10px] text-amber-600 leading-tight">You plan to deploy to Syria. Reveal at Turn 2.</p>
                  </div>
                )}
                {evidenceBomb && (
                  <div className="p-3 bg-orange-50 border border-orange-100 rounded-xl">
                    <div className="flex items-center gap-2 mb-1">
                      <Bomb className="w-3.5 h-3.5 text-orange-500" />
                      <span className="font-bold text-[10px] text-orange-700 uppercase">Evidence Bomb</span>
                    </div>
                    <p className="text-[10px] text-orange-600 leading-tight">You can release forensic logs if agreement stalls.</p>
                  </div>
                )}
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-semibold text-slate mb-2">Your Company Name (Buyer)</label>
                  <input
                    value={companyName}
                    onChange={e => setCompanyName(e.target.value)}
                    placeholder="e.g. MetaGlobal Industries"
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-pink-400 text-charcoal"
                  />
                </div>
              </div>
            </div>

            <div className="pt-2 flex justify-end">
              <Button onClick={() => setStep(1)} disabled={!companyName}>Configure Agent Style →</Button>
            </div>
          </div>
        )}

        {step === 1 && (
          <div className="bg-white border border-pink-200 rounded-3xl p-8 shadow-sm space-y-8">
            <div>
              <h2 className="font-display font-bold text-2xl text-charcoal mb-1">Agent Strategy</h2>
              <p className="text-sm text-slate-500">Align your AI agent with your acquisition goals.</p>
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

            <div>
              <div className="flex items-center gap-2 mb-3">
                <Shield className="w-4 h-4 text-pink-400" />
                <h3 className="font-semibold text-slate text-sm">Active Directives</h3>
              </div>
              <div className="space-y-2">
                {constraints.map((c: any, i: number) => (
                  <div key={i} className={clsx(
                    'flex items-start gap-3 p-3 rounded-xl border text-[11px]',
                    c.is_deal_breaker ? 'bg-red-50 border-red-100 text-red-800' : 'bg-slate-50 border-slate-100 text-slate-700'
                  )}>
                    {c.is_deal_breaker ? <AlertTriangle className="w-3.5 h-3.5 text-red-500 flex-shrink-0" /> : <Check className="w-3.5 h-3.5 text-emerald-500 flex-shrink-0" />}
                    <span>{c.description}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex justify-between pt-2">
              <Button variant="outline" onClick={() => setStep(0)}>Back</Button>
              <Button onClick={handleJoin} isLoading={loading}>Join Negotiation →</Button>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="bg-white border border-pink-200 rounded-3xl p-10 shadow-sm text-center max-w-sm mx-auto">
            <div className="w-16 h-16 bg-emerald-100 text-emerald-500 rounded-full flex items-center justify-center mx-auto mb-6 shadow-inner">
              <Check className="w-8 h-8" />
            </div>
            <h2 className="font-display font-bold text-2xl mb-2 text-charcoal">All Set!</h2>
            <p className="text-slate text-sm mb-8">The Seller has been notified. You are now entering the boardroom.</p>
            <Button onClick={handleEnterSession} className="w-full">
              Enter Deal Room →
            </Button>
          </div>
        )}
      </main>
      <Footer />
    </div>
  )
}
