'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Navbar } from '@/components/layout/Navbar'
import { Footer } from '@/components/layout/Footer'
import { ProgressSteps } from '@/components/ui/ProgressSteps'
import { Button } from '@/components/ui/Button'
import { ConstraintBuilder } from '@/components/negotiation/ConstraintBuilder'
import { ConstraintList } from '@/components/negotiation/ConstraintList'
import { DocumentUploader } from '@/components/negotiation/DocumentUploader'
import { InviteCard } from '@/components/session/InviteCard'
import { WaitingRoom } from '@/components/session/WaitingRoom'
import { api } from '@/lib/api'
import { PrivateConstraint, CompanyDocument } from '@/types'
import { Check } from 'lucide-react'

export default function NegotiateSetup() {
  const router = useRouter()
  const [step, setStep] = useState(0)
  
  const [companyName, setCompanyName] = useState('')
  const [contractText, setContractText] = useState('')
  const [companyContext, setCompanyContext] = useState('')
  const [constraints, setConstraints] = useState<PrivateConstraint[]>([])
  const [agentStyle, setAgentStyle] = useState<'balanced'|'aggressive'|'cooperative'>('balanced')
  const [documents, setDocuments] = useState<CompanyDocument[]>([])
  
  const [sessionInfo, setSessionInfo] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const handleNext1 = () => {
    if (companyName) setStep(1)
  }

  const handleCreateSession = async () => {
    setLoading(true)
    try {
      const { data } = await api.session.create({
        contract_id: 'nda_001',
        seller_company_name: companyName,
        seller_constraints: constraints,
        seller_agent_style: agentStyle,
        seller_context: companyContext
      })
      setSessionInfo(data)
      setStep(2)
    } catch(e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const handleLinkDocuments = async () => {
    if (documents.length > 0 && sessionInfo?.session_id) {
      try {
        await api.document.link(sessionInfo.session_id, 'seller', documents.map(d => d.document_id))
      } catch(e) {
        console.error('Failed to link documents:', e)
      }
    }
  }

  const handleStart = async () => {
    setLoading(true)
    try {
      await api.session.start(sessionInfo.session_id)
      router.push(`/session/${sessionInfo.session_id}`)
    } catch(e) {
      console.error(e)
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      
      <main className="flex-1 py-12 px-4 max-w-4xl mx-auto w-full">
        <ProgressSteps steps={['Upload Contract', 'Your Rules', 'Invite Client']} currentStep={step} />
        
        {step === 0 && (
          <div className="bg-white border border-pink-200 rounded-2xl p-8 shadow-sm">
            <h2 className="font-display font-bold text-2xl mb-6 text-charcoal">Upload Your Contract</h2>
            
            <div className="space-y-5">
              <div>
                <label className="block text-sm font-semibold text-slate mb-2">Company Name (Seller)</label>
                <input value={companyName} onChange={e=>setCompanyName(e.target.value)} placeholder="Acme Corp" className="w-full bg-pink-50 border border-pink-200 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-pink-400 text-charcoal" />
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

              <div>
                <label className="block text-sm font-semibold text-slate mb-2">Contract Text</label>
                <textarea 
                  value={contractText} 
                  onChange={e=>setContractText(e.target.value)} 
                  placeholder="Paste your standard agreement here..." 
                  className="w-full bg-pink-50 border border-pink-200 text-charcoal rounded-xl px-4 py-3 h-48 resize-none focus:outline-none focus:ring-2 focus:ring-pink-400"
                />
                <button 
                  onClick={() => setContractText("DEMO: Standard NDA with 6 clauses selected automatically across duration, non-compete, IP, liability, etc.")}
                  className="mt-2 text-sm text-pink-500 hover:text-pink-600 font-medium"
                >
                  Use Demo NDA &rarr;
                </button>
              </div>
              
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
                Your Private Rules & Documents
              </h2>
              <p className="text-pink-500 text-sm italic font-medium mt-2">
                These are never shown to the other party. Your AI agent uses them to negotiate.
              </p>
            </div>
            
            <div className="mb-8">
              <h3 className="font-semibold text-slate mb-4">Prerequisite Documents (Optional)</h3>
              <p className="text-sm text-slate mb-4">
                Upload financials, bylaws, due diligence reports, cap tables, etc. The AI will use these to inform negotiations on amount, payment, equity distribution, and other deal terms.
              </p>
              <DocumentUploader 
                sessionId={sessionInfo?.session_id || ''}
                documents={documents}
                onDocumentsChange={setDocuments}
              />
            </div>

            <div className="border-t border-pink-100 pt-8">
              <h3 className="font-semibold text-slate mb-4">Private Constraints</h3>
              <ConstraintBuilder onAdd={c => setConstraints([...constraints, c])} />
            </div>
            
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
              <Button onClick={handleCreateSession} isLoading={loading}>Generate Invite Link &rarr;</Button>
            </div>
          </div>
        )}

        {step === 2 && sessionInfo && (
          <div className="space-y-8">
            <div className="bg-white border border-pink-200 rounded-2xl p-8 shadow-sm">
              <h2 className="font-display font-bold text-2xl mb-6 text-charcoal">Upload Documents</h2>
              <p className="text-slate mb-6">
                Optionally upload prerequisite documents now. These will be used by both parties during negotiation.
              </p>
              <DocumentUploader 
                sessionId={sessionInfo.session_id}
                documents={documents}
                onDocumentsChange={setDocuments}
              />
              <div className="mt-6 flex justify-end">
                <Button onClick={handleLinkDocuments}>
                  Save Documents &rarr;
                </Button>
              </div>
            </div>
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
