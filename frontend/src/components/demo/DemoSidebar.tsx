'use client'

import React from 'react'
import { TaskConfig } from '@/types'
import { Badge } from '@/components/ui/Badge'

interface DemoSidebarProps {
  tasks: TaskConfig[]
  selectedTask: string
  onSelectTask: (taskId: string) => void
  activeTab: string
  onSelectTab: (tab: string) => void
  episodeStats?: {
    turn: number
    maxTurns: number
    agreements: number
    totalClauses: number
    totalReward: number
  }
}

const TABS = [
  { id: 'negotiate', label: 'Negotiate' },
  { id: 'history', label: 'History' },
  { id: 'api', label: 'API Explorer' },
  { id: 'scores', label: 'Scores' },
]

export default function DemoSidebar({
  tasks,
  selectedTask,
  onSelectTask,
  activeTab,
  onSelectTab,
  episodeStats,
}: DemoSidebarProps) {
  const difficultyVariant: Record<string, any> = {
    easy: 'easy',
    medium: 'medium',
    hard: 'hard',
  }

  return (
    <aside className="w-60 bg-white border-r border-pink-200 p-5 flex flex-col gap-6">
      <div>
        <p className="text-xs font-semibold tracking-widest uppercase text-pink-400 mb-3">
          Tasks
        </p>
        <div className="space-y-2">
          {tasks.map(task => (
            <button
              key={task.task_id}
              onClick={() => onSelectTask(task.task_id)}
              className={`w-full text-left rounded-xl p-3 transition-all duration-200 ${
                selectedTask === task.task_id
                  ? 'bg-pink-100 border-2 border-pink-300'
                  : 'bg-pink-50 border-2 border-transparent hover:border-pink-200'
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-semibold text-charcoal">{task.name}</span>
                <Badge variant={difficultyVariant[task.difficulty] || 'pending'}>
                  {task.difficulty}
                </Badge>
              </div>
              <p className="text-xs text-muted leading-snug">{task.description}</p>
              <p className="text-xs font-mono text-pink-400 mt-1">
                target: {task.target_score} · {task.max_turns} turns
              </p>
            </button>
          ))}
        </div>
      </div>

      {/* Episode stats */}
      {episodeStats && (
        <div>
          <p className="text-xs font-semibold tracking-widest uppercase text-pink-400 mb-3">
            Episode Stats
          </p>
          <div className="space-y-2">
            <div className="flex justify-between text-xs">
              <span className="text-muted">Turn</span>
              <span className="font-mono font-semibold text-charcoal">
                {episodeStats.turn} / {episodeStats.maxTurns}
              </span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-muted">Agreements</span>
              <span className="font-mono font-semibold text-charcoal">
                {episodeStats.agreements} / {episodeStats.totalClauses}
              </span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-muted">Total Reward</span>
              <span
                className={`font-mono font-semibold ${
                  episodeStats.totalReward >= 0 ? 'text-emerald-600' : 'text-red-500'
                }`}
              >
                {episodeStats.totalReward >= 0 ? '+' : ''}
                {episodeStats.totalReward.toFixed(3)}
              </span>
            </div>
          </div>
          {/* Progress bar */}
          <div className="mt-3 h-1.5 bg-pink-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-pink-400 rounded-full transition-all duration-500"
              style={{
                width: `${Math.min(100, (episodeStats.turn / episodeStats.maxTurns) * 100)}%`,
              }}
            />
          </div>
        </div>
      )}

      {/* Tabs */}
      <div>
        <p className="text-xs font-semibold tracking-widest uppercase text-pink-400 mb-3">
          Views
        </p>
        <div className="space-y-1">
          {TABS.map(tab => (
            <button
              key={tab.id}
              onClick={() => onSelectTab(tab.id)}
              className={`w-full text-left px-3 py-2 rounded-xl text-sm font-medium transition-all ${
                activeTab === tab.id
                  ? 'bg-pink-100 text-pink-500'
                  : 'text-slate hover:bg-pink-50 hover:text-pink-500'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>
    </aside>
  )
}
