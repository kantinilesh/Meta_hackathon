'use client'

import { X, RotateCcw, ChevronRight, BarChart3 } from 'lucide-react'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { ScoreBar } from '@/components/ui/ScoreBar'
import type { GradeResult } from '@/types'

interface GradeModalProps {
  result: GradeResult
  targetScore: number
  onClose: () => void
  onRunAgain: () => void
  onNextTask: () => void
  onViewScores: () => void
}

export default function GradeModal({
  result,
  targetScore,
  onClose,
  onRunAgain,
  onNextTask,
  onViewScores,
}: GradeModalProps) {
  const scoreColor = result.passed
    ? 'text-emerald-400'
    : result.score >= targetScore * 0.8
      ? 'text-amber-400'
      : 'text-red-400'

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-lg bg-card rounded-2xl border border-border shadow-2xl overflow-hidden">
        {/* ── Header ── */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <div className="flex items-center gap-3">
            <h2 className="text-base font-semibold text-text-primary">Episode Complete</h2>
            <Badge variant={
              result.task_id === 'task1' ? 'easy' : result.task_id === 'task2' ? 'medium' : 'hard'
            }>
              {result.task_id}
            </Badge>
          </div>
          <button onClick={onClose} className="text-text-muted hover:text-text-primary transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* ── Score Display ── */}
        <div className="px-6 py-6 text-center border-b border-border">
          <p className={`text-6xl font-mono font-bold ${scoreColor}`}>
            {result.score.toFixed(2)}
          </p>
          <p className="text-text-muted text-sm mt-1">/ 1.00</p>
          <div className="mt-3">
            <Badge variant={result.passed ? 'success' as any : 'danger' as any}>
              {result.passed ? '✓ PASSED' : '✗ FAILED'}
            </Badge>
          </div>
          <p className="text-xs text-text-muted mt-2">Target: {targetScore.toFixed(2)}</p>
          <div className="mt-4 max-w-xs mx-auto">
            <ScoreBar value={result.score} targetScore={targetScore} />
          </div>
        </div>

        {/* ── Breakdown ── */}
        <div className="px-6 py-4 max-h-48 overflow-y-auto border-b border-border">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-text-muted mb-2">Breakdown</p>
          <div className="space-y-1.5">
            {Object.entries(result.breakdown).map(([key, val]) => (
              <div key={key} className="flex items-center justify-between text-xs">
                <span className="text-text-secondary">{key.replace(/_/g, ' ')}</span>
                <span className="font-mono text-text-primary">
                  {typeof val === 'number' ? val.toFixed(3) : String(val)}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* ── Details ── */}
        {result.details.length > 0 && (
          <div className="px-6 py-4 max-h-32 overflow-y-auto border-b border-border">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-text-muted mb-2">Details</p>
            <div className="space-y-1">
              {result.details.map((d, i) => (
                <p key={i} className="text-xs text-text-secondary">
                  {d.includes('correct') || d.startsWith('✓') ? '✅' : '🔸'} {d}
                </p>
              ))}
            </div>
          </div>
        )}

        {/* ── Actions ── */}
        <div className="px-6 py-4 flex gap-3">
          <Button onClick={onRunAgain} variant="primary" className="flex-1">
            <RotateCcw className="w-3.5 h-3.5" /> Run Again
          </Button>
          <Button onClick={onNextTask} variant="outline" className="flex-1">
            Next Task <ChevronRight className="w-3.5 h-3.5" />
          </Button>
          <Button onClick={onViewScores} variant="ghost">
            <BarChart3 className="w-3.5 h-3.5" />
          </Button>
        </div>
      </div>
    </div>
  )
}
