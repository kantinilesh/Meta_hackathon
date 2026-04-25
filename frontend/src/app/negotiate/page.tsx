'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Navbar } from '@/components/layout/Navbar'
import { Footer } from '@/components/layout/Footer'
import { ProgressSteps } from '@/components/ui/ProgressSteps'
import { Button } from '@/components/ui/Button'
import { ConstraintBuilder } from '@/components/negotiation/ConstraintBuilder'
import { ConstraintList } from '@/components/negotiation/ConstraintList'
import { InviteCard } from '@/components/session/InviteCard'
import { WaitingRoom } from '@/components/session/WaitingRoom'
import { api } from '@/lib/api'
import { PrivateConstraint } from '@/types'
import { Check, UploadCloud, FileText, Download } from 'lucide-react'
import clsx from 'clsx'

export default function NegotiateSetup() {
  const router = useRouter()
  const [step, setStep] = useState(0)
  
  const [companyName, setCompanyName] = useState('')
  const [contractId, setContractId] = useState('task3') // backend mapped
  const [hasUploadedContract, setHasUploadedContract] = useState(false)
  const [constraints, setConstraints] = useState<PrivateConstraint[]>([])
  const [agentStyle, setAgentStyle] = useState<'balanced'|'aggressive'|'cooperative'>('balanced')
  
  const [sessionInfo, setSessionInfo] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const handleNext1 = () => {
    if (companyName) setStep(1)
  }

  const handleCreateSession = async () => {
    setLoading(true)
    try {
      const { data } = await api.session.create({
        contract_id: contractId,
        seller_company_name: companyName,
        // If they uploaded the contract, they don't need constraints (they defend it as-is)
        seller_constraints: hasUploadedContract ? [] : constraints,
        seller_agent_style: agentStyle,
        seller_context: ""
      })
      setSessionInfo(data)
      setStep(2)
    } catch(e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const handleStart = async () => {
    setLoading(true)
    try {
      await api.session.start(sessionInfo.session_id)
      router.push(`/session/${sessionInfo.session_id}?role=seller`)
    } catch(e) {
      console.error(e)
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <Navbar />
      
      <main className="flex-1 py-12 px-4 max-w-4xl mx-auto w-full">
        <ProgressSteps steps={['Upload Agreement', 'Your Strategy', 'Invite Client']} currentStep={step} />
        
        {step === 0 && (
          <div className="bg-white border border-pink-200 rounded-2xl p-8 shadow-sm">
            <h2 className="font-display font-bold text-2xl mb-6 text-charcoal">Establish the Base Agreement</h2>
            
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-semibold text-slate mb-2">Your Company Name (Seller)</label>
                <input value={companyName} onChange={e=>setCompanyName(e.target.value)} placeholder="Acme Corp" className="w-full bg-pink-50 border border-pink-200 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-pink-400 text-charcoal" />
              </div>
              
              <div>
                <label className="block text-sm font-semibold text-slate mb-3">Provide Base Agreement</label>
                <div className="border border-pink-200 rounded-xl p-6 bg-pink-50/50">
                  <div className="grid md:grid-cols-2 gap-4">
                    {/* Upload Custom Agreement */}
                    <div>
                      <input 
                        type="file" 
                        id="contract-upload" 
                        className="hidden" 
                        accept=".pdf,.doc,.docx,.txt" 
                        onChange={(e) => {
                          if (e.target.files && e.target.files[0]) {
                            setHasUploadedContract(true)
                            setContractId('task3')
                            const el = document.getElementById('uploaded-filename');
                            if (el) el.innerText = 'Uploaded: ' + e.target.files[0].name;
                          }
                        }} 
                      />
                      <label 
                        htmlFor="contract-upload"
                        className="border-2 border-slate-200 bg-white hover:border-emerald-300 rounded-xl p-6 flex flex-col items-center justify-center cursor-pointer transition-all text-center h-full"
                      >
                        <UploadCloud className="w-8 h-8 mb-2 text-slate-400" />
                        <p className="font-bold text-sm text-slate-700">Upload Custom PDF</p>
                        <p className="text-xs text-slate-500 mt-1">Upload your own drafted agreement.</p>
                      </label>
                    </div>

                    {/* Use Random Demo */}
                    <div 
                      onClick={() => {
                        setHasUploadedContract(true)
                        const randomTask = Math.random() > 0.5 ? 'task2' : 'task3';
                        setContractId(randomTask)
                        const el = document.getElementById('uploaded-filename');
                        if (el) el.innerText = 'Selected: ' + (randomTask === 'task2' ? 'Demo_SaaS_Agreement.pdf' : 'Demo_NDA_Agreement.pdf');
                      }}
                      className="border-2 border-slate-200 bg-white hover:border-pink-300 rounded-xl p-6 flex flex-col items-center justify-center cursor-pointer transition-all text-center h-full"
                    >
                      <FileText className="w-8 h-8 mb-2 text-slate-400" />
                      <p className="font-bold text-sm text-slate-700">Use Random Demo</p>
                      <p className="text-xs text-slate-500 mt-1">Automatically use a sample NDA or SaaS.</p>
                    </div>
                  </div>
                  
                  <div className="mt-6 bg-white p-3 rounded-lg border border-slate-200 shadow-sm flex items-center justify-between">
                    <p id="uploaded-filename" className="text-sm font-semibold text-slate-600 ml-2">
                      {hasUploadedContract ? "Agreement ready." : "No agreement selected yet."}
                    </p>
                    {hasUploadedContract && (
                      <button 
                        onClick={(e) => {
                          e.stopPropagation()
                          setHasUploadedContract(false)
                          setContractId('task3')
                          // Optional: Clear the file input value
                          const fileInput = document.getElementById('contract-upload') as HTMLInputElement
                          if (fileInput) fileInput.value = ''
                        }}
                        className="text-xs bg-red-50 text-red-600 hover:bg-red-100 px-3 py-1.5 rounded-md font-medium transition-colors"
                      >
                        Clear Selection
                      </button>
                    )}
                  </div>
                </div>
              </div>

              {!hasUploadedContract && (
                <div className="border-t border-pink-100 pt-8">
                  <h3 className="font-semibold text-slate mb-4">Basic Constraints</h3>
                  <ConstraintBuilder onAdd={c => setConstraints([...constraints, c])} />
                  {constraints.length > 0 && (
                    <div className="mt-6">
                      <h3 className="font-semibold text-slate mb-4">Your Added Constraints</h3>
                      <ConstraintList constraints={constraints} onRemove={id => setConstraints(constraints.filter(c=>c.constraint_id !== id))} />
                    </div>
                  )}
                </div>
              )}
              
              <div className="pt-4 flex justify-end">
                <Button onClick={handleNext1} disabled={!companyName}>Next &rarr;</Button>
              </div>
            </div>
          </div>
        )}

        {step === 1 && (
          <div className="bg-white border border-pink-200 rounded-2xl p-8 shadow-sm">
            <div className="mb-6">
              <h2 className="font-display font-bold text-2xl text-charcoal flex items-center gap-2">
                Your Agent's Strategy
              </h2>
            </div>

            <div className="border-t border-pink-100 pt-8">
              <h3 className="font-semibold text-slate mb-4">Agent Style</h3>
              <p className="text-sm text-slate-500 mb-4">How aggressively should your agent defend the base agreement?</p>
              <div className="flex gap-4">
                {['aggressive', 'balanced', 'cooperative'].map(style => (
                  <button 
                    key={style}
                    onClick={() => setAgentStyle(style as any)}
                    className={`flex-1 py-3 rounded-xl border-2 font-medium capitalize transition-colors ${agentStyle === style ? 'border-pink-400 bg-pink-50 text-pink-600 shadow-sm' : 'border-slate-200 text-slate hover:border-pink-200'}`}
                  >
                    {style}
                  </button>
                ))}
              </div>
            </div>
            
            <div className="pt-8 flex justify-end gap-3">
              <Button variant="outline" onClick={() => setStep(0)}>Back</Button>
              <Button onClick={handleCreateSession} isLoading={loading}>Generate Invite Link &rarr;</Button>
            </div>
          </div>
        )}

        {step === 2 && sessionInfo && (
          <div className="space-y-8">
            <InviteCard inviteUrl={sessionInfo.invite_url} />
            <WaitingRoom sessionId={sessionInfo.session_id} onReady={() => setStep(3)} />
          </div>
        )}

        {step === 3 && sessionInfo && (
          <div className="bg-white border border-pink-200 rounded-2xl p-8 shadow-sm text-center max-w-sm mx-auto">
            <div className="w-16 h-16 bg-emerald-100 text-emerald-500 rounded-full flex items-center justify-center mx-auto mb-6">
              <Check className="w-8 h-8" />
            </div>
            <h2 className="font-display font-bold text-2xl mb-2 text-charcoal">Client Joined!</h2>
            <p className="text-slate mb-8">Both parties are ready. Click below to begin the live negotiation.</p>
            <Button onClick={handleStart} isLoading={loading} className="w-full">
              Start Negotiation &rarr;
            </Button>
          </div>
        )}

      </main>
      
      <Footer />
    </div>
  )
}
