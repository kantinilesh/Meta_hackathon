'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Navbar } from '@/components/layout/Navbar'
import { Footer } from '@/components/layout/Footer'
import { ProgressSteps } from '@/components/ui/ProgressSteps'
import { Button } from '@/components/ui/Button'
import { ConstraintBuilder } from '@/components/negotiation/ConstraintBuilder'
import { ConstraintList } from '@/components/negotiation/ConstraintList'
import { api } from '@/lib/api'
import { PrivateConstraint } from '@/types'
import { LiveBadge } from '@/components/ui/LiveBadge'

export default function ClientJoin({ params }: { params: { token: string } }) {
  const router = useRouter()
  const [step, setStep] = useState(0)
  
  const [companyName, setCompanyName] = useState('')
  const [companyContext, setCompanyContext] = useState('')
  const [constraints, setConstraints] = useState<PrivateConstraint[]>([])
  const [agentStyle, setAgentStyle] = useState<'balanced'|'aggressive'|'cooperative'>('balanced')
  
  const [sessionInfo, setSessionInfo] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    api.session.status(undefined, params.token).then(res => {
      setSessionInfo(res.data)
    }).catch(err => {
      setError("Invalid or expired invite link.")
    })
  }, [params.token])

  const handleJoin = async () => {
    setLoading(true)
    try {
      await api.session.join({
        invite_token: params.token,
        client_company_name: companyName,
        client_constraints: constraints,
        client_agent_style: agentStyle,
        client_context: companyContext
      })
      setStep(1)
      
      // now poll for session start
      const interval = setInterval(async () => {
        try {
          const { data } = await api.session.status(undefined, params.token)
          if (data.status === 'negotiating') {
            clearInterval(interval)
            router.push(`/session/${data.session_id}?role=client`)
          }
        } catch(e) {}
      }, 3000)
    } catch(e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  if (error) {
    return <div className="min-h-screen flex items-center justify-center p-4">
      <div className="bg-white p-8 rounded-2xl border text-charcoal border-red-200 text-center text-red-500 font-medium">
        {error}
      </div>
    </div>
  }

  if (!sessionInfo) return <div className="min-h-screen flex items-center justify-center"><div className="w-8 h-8 border-4 border-pink-400 border-t-transparent animate-spin rounded-full"/></div>

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      
      <main className="flex-1 py-12 px-4 max-w-4xl mx-auto w-full">
        <ProgressSteps steps={['Set Constraints', 'Wait for Start']} currentStep={step} />
        
        {step === 0 && (
          <div className="space-y-6">
            <div className="bg-white border text-charcoal border-pink-200 rounded-2xl p-8 shadow-sm text-center">
              <h2 className="font-display font-medium text-xl text-slate mb-1">
                You've been invited to negotiate:
              </h2>
              <p className="font-display font-bold text-3xl text-charcoal">
                {sessionInfo.contract_title}
              </p>
              <p className="text-pink-500 font-medium mt-2">by {sessionInfo.seller_config?.company_name}</p>
            </div>

            <div className="bg-white border border-pink-200 rounded-2xl p-8 shadow-sm">
              <h2 className="font-display text-charcoal font-bold text-2xl mb-6">Your Private Rules</h2>
              
              <div className="mb-8 space-y-5">
                <div>
                  <label className="block text-sm font-semibold text-slate mb-2">Your Company Name</label>
                  <input value={companyName} onChange={e=>setCompanyName(e.target.value)} placeholder="Startup Inc" className="w-full bg-pink-50 border border-pink-200 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-pink-400 text-charcoal" />
                </div>
                
                <div>
                  <label className="block text-sm font-semibold text-slate mb-2">Company Context / Background Document (Optional)</label>
                  <textarea 
                    value={companyContext} 
                    onChange={e=>setCompanyContext(e.target.value)} 
                    placeholder="Paste internal notes describing your primary objectives, priorities, and what this company does..." 
                    className="w-full bg-pink-50 border border-pink-200 text-charcoal rounded-xl px-4 py-3 h-24 resize-none focus:outline-none focus:ring-2 focus:ring-pink-400"
                  />
                </div>
              </div>
              
              <ConstraintBuilder onAdd={c => setConstraints([...constraints, c])} />
              
              <div className="mt-8 border-t border-pink-100 pt-8">
                <h3 className="font-semibold text-slate mb-4">Your Added Constraints</h3>
                <ConstraintList constraints={constraints} onRemove={id => setConstraints(constraints.filter(c=>c.constraint_id !== id))} />
              </div>

              <div className="mt-8 border-t border-pink-100 pt-8">
                <h3 className="font-semibold text-slate mb-4">Agent Style</h3>
                <div className="flex gap-4">
                  {['aggressive', 'balanced', 'cooperative'].map(style => (
                    <button 
                      key={style}
                      onClick={() => setAgentStyle(style as any)}
                      className={`flex-1 py-3 rounded-xl border-2 font-medium capitalize transition-colors ${agentStyle === style ? 'border-pink-400 bg-pink-50 text-pink-600' : 'border-pink-100 text-slate hover:border-pink-200'}`}
                    >
                      {style}
                    </button>
                  ))}
                </div>
              </div>
              
              <div className="pt-8 flex justify-end">
                <Button onClick={handleJoin} disabled={!companyName} isLoading={loading}>Join & Ready &rarr;</Button>
              </div>
            </div>
          </div>
        )}

        {step === 1 && (
          <div className="bg-white border border-pink-200 rounded-2xl p-8 shadow-sm text-center text-charcoal flex flex-col items-center max-w-md mx-auto">
            <LiveBadge className="mb-6" />
            <h2 className="font-display font-bold text-2xl mb-2">Ready to negotiate</h2>
            <p className="text-slate">Waiting for {sessionInfo.seller_config?.company_name} to start the session. You will be redirected automatically.</p>
          </div>
        )}
      </main>
      <Footer />
    </div>
  )
}
