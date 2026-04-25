'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'

import { api } from '@/lib/api'

type CompanyResponse = {
  company: {
    company_id: string
    company_name: string
    role_history: string[]
    total_sessions: number
    avg_negotiation_score: number
    constraint_templates: Array<{
      description: string
      clause_category: string
      priority: number
    }>
  }
  agreement_rate: number
  session_history: Array<{
    session_id: string
    status: string
    contract_title: string
    agreement_rate: number
    total_turns: number
    completed_at: string | null
  }>
}

function formatPct(value: number) {
  return `${Math.round((value || 0) * 100)}%`
}

export default function CompanyProfilePage({ params }: { params: { companyId: string } }) {
  const [data, setData] = useState<CompanyResponse | null>(null)

  useEffect(() => {
    api.companies.get(params.companyId).then((response) => setData(response.data))
  }, [params.companyId])

  if (!data) {
    return (
      <div className="min-h-screen bg-[linear-gradient(180deg,#fff8fb_0%,#ffe9f1_100%)] px-6 py-12 text-charcoal">
        <div className="mx-auto max-w-5xl animate-pulse rounded-[28px] bg-white/80 p-10 shadow-[0_18px_60px_rgba(232,67,147,0.12)]">
          <div className="h-10 w-72 rounded-full bg-pink-100" />
        </div>
      </div>
    )
  }

  const commonConstraints = data.company.constraint_templates.slice(0, 6)

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,#fff9fb_0%,#ffe8f1_55%,#ffd9e5_100%)] px-6 py-10 text-charcoal">
      <div className="mx-auto max-w-5xl space-y-6">
        <div className="rounded-[32px] border border-white/70 bg-white/85 p-8 shadow-[0_18px_60px_rgba(232,67,147,0.12)]">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-pink-400">Company Profile</p>
          <h1 className="mt-2 font-display text-4xl font-bold">{data.company.company_name}</h1>
          <div className="mt-6 grid gap-4 md:grid-cols-4">
            <div className="rounded-3xl bg-pink-50 p-4">
              <p className="text-xs uppercase tracking-[0.18em] text-pink-400">Roles Played</p>
              <p className="mt-2 text-sm font-semibold capitalize">{Array.from(new Set(data.company.role_history)).join(', ')}</p>
            </div>
            <div className="rounded-3xl bg-pink-50 p-4">
              <p className="text-xs uppercase tracking-[0.18em] text-pink-400">Total Sessions</p>
              <p className="mt-2 font-display text-3xl font-bold">{data.company.total_sessions}</p>
            </div>
            <div className="rounded-3xl bg-pink-50 p-4">
              <p className="text-xs uppercase tracking-[0.18em] text-pink-400">Agreement Rate</p>
              <p className="mt-2 font-display text-3xl font-bold">{formatPct(data.agreement_rate)}</p>
            </div>
            <div className="rounded-3xl bg-pink-50 p-4">
              <p className="text-xs uppercase tracking-[0.18em] text-pink-400">Avg Score</p>
              <p className="mt-2 font-display text-3xl font-bold">{data.company.avg_negotiation_score.toFixed(2)}</p>
            </div>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-[1fr_1.2fr]">
          <section className="rounded-[32px] border border-white/70 bg-white/85 p-6 shadow-[0_18px_60px_rgba(232,67,147,0.12)]">
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-pink-400">Constraint Templates</p>
            <h2 className="font-display text-2xl font-bold">Commonly reused private constraints</h2>
            <div className="mt-5 space-y-3">
              {commonConstraints.length === 0 && (
                <div className="rounded-3xl bg-pink-50 p-4 text-sm text-slate">No reusable constraint templates saved yet.</div>
              )}
              {commonConstraints.map((constraint, index) => (
                <div key={`${constraint.description}-${index}`} className="rounded-3xl border border-pink-100 bg-pink-50 p-4">
                  <div className="flex items-center justify-between gap-3">
                    <p className="font-semibold">{constraint.description}</p>
                    <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold uppercase tracking-[0.15em] text-pink-500">
                      {constraint.clause_category}
                    </span>
                  </div>
                  <p className="mt-2 text-sm text-slate">Priority {constraint.priority}</p>
                </div>
              ))}
            </div>
          </section>

          <section className="rounded-[32px] border border-white/70 bg-white/85 p-6 shadow-[0_18px_60px_rgba(232,67,147,0.12)]">
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-pink-400">Session History</p>
            <h2 className="font-display text-2xl font-bold">Negotiation outcomes</h2>
            <div className="mt-5 space-y-3">
              {data.session_history.map((session) => (
                <Link
                  key={session.session_id}
                  href={`/session/${session.session_id}/full`}
                  className="block rounded-3xl border border-pink-100 bg-white p-4 transition hover:border-pink-300 hover:bg-pink-50"
                >
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="font-semibold">{session.contract_title}</p>
                      <p className="mt-1 text-sm text-slate">
                        {session.status} • {formatPct(session.agreement_rate)} agreement • {session.total_turns} turns
                      </p>
                    </div>
                    <p className="text-sm text-slate">
                      {session.completed_at ? new Date(session.completed_at).toLocaleDateString() : 'In progress'}
                    </p>
                  </div>
                </Link>
              ))}
            </div>
          </section>
        </div>
      </div>
    </div>
  )
}
