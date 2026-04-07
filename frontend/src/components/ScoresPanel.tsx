'use client'

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { Badge } from '@/components/ui/Badge'
import { ScoreBar } from '@/components/ui/ScoreBar'
import type { GradeResult } from '@/types'

interface ScoresPanelProps {
  gradeResults: Record<string, GradeResult>
  targetScores: Record<string, number>
}

const TASK_META = [
  { id: 'task1', name: 'Clause Identification', difficulty: 'easy' as const },
  { id: 'task2', name: 'Clause Redlining', difficulty: 'medium' as const },
  { id: 'task3', name: 'Full Negotiation', difficulty: 'hard' as const },
]

export default function ScoresPanel({ gradeResults, targetScores }: ScoresPanelProps) {
  const hasResults = Object.keys(gradeResults).length > 0

  if (!hasResults) {
    return (
      <div className="flex-1 flex items-center justify-center p-4">
        <div className="text-center space-y-3">
          <div className="w-16 h-16 rounded-full bg-surface flex items-center justify-center mx-auto">
            <span className="text-2xl">📊</span>
          </div>
          <p className="text-sm text-text-secondary">Complete and grade episodes to see scores</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 p-4 space-y-4 overflow-y-auto">
      {/* ── Score Overview Cards ── */}
      <div className="grid grid-cols-3 gap-4">
        {TASK_META.map(t => {
          const result = gradeResults[t.id]
          const target = targetScores[t.id] ?? 0.5
          if (!result) {
            return (
              <div key={t.id} className="bg-card rounded-lg border border-border p-4 opacity-50">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xs font-medium text-text-primary">{t.name}</span>
                  <Badge variant={t.difficulty}>{t.difficulty}</Badge>
                </div>
                <p className="text-3xl font-mono text-text-muted">—</p>
                <p className="text-xs text-text-muted mt-1">Not graded yet</p>
              </div>
            )
          }
          const scoreColor = result.passed ? 'text-emerald-400' : result.score >= target * 0.8 ? 'text-amber-400' : 'text-red-400'
          return (
            <div key={t.id} className="bg-card rounded-lg border border-border p-4">
              <div className="flex items-center gap-2 mb-3">
                <span className="text-xs font-medium text-text-primary">{t.name}</span>
                <Badge variant={t.difficulty}>{t.difficulty}</Badge>
              </div>
              <p className={`text-3xl font-mono font-bold ${scoreColor}`}>
                {result.score.toFixed(2)}
              </p>
              <p className="text-xs text-text-muted mt-1">Target: {target.toFixed(2)}</p>
              <Badge variant={(result.passed ? 'success' : 'danger') as any} className="mt-2">
                {result.passed ? 'PASSED' : 'FAILED'}
              </Badge>
              <div className="mt-3">
                <ScoreBar value={result.score} targetScore={target} />
              </div>
            </div>
          )
        })}
      </div>

      {/* ── Breakdown Charts ── */}
      {Object.entries(gradeResults).map(([taskId, result]) => {
        const breakdownData = Object.entries(result.breakdown).map(([key, value]) => ({
          name: key.replace(/_/g, ' '),
          value: typeof value === 'number' ? value : 0,
          isNegative: typeof value === 'number' && value < 0,
        }))

        return (
          <div key={taskId} className="bg-card rounded-lg border border-border p-4">
            <p className="text-xs font-semibold text-text-primary mb-3">{taskId} — Breakdown</p>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={breakdownData}>
                <XAxis dataKey="name" tick={{ fontSize: 9, fill: '#64748b' }} angle={-20} textAnchor="end" height={50} />
                <YAxis tick={{ fontSize: 10, fill: '#64748b' }} />
                <Tooltip
                  contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8, fontSize: 11 }}
                  labelStyle={{ color: '#f1f5f9' }}
                />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {breakdownData.map((entry, i) => (
                    <Cell key={i} fill={entry.isNegative ? '#ef4444' : '#3b82f6'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )
      })}

      {/* ── Grade Details ── */}
      {Object.entries(gradeResults).map(([taskId, result]) => (
        <div key={`details-${taskId}`} className="bg-card rounded-lg border border-border p-4">
          <p className="text-xs font-semibold text-text-primary mb-3">{taskId} — Details</p>
          <div className="space-y-1 max-h-48 overflow-y-auto">
            {result.details.map((detail, i) => (
              <div key={i} className="flex items-start gap-2 text-xs">
                <span className="mt-0.5">{detail.startsWith('✓') || detail.includes('correct') ? '✅' : '🔸'}</span>
                <span className="text-text-secondary">{detail}</span>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
