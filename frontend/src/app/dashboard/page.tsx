'use client'

import Link from 'next/link'
import { useEffect, useMemo, useState } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { api } from '@/lib/api'

type SummaryResponse = {
  total_sessions: number
  total_companies: number
  avg_agreement_rate: number
  top_model: { overall_score?: number; model_name?: string } | null
}

type RecentSession = {
  session_id: string
  seller_company_name: string
  client_company_name: string
  contract_title: string
  status: string
  total_agreements: number
  total_clauses: number
  agreement_rate: number
  duration_seconds: number | null
  completed_at: string | null
}

type LeaderboardEntry = {
  run_id: string
  rank: number
  model_name: string
  task1_score: number
  task2_score: number
  task3_score: number
  overall_score: number
  submitted_at: string
}

type ClauseAnalytics = {
  clause_id: string
  clause_title: string
  agreement_rate: number
  total_appearances: number
}

const statusClasses: Record<string, string> = {
  completed: 'bg-emerald-100 text-emerald-700',
  negotiating: 'bg-pink-100 text-pink-700 animate-pulse',
  failed: 'bg-rose-100 text-rose-700',
}

function formatPct(value: number) {
  return `${Math.round((value || 0) * 100)}%`
}

function formatDate(value: string | null) {
  if (!value) return 'In progress'
  return new Date(value).toLocaleDateString()
}

function formatDuration(seconds: number | null) {
  if (!seconds) return '—'
  const minutes = Math.floor(seconds / 60)
  const remainder = seconds % 60
  return `${minutes}m ${remainder}s`
}

export default function DashboardPage() {
  const [summary, setSummary] = useState<SummaryResponse | null>(null)
  const [recentSessions, setRecentSessions] = useState<RecentSession[]>([])
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([])
  const [clauses, setClauses] = useState<ClauseAnalytics[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let mounted = true
    Promise.all([
      api.analytics.summary(),
      api.sessions.recent(),
      api.leaderboard.get(20),
      api.analytics.clauses(6),
    ])
      .then(([summaryRes, sessionsRes, leaderboardRes, clausesRes]) => {
        if (!mounted) return
        setSummary(summaryRes.data)
        setRecentSessions(sessionsRes.data)
        setLeaderboard(leaderboardRes.data)
        setClauses(clausesRes.data)
      })
      .finally(() => {
        if (mounted) setLoading(false)
      })
    return () => {
      mounted = false
    }
  }, [])

  const currentBestRunId = useMemo(() => leaderboard[0]?.run_id, [leaderboard])

  if (loading) {
    return (
      <div className="min-h-screen bg-[linear-gradient(180deg,#fff8fb_0%,#ffe9f1_100%)] px-6 py-12 text-charcoal">
        <div className="mx-auto max-w-7xl animate-pulse">
          <div className="h-12 w-72 rounded-full bg-pink-100" />
        </div>
      </div>
    )
  }

  const statCards = [
    { label: 'Total Sessions', value: summary?.total_sessions ?? 0 },
    { label: 'Total Companies', value: summary?.total_companies ?? 0 },
    { label: 'Avg Agreement Rate', value: formatPct(summary?.avg_agreement_rate ?? 0) },
    { label: 'Top Model Score', value: `${((summary?.top_model?.overall_score ?? 0) * 100).toFixed(1)}%` },
  ]

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,#fff9fb_0%,#ffe7f0_55%,#ffdbe7_100%)] px-6 py-10 text-charcoal">
      <div className="mx-auto flex max-w-7xl flex-col gap-8">
        <div>
          <p className="mb-2 text-sm font-semibold uppercase tracking-[0.24em] text-pink-500">Dashboard</p>
          <h1 className="font-display text-4xl font-bold">ContractEnv platform analytics</h1>
          <p className="mt-2 max-w-2xl text-sm text-slate">
            Live session history, model performance, and the clauses that create the most friction.
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {statCards.map((card) => (
            <div
              key={card.label}
              className="rounded-[28px] border border-white/70 bg-white/80 p-5 shadow-[0_18px_60px_rgba(232,67,147,0.12)] backdrop-blur"
            >
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-pink-400">{card.label}</p>
              <p className="mt-3 font-display text-3xl font-bold">{card.value}</p>
            </div>
          ))}
        </div>

        <div className="grid gap-6 xl:grid-cols-[1.6fr_1fr]">
          <section className="rounded-[32px] border border-white/70 bg-white/85 p-6 shadow-[0_18px_60px_rgba(232,67,147,0.12)]">
            <div className="mb-5 flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-pink-400">Recent Sessions</p>
                <h2 className="font-display text-2xl font-bold">Negotiation history</h2>
              </div>
            </div>

            <div className="overflow-hidden rounded-3xl border border-pink-100">
              <table className="min-w-full text-left text-sm">
                <thead className="bg-pink-50 text-slate">
                  <tr>
                    <th className="px-4 py-3">Companies</th>
                    <th className="px-4 py-3">Contract</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Agreements</th>
                    <th className="px-4 py-3">Duration</th>
                    <th className="px-4 py-3">Date</th>
                  </tr>
                </thead>
                <tbody>
                  {recentSessions.map((session) => (
                    <tr key={session.session_id} className="border-t border-pink-100 transition hover:bg-pink-50/60">
                      <td className="px-4 py-4">
                        <Link href={`/session/${session.session_id}/full`} className="font-semibold hover:text-pink-600">
                          {session.seller_company_name} vs {session.client_company_name}
                        </Link>
                      </td>
                      <td className="px-4 py-4">{session.contract_title}</td>
                      <td className="px-4 py-4">
                        <span className={`rounded-full px-3 py-1 text-xs font-semibold ${statusClasses[session.status] || 'bg-slate-100 text-slate-700'}`}>
                          {session.status}
                        </span>
                      </td>
                      <td className="px-4 py-4">
                        {session.total_agreements}/{session.total_clauses} ({formatPct(session.agreement_rate)})
                      </td>
                      <td className="px-4 py-4">{formatDuration(session.duration_seconds)}</td>
                      <td className="px-4 py-4">{formatDate(session.completed_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <aside className="rounded-[32px] border border-white/70 bg-[#fff7fa] p-6 shadow-[0_18px_60px_rgba(232,67,147,0.12)]">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-pink-400">Leaderboard</p>
            <h2 className="font-display text-2xl font-bold">Model Performance Leaderboard</h2>
            <div className="mt-5 overflow-hidden rounded-3xl border border-pink-100">
              <table className="min-w-full text-left text-sm">
                <thead className="bg-pink-50 text-slate">
                  <tr>
                    <th className="px-3 py-3">Rank</th>
                    <th className="px-3 py-3">Model</th>
                    <th className="px-3 py-3">T1</th>
                    <th className="px-3 py-3">T2</th>
                    <th className="px-3 py-3">T3</th>
                    <th className="px-3 py-3">Avg</th>
                    <th className="px-3 py-3">Date</th>
                  </tr>
                </thead>
                <tbody>
                  {leaderboard.map((entry) => (
                    <tr
                      key={entry.run_id}
                      className={`border-t border-pink-100 ${entry.run_id === currentBestRunId ? 'bg-pink-100/70' : 'bg-white'}`}
                    >
                      <td className="px-3 py-3 font-semibold">#{entry.rank}</td>
                      <td className="px-3 py-3">{entry.model_name}</td>
                      <td className="px-3 py-3">{entry.task1_score.toFixed(2)}</td>
                      <td className="px-3 py-3">{entry.task2_score.toFixed(2)}</td>
                      <td className="px-3 py-3">{entry.task3_score.toFixed(2)}</td>
                      <td className="px-3 py-3 font-semibold">{entry.overall_score.toFixed(2)}</td>
                      <td className="px-3 py-3">{formatDate(entry.submitted_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </aside>
        </div>

        <section className="rounded-[32px] border border-white/70 bg-white/85 p-6 shadow-[0_18px_60px_rgba(232,67,147,0.12)]">
          <div className="mb-5">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-pink-400">Clause Analytics</p>
            <h2 className="font-display text-2xl font-bold">Most Contested Clauses</h2>
          </div>
          <div className="h-[360px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={clauses} margin={{ top: 16, right: 16, left: 0, bottom: 8 }}>
                <CartesianGrid stroke="#ffd3e0" vertical={false} />
                <XAxis dataKey="clause_title" tick={{ fill: '#6b7280', fontSize: 12 }} />
                <YAxis tickFormatter={(value) => `${Math.round(value * 100)}%`} tick={{ fill: '#6b7280', fontSize: 12 }} />
                <Tooltip formatter={(value: number) => `${(value * 100).toFixed(1)}%`} />
                <Bar dataKey="agreement_rate" radius={[12, 12, 0, 0]} fill="#e84393" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>
      </div>
    </div>
  )
}
