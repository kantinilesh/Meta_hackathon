'use client'

import React from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { ScoreBar } from '@/components/ui/ScoreBar'

interface TaskScore {
  taskId: string
  taskName: string
  score: number
  targetScore: number
  passed: boolean
  breakdown?: Record<string, number>
}

interface ScoresDashboardProps {
  scores: TaskScore[]
}

export default function ScoresDashboard({ scores }: ScoresDashboardProps) {
  const chartData = scores.map(s => ({
    name: s.taskName.replace('Clause ', ''),
    score: Math.round(s.score * 100),
    target: Math.round(s.targetScore * 100),
  }))

  return (
    <div className="space-y-6">
      {/* Score cards */}
      <div className="grid grid-cols-3 gap-4">
        {scores.map(s => (
          <div
            key={s.taskId}
            className={`bg-white rounded-2xl border p-5 ${
              s.passed ? 'border-emerald-200' : 'border-pink-200'
            }`}
          >
            <div className="flex items-center justify-between mb-3">
              <p className="text-sm font-semibold text-charcoal">{s.taskName}</p>
              <span
                className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                  s.passed
                    ? 'bg-emerald-100 text-emerald-700'
                    : 'bg-pink-100 text-pink-500'
                }`}
              >
                {s.passed ? 'PASS' : 'IN PROGRESS'}
              </span>
            </div>
            <p className="text-3xl font-bold font-mono text-charcoal mb-1">
              {(s.score * 100).toFixed(1)}
              <span className="text-base text-muted font-normal">%</span>
            </p>
            <ScoreBar
              value={s.score}
              targetScore={s.targetScore}
            />
          </div>
        ))}
      </div>

      {/* Chart */}
      {chartData.length > 0 && (
        <div className="bg-white rounded-2xl border border-pink-200 p-6">
          <p className="text-xs font-semibold tracking-widest uppercase text-pink-400 mb-4">
            Score vs Target
          </p>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={chartData} barSize={32} barGap={4}>
              <CartesianGrid strokeDasharray="3 3" stroke="#ffc2d4" />
              <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#4a4a6a' }} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 12, fill: '#4a4a6a' }} />
              <Tooltip
                contentStyle={{
                  background: '#fff',
                  border: '1px solid #ffc2d4',
                  borderRadius: '12px',
                }}
              />
              <Bar dataKey="score" name="Score" fill="#ff6b9d" radius={[6, 6, 0, 0]} />
              <Bar dataKey="target" name="Target" fill="#ffe0e9" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}
