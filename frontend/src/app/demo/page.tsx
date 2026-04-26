'use client'

import { useState } from 'react'
import { Navbar } from '@/components/layout/Navbar'
import { Footer } from '@/components/layout/Footer'
import { ClauseTabBar } from '@/components/negotiation/ClauseTabBar'
import { ClauseCard } from '@/components/negotiation/ClauseCard'
import { useEpisode } from '@/hooks/useEpisode'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { JsonViewer } from '@/components/ui/JsonViewer'
import { ScoreBar } from '@/components/ui/ScoreBar'

export default function DemoPage() {
  const { episodeState, isLoading, reset, step, grade } = useEpisode()
  const [taskId, setTaskId] = useState('task1')
  const [activeClause, setActiveClause] = useState('c1')

  const TARGETS = { task1: 0.85, task2: 1.0, task3: 0.85 }
  const obs = episodeState.observation

  const handleStep = async (actionType: any) => {
    await step({ clause_id: activeClause, action_type: actionType })
  }

  const TASK_NAMES: Record<string, { title: string; subtitle: string }> = {
    task1: { title: 'Hidden Skeletons', subtitle: 'Data Room Lawsuit' },
    task2: { title: 'Compliance Trap', subtitle: 'US Export Control' },
    task3: { title: 'Post-Breach Settlement', subtitle: 'Gross Negligence' },
  }

  return (
    <div className="min-h-screen flex flex-col bg-pink-50">
      <Navbar />
      
      <main className="flex-1 flex max-h-[calc(100vh-73px)]">
        {/* SIDEBAR */}
        <div className="w-64 bg-white border-r border-pink-200 flex flex-col hidden md:flex">
          <div className="p-4 border-b border-pink-200">
            <h2 className="font-display font-bold text-lg text-charcoal">Select Task</h2>
          </div>
          <div className="p-4 space-y-3">
            {(['task1', 'task2', 'task3'] as const).map((t) => (
              <button 
                key={t} onClick={() => setTaskId(t)}
                className={`w-full text-left p-3 rounded-xl border transition-colors ${taskId === t ? 'bg-pink-50 border-pink-400 shadow-sm' : 'bg-white border-pink-200 hover:border-pink-300'}`}
              >
                <div className="font-semibold text-charcoal">
                  {TASK_NAMES[t].title}
                </div>
                <div className="text-xs text-muted mb-2">
                  {TASK_NAMES[t].subtitle}
                </div>
                <Badge variant="hard">
                  HARD
                </Badge>
              </button>
            ))}
            
            <Button onClick={() => reset(taskId)} isLoading={isLoading} className="w-full mt-4">
              Reset Episode
            </Button>
            {obs && (
              <Button variant="outline" onClick={() => grade()} isLoading={isLoading} className="w-full mt-2">
                Evaluate Score
              </Button>
            )}
          </div>
        </div>

        {/* MAIN */}
        <div className="flex-1 flex flex-col bg-white">
          {!obs ? (
            <div className="flex-1 flex flex-col items-center justify-center text-center p-8">
              <div className="w-16 h-16 bg-pink-50 text-pink-400 rounded-full flex items-center justify-center mb-4">
                <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"/><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
              </div>
              <h3 className="font-display font-bold text-2xl text-charcoal mb-2">No Episode Active</h3>
              <p className="text-slate mb-6">Select a task and hit "Reset Episode" to start the OpenEnv interactive debug dashboard.</p>
              <Button onClick={() => reset(taskId)}>Start {taskId}</Button>
            </div>
          ) : (
            <>
              {/* TOP NAV */}
              <div className="bg-white border-b border-pink-200">
                <ClauseTabBar clauses={obs.clauses} activeId={activeClause} onChange={setActiveClause} />
              </div>
              
              {/* CONTENT */}
              <div className="flex-1 overflow-y-auto p-6 bg-pink-50/30">
                <div className="max-w-4xl mx-auto space-y-6">
                  {obs.clauses.filter(c => c.id === activeClause).map(c => (
                    <ClauseCard key={c.id} clause={c} isActive={true} />
                  ))}
                  
                  {/* Data Room (if provided) */}
                  {obs.data_room && obs.data_room.length > 0 && (
                    <div className="bg-red-50 border border-red-200 rounded-2xl p-6 shadow-sm">
                      <h4 className="font-semibold text-red-600 mb-4">Data Room Documents</h4>
                      <div className="space-y-3">
                        {obs.data_room.map((doc, idx) => (
                          <div key={idx} className="bg-white rounded p-4 text-xs text-slate border border-red-100">
                            <div className="font-semibold text-charcoal">{doc.file_name}</div>
                            <div className="mt-1">{doc.summary}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {/* Action Panel */}
                  <div className="bg-white border border-pink-200 rounded-2xl p-6 shadow-sm">
                    <h4 className="font-semibold text-charcoal mb-4">Take Action</h4>
                    <div className="flex flex-wrap gap-3">
                      <Button onClick={() => handleStep('flag')} variant="outline">Flag Unfair</Button>
                      <Button onClick={() => handleStep('propose')} variant="outline">Propose Redline</Button>
                      <Button onClick={() => handleStep('accept')} variant="outline">Accept Text</Button>
                      <Button onClick={() => handleStep('reject')} variant="danger">Reject</Button>
                      <Button onClick={() => handleStep('skip')} variant="ghost">Skip Turn</Button>
                      <Button onClick={() => handleStep('terminate_deal')} variant="danger">Terminate Deal</Button>
                    </div>
                  </div>

                  {/* History List */}
                  <div className="bg-white border text-charcoal border-pink-200 rounded-2xl p-6 shadow-sm">
                    <h4 className="font-semibold mb-4">Turn History</h4>
                    <JsonViewer data={obs.negotiation_history} />
                  </div>
                </div>
              </div>
            </>
          )}
        </div>

        {/* RIGHT METRICS */}
        {obs && (
          <div className="w-72 bg-white border-l border-pink-200 p-5 hidden lg:block overflow-y-auto">
            <h3 className="text-xs font-bold tracking-widest uppercase text-pink-400 mb-6">Episode Stats</h3>
            
            <div className="space-y-6">
              <div>
                <div className="flex justify-between text-sm mb-1 text-charcoal font-medium">
                  <span>Turn Budget</span>
                  <span>{obs.turn} / {obs.max_turns}</span>
                </div>
                <div className="h-2 w-full bg-pink-100 rounded-full overflow-hidden">
                  <div className="h-full bg-pink-400 rounded-full" style={{width: `${(obs.turn/obs.max_turns)*100}%`}} />
                </div>
              </div>
              
              <div>
                <ScoreBar value={episodeState.reward?.value || 0} targetScore={(TARGETS as any)[taskId]} />
              </div>
              
              {episodeState.gradeResult && (
                <div className="bg-pink-50 rounded-xl p-4 border border-pink-200">
                  <div className="font-semibold text-charcoal mb-2">Grade Result</div>
                  <Badge variant={episodeState.gradeResult.passed ? 'agreed' : 'unfair'} className="mb-2">
                    {episodeState.gradeResult.passed ? 'PASSED' : 'FAILED'}
                  </Badge>
                  <div className="text-xs font-mono text-muted space-y-1">
                    {episodeState.gradeResult.details.map((d,i) => <div key={i}>{d}</div>)}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
