'use client'
import React, { useState } from 'react'
import { Plus, Info } from 'lucide-react'
import clsx from 'clsx'
import { PrivateConstraint, ClauseCategory } from '@/types'

export function ConstraintBuilder({ onAdd }: { onAdd: (c: PrivateConstraint) => void }) {
  const templates = [
    { desc: "+ Non-compete: max 1 year", cat: "scope", rule: "max_value", val: "1 year", db: true },
    { desc: "+ IP carve-out required", cat: "ip", rule: "must_include", val: "carve-out", db: true },
    { desc: "+ Liability cap: $50,000", cat: "liability", rule: "max_value", val: "50000", db: false },
    { desc: "+ Payment: net-30", cat: "payment", rule: "must_exclude", val: "net-60", db: false },
    { desc: "+ Jurisdiction: Delaware", cat: "jurisdiction", rule: "prefer", val: "Delaware", db: false }
  ]

  const initialForm = {
    desc: '', cat: 'scope' as ClauseCategory, rule: 'must_include' as any, val: '', db: false
  }
  const [form, setForm] = useState(initialForm)

  const handleTemplate = (t: any) => {
    onAdd({
      constraint_id: 'c_' + Date.now(),
      description: t.desc.replace('+ ', ''),
      clause_category: t.cat,
      rule_type: t.rule,
      rule_value: t.val,
      is_deal_breaker: t.db,
      priority: t.db ? 1 : 2
    })
  }

  const handleCustomAdd = () => {
    if (!form.desc) return
    onAdd({
      constraint_id: 'c_' + Date.now(),
      description: form.desc,
      clause_category: form.cat,
      rule_type: form.rule,
      rule_value: form.val,
      is_deal_breaker: form.db,
      priority: form.db ? 1 : 3
    })
    setForm(initialForm)
  }

  return (
    <div className="space-y-6">
      <div>
        <label className="text-sm font-semibold text-slate mb-2 block">Quick Templates</label>
        <div className="flex flex-wrap gap-2">
          {templates.map((t, i) => (
            <button key={i} onClick={() => handleTemplate(t)} className="bg-pink-50 text-pink-500 border border-pink-200 px-3 py-1.5 rounded-full text-sm font-medium hover:bg-pink-100 transition-colors">
              {t.desc}
            </button>
          ))}
        </div>
      </div>

      <div className="bg-white border text-charcoal border-pink-200 rounded-2xl p-6 shadow-sm space-y-4">
        <h4 className="font-display font-semibold text-charcoal">Custom Constraint</h4>
        
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate mb-1">Description</label>
            <input value={form.desc} onChange={e=>setForm({...form, desc: e.target.value})} placeholder="e.g. Must include limitation of liability" className="w-full bg-pink-50 border border-pink-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-pink-400" />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate mb-1">Category</label>
            <select value={form.cat} onChange={e=>setForm({...form, cat: e.target.value as any})} className="w-full bg-pink-50 border border-pink-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-pink-400">
              <option value="scope">Scope</option><option value="duration">Duration</option>
              <option value="ip">IP</option><option value="liability">Liability</option>
              <option value="jurisdiction">Jurisdiction</option><option value="payment">Payment</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate mb-1">Rule Type</label>
            <select value={form.rule} onChange={e=>setForm({...form, rule: e.target.value as any})} className="w-full bg-pink-50 border border-pink-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-pink-400">
              <option value="must_include">Must Include</option><option value="must_exclude">Must Exclude</option>
              <option value="max_value">Max Value</option><option value="min_value">Min Value</option>
              <option value="prefer">Prefer</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate mb-1">Value matched</label>
            <input value={form.val} onChange={e=>setForm({...form, val: e.target.value})} placeholder="e.g. limitation" className="w-full bg-pink-50 border border-pink-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-pink-400" />
          </div>
        </div>

        <div className="flex items-center justify-between pt-2">
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" checked={form.db} onChange={e=>setForm({...form, db: e.target.checked})} className="rounded text-pink-500 focus:ring-pink-400 border-pink-300" />
            <span className="text-sm font-medium text-charcoal">This is a deal-breaker</span>
            {form.db && <span className="bg-red-100 text-red-600 text-[10px] px-2 py-0.5 rounded-full font-bold ml-2">DEAL-BREAKER</span>}
          </label>
          <button onClick={handleCustomAdd} disabled={!form.desc} className="flex items-center gap-1 bg-white border-2 border-pink-400 text-pink-500 px-4 py-2 rounded-xl text-sm font-semibold hover:bg-pink-50 disabled:opacity-50">
            <Plus className="w-4 h-4" /> Add Constraint
          </button>
        </div>
      </div>
    </div>
  )
}
