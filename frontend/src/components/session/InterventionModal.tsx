'use client'
import React, { useState } from 'react'
import { X, AlertTriangle, RotateCcw, Play } from 'lucide-react'
import { ConstraintBuilder } from '@/components/negotiation/ConstraintBuilder'
import { ConstraintList } from '@/components/negotiation/ConstraintList'
import { Button } from '@/components/ui/Button'
import { PrivateConstraint } from '@/types'

interface InterventionModalProps {
  isOpen: boolean
  onClose: () => void
  role: string
  currentTurn: number
  maxTurns: number
  currentConstraints: PrivateConstraint[]
  onIntervene: (rewindToTurn: number, updatedConstraints: PrivateConstraint[]) => Promise<void>
  onResume: () => Promise<void>
  isPaused: boolean
}

export function InterventionModal({
  isOpen, onClose, role, currentTurn, maxTurns,
  currentConstraints, onIntervene, onResume, isPaused
}: InterventionModalProps) {
  const [constraints, setConstraints] = useState<PrivateConstraint[]>([...currentConstraints])
  const [rewindTurn, setRewindTurn] = useState(Math.max(0, currentTurn - 4))
  const [loading, setLoading] = useState(false)
  const [step, setStep] = useState<'edit' | 'done'>('edit')

  if (!isOpen) return null

  const handleIntervene = async () => {
    setLoading(true)
    try {
      await onIntervene(rewindTurn, constraints)
      setStep('done')
    } finally {
      setLoading(false)
    }
  }

  const handleResume = async () => {
    setLoading(true)
    try {
      await onResume()
      onClose()
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-charcoal/60 backdrop-blur-sm" onClick={onClose} />
      
      {/* Modal */}
      <div className="relative bg-white rounded-3xl shadow-2xl border border-pink-200 w-full max-w-2xl max-h-[90vh] overflow-y-auto mx-4">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-pink-200 px-8 py-5 rounded-t-3xl flex items-center justify-between z-10">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-amber-100 rounded-full flex items-center justify-center">
              <AlertTriangle className="w-5 h-5 text-amber-600" />
            </div>
            <div>
              <h2 className="font-display font-bold text-xl text-charcoal">Human Intervention</h2>
              <p className="text-sm text-slate">Pause, adjust constraints, and resume</p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate hover:text-charcoal transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="px-8 py-6 space-y-8">
          {step === 'edit' && (
            <>
              {/* Rewind Slider */}
              <div>
                <h3 className="font-semibold text-charcoal mb-3 flex items-center gap-2">
                  <RotateCcw className="w-4 h-4 text-pink-500" />
                  Rewind Negotiation
                </h3>
                <p className="text-sm text-slate mb-4">
                  Drag the slider to choose which turn to rewind to. All negotiation history after this turn will be discarded, and the AI agents will restart from that point with your new constraints.
                </p>
                <div className="bg-pink-50 border border-pink-200 rounded-xl p-4">
                  <div className="flex justify-between text-xs font-semibold text-slate mb-2">
                    <span>Turn 0 (Start)</span>
                    <span className="text-pink-600 font-bold">Rewind to: Turn {rewindTurn}</span>
                    <span>Turn {currentTurn} (Now)</span>
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={currentTurn}
                    value={rewindTurn}
                    onChange={e => setRewindTurn(parseInt(e.target.value))}
                    className="w-full accent-pink-500"
                  />
                  <div className="text-xs text-slate mt-2 text-center">
                    {currentTurn - rewindTurn} turn(s) of history will be discarded
                  </div>
                </div>
              </div>

              {/* Constraint Editor */}
              <div>
                <h3 className="font-semibold text-charcoal mb-3">Update Your Private Constraints</h3>
                <p className="text-sm text-slate mb-4">
                  Modify your deal-breakers and rules below. These new constraints will guide your AI agent when the negotiation resumes.
                </p>
                <ConstraintBuilder onAdd={c => setConstraints([...constraints, c])} />
                <div className="mt-6">
                  <h4 className="text-sm font-semibold text-slate mb-3">Your Current Constraints</h4>
                  <ConstraintList
                    constraints={constraints}
                    onRemove={id => setConstraints(constraints.filter(c => c.constraint_id !== id))}
                  />
                </div>
              </div>

              {/* Submit */}
              <div className="flex justify-end gap-3 pt-4 border-t border-pink-100">
                <Button variant="outline" onClick={onClose}>Cancel</Button>
                <Button onClick={handleIntervene} isLoading={loading} className="bg-amber-500 hover:bg-amber-600 text-white border-0">
                  <AlertTriangle className="w-4 h-4 mr-2" />
                  Pause &amp; Apply Changes
                </Button>
              </div>
            </>
          )}

          {step === 'done' && (
            <div className="text-center py-8">
              <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <RotateCcw className="w-8 h-8 text-emerald-600" />
              </div>
              <h3 className="font-display font-bold text-2xl text-charcoal mb-2">Intervention Applied!</h3>
              <p className="text-slate mb-2">Negotiation paused and rewound to turn {rewindTurn}.</p>
              <p className="text-sm text-slate mb-8">Your updated constraints are now loaded into your AI agent. Click below to resume the negotiation.</p>
              <Button onClick={handleResume} isLoading={loading} className="w-full max-w-xs mx-auto">
                <Play className="w-4 h-4 mr-2" />
                Resume Negotiation
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
