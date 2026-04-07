'use client'

import { useEffect, useState } from 'react'
import clsx from 'clsx'
import { Activity, RotateCcw, Award, Clock, Handshake, TrendingUp } from 'lucide-react'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { useHealthCheck } from '@/hooks/useHealthCheck'
import type { TaskConfig, EpisodeState } from '@/types'
import { api } from '@/lib/api'

interface SidebarProps {
  selectedTask: string
  onSelectTask: (taskId: string) => void
  onReset: () => void
  onGrade: () => void
  episodeState: EpisodeState
  isLoading: boolean
}

const difficultyVariant = { easy: 'easy', medium: 'medium', hard: 'hard' } as const

export default function Sidebar({
  selectedTask,
  onSelectTask,
  onReset,
  onGrade,
  episodeState,
  isLoading,
}: SidebarProps) {
  const { isOnline, version } = useHealthCheck()
  const [tasks, setTasks] = useState<TaskConfig[]>([])

  useEffect(() => {
    api.tasks().then(res => setTasks(res.data)).catch(() => {})
  }, [])

  return (
    <aside className="w-60 flex-shrink-0 flex flex-col bg-primary border-r border-border h-screen overflow-y-auto">
      {/* ── Branding ── */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-accent" />
          <h1 className="text-sm font-semibold text-text-primary">ContractEnv</h1>
          <Badge variant={'info' as any}>v{version || '1.0.0'}</Badge>
        </div>
        <div className="flex items-center gap-1.5 mt-2">
          <div className={clsx('w-2 h-2 rounded-full', isOnline ? 'bg-emerald-400' : 'bg-red-400')} />
          <span className="text-xs text-text-muted">{isOnline ? 'API online' : 'API offline'}</span>
        </div>
      </div>

      {/* ── Tasks ── */}
      <div className="p-3 space-y-2 flex-1">
        <p className="text-[10px] font-semibold uppercase tracking-wider text-text-muted mb-1">Tasks</p>
        {tasks.map(t => (
          <button
            key={t.task_id}
            onClick={() => onSelectTask(t.task_id)}
            className={clsx(
              'w-full text-left p-3 rounded-lg border transition-colors',
              selectedTask === t.task_id
                ? 'border-accent bg-accent/10 border-l-4'
                : 'border-border hover:bg-surface'
            )}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-text-primary">{t.name}</span>
              <Badge variant={difficultyVariant[t.difficulty] || 'neutral'}>{t.difficulty}</Badge>
            </div>
            <p className="text-[11px] text-text-muted mt-1 line-clamp-2">{t.description}</p>
            <p className="text-[10px] text-text-muted mt-1 font-mono">
              Target: {t.target_score} · {t.max_turns} turns
            </p>
          </button>
        ))}
      </div>

      {/* ── Episode Stats ── */}
      {episodeState.observation && (
        <div className="px-3 py-3 border-t border-border space-y-2">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-text-muted">Episode</p>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <Stat icon={<Clock className="w-3 h-3" />} label="Turn" value={`${episodeState.observation?.turn ?? 0} / ${episodeState.observation?.max_turns ?? 0}`} />
            <Stat icon={<Handshake className="w-3 h-3" />} label="Agreed" value={`${episodeState.observation?.agreements_reached ?? 0} / ${episodeState.observation?.total_clauses ?? 0}`} />
            <Stat icon={<TrendingUp className="w-3 h-3" />} label="Reward" value={(episodeState.reward?.value || 0).toFixed(2)} positive={(episodeState.reward?.value || 0) >= 0} />
            <Stat icon={<Activity className="w-3 h-3" />} label="Steps" value={String(episodeState.observation?.turn ?? 0)} />
          </div>
        </div>
      )}

      {/* ── Actions ── */}
      <div className="p-3 space-y-2 border-t border-border">
        <Button onClick={onReset} isLoading={isLoading} className="w-full">
          <RotateCcw className="w-3.5 h-3.5" /> Reset Episode
        </Button>
        {episodeState.done && (
          <Button variant="outline" onClick={onGrade} isLoading={isLoading} className="w-full">
            <Award className="w-3.5 h-3.5" /> Grade Episode
          </Button>
        )}
      </div>

      {/* ── Footer ── */}
      <div className="p-3 border-t border-border">
        <p className="text-[9px] text-text-muted text-center">
          Built for Meta / Scaler<br />OpenEnv Hackathon 2026
        </p>
      </div>
    </aside>
  )
}

function Stat({ icon, label, value, positive }: { icon: React.ReactNode; label: string; value: string; positive?: boolean }) {
  return (
    <div className="flex items-center gap-1.5 text-text-secondary">
      {icon}
      <div>
        <p className="text-[10px] text-text-muted">{label}</p>
        <p className={clsx('font-mono text-xs', positive === true && 'text-emerald-400', positive === false && 'text-red-400')}>
          {value}
        </p>
      </div>
    </div>
  )
}
