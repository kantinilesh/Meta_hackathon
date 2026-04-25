'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'

import { api } from '@/lib/api'

type SessionFullResponse = {
  session: {
    session_id: string
    status: string
    contract_title: string
    seller_config: { company_name: string } | null
    client_config: { company_name: string } | null
  }
  turns: Array<{
    turn_number: number
    speaker: string
    content: string
    clause_id: string
    proposed_text?: string | null
  }>
  outcomes: Array<{
    clause_id: string
    clause_title: string
    status: string
    final_agreed_text?: string | null
    turns_to_resolve: number
  }>
  final_contract_text: string
  metrics: {
    agreement_rate: number
    duration_seconds: number | null
  }
}

function formatPct(value: number) {
  return `${Math.round((value || 0) * 100)}%`
}

export default function SessionFullPage({ params }: { params: { sessionId: string } }) {
  const [data, setData] = useState<SessionFullResponse | null>(null)

  useEffect(() => {
    api.sessions.full(params.sessionId).then((response) => setData(response.data))
  }, [params.sessionId])

  if (!data) {
    return (
      <div className="min-h-screen bg-[linear-gradient(180deg,#fff8fb_0%,#ffe9f1_100%)] px-6 py-12 text-charcoal">
        <div className="mx-auto max-w-6xl animate-pulse rounded-[28px] bg-white/80 p-10 shadow-[0_18px_60px_rgba(232,67,147,0.12)]">
          <div className="h-10 w-80 rounded-full bg-pink-100" />
        </div>
      </div>
    )
  }

  const sellerName = data.session.seller_config?.company_name || 'Seller'
  const clientName = data.session.client_config?.company_name || 'Client'

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,#fff9fb_0%,#ffe8f1_55%,#ffd9e5_100%)] px-6 py-10 text-charcoal">
      <div className="mx-auto max-w-6xl space-y-6">
        <div className="rounded-[32px] border border-white/70 bg-white/85 p-8 shadow-[0_18px_60px_rgba(232,67,147,0.12)]">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-pink-400">Session Record</p>
          <h1 className="mt-2 font-display text-4xl font-bold">
            {sellerName} vs {clientName}
          </h1>
          <p className="mt-2 text-sm text-slate">{data.session.contract_title}</p>
          <div className="mt-6 grid gap-4 md:grid-cols-3">
            <div className="rounded-3xl bg-pink-50 p-4">
              <p className="text-xs uppercase tracking-[0.18em] text-pink-400">Status</p>
              <p className="mt-2 font-semibold capitalize">{data.session.status}</p>
            </div>
            <div className="rounded-3xl bg-pink-50 p-4">
              <p className="text-xs uppercase tracking-[0.18em] text-pink-400">Agreement Rate</p>
              <p className="mt-2 font-display text-3xl font-bold">{formatPct(data.metrics.agreement_rate)}</p>
            </div>
            <div className="rounded-3xl bg-pink-50 p-4">
              <p className="text-xs uppercase tracking-[0.18em] text-pink-400">Turns Logged</p>
              <p className="mt-2 font-display text-3xl font-bold">{data.turns.length}</p>
            </div>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
          <section className="rounded-[32px] border border-white/70 bg-white/85 p-6 shadow-[0_18px_60px_rgba(232,67,147,0.12)]">
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-pink-400">Clause Outcomes</p>
            <h2 className="font-display text-2xl font-bold">Resolution summary</h2>
            <div className="mt-5 space-y-3">
              {data.outcomes.map((outcome) => (
                <div key={outcome.clause_id} className="rounded-3xl border border-pink-100 bg-pink-50 p-4">
                  <div className="flex items-center justify-between gap-3">
                    <p className="font-semibold">{outcome.clause_title}</p>
                    <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold uppercase tracking-[0.14em] text-pink-500">
                      {outcome.status}
                    </span>
                  </div>
                  <p className="mt-2 text-sm text-slate">Resolved in {outcome.turns_to_resolve} turns</p>
                  {outcome.final_agreed_text && (
                    <p className="mt-3 rounded-2xl bg-white p-3 text-sm text-slate">{outcome.final_agreed_text}</p>
                  )}
                </div>
              ))}
            </div>
          </section>

          <section className="rounded-[32px] border border-white/70 bg-white/85 p-6 shadow-[0_18px_60px_rgba(232,67,147,0.12)]">
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-pink-400">Turn Log</p>
            <h2 className="font-display text-2xl font-bold">Negotiation transcript</h2>
            <div className="mt-5 space-y-3">
              {data.turns.map((turn) => (
                <div key={`${turn.turn_number}-${turn.speaker}-${turn.clause_id}`} className="rounded-3xl border border-pink-100 bg-white p-4">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-semibold">
                      Turn {turn.turn_number} • {turn.speaker}
                    </p>
                    <span className="text-xs uppercase tracking-[0.14em] text-pink-500">{turn.clause_id || 'system'}</span>
                  </div>
                  <p className="mt-2 text-sm text-slate">{turn.content}</p>
                  {turn.proposed_text && (
                    <p className="mt-3 rounded-2xl bg-pink-50 p-3 text-sm text-slate">{turn.proposed_text}</p>
                  )}
                </div>
              ))}
            </div>
          </section>
        </div>

        <section className="rounded-[32px] border border-white/70 bg-white/85 p-6 shadow-[0_18px_60px_rgba(232,67,147,0.12)]">
          <div className="mb-4 flex items-center justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-pink-400">Final Contract</p>
              <h2 className="font-display text-2xl font-bold">Agreed contract text</h2>
            </div>
            <Link href="/dashboard" className="rounded-full bg-pink-500 px-4 py-2 text-sm font-semibold text-white">
              Back to dashboard
            </Link>
          </div>
          <pre className="overflow-x-auto whitespace-pre-wrap rounded-3xl bg-pink-50 p-5 font-mono text-sm text-slate">
            {data.final_contract_text}
          </pre>
        </section>
      </div>
    </div>
  )
}
