export type ClauseCategory = 'scope' | 'duration' | 'ip' | 'liability' | 'jurisdiction' | 'payment' | 'termination'
export type ClauseLabel = 'fair' | 'unfair' | 'neutral'
export type ActionType = 'flag' | 'propose' | 'accept' | 'reject' | 'skip' | 'counter' | 'terminate_deal'
export type NegotiationRole = 'seller' | 'client'
export type SessionStatus = 'waiting_seller' | 'waiting_client' | 'ready' | 'negotiating' | 'completed' | 'failed' | 'paused'
export type DocumentType = 'financials' | 'bylaws' | 'due_diligence' | 'cap_table' | 'employment' | 'ip_assignment' | 'other'

export interface CompanyDocument {
  document_id: string
  file_name: string
  file_type: 'pdf' | 'docx' | 'txt' | 'xlsx'
  document_type: DocumentType
  summary: string
  key_terms: string[]
  upload_date: string
}

export interface PrivateConstraint {
  constraint_id: string
  description: string
  clause_category: ClauseCategory
  is_deal_breaker: boolean
  rule_type: 'max_value' | 'min_value' | 'must_include' | 'must_exclude' | 'prefer'
  rule_value: string | null
  priority: number
}

export interface PartyConfig {
  role: 'seller' | 'client'
  company_name: string
  constraints: PrivateConstraint[]
  agent_style: 'aggressive' | 'balanced' | 'cooperative'
  constraint_summary?: string
  company_context?: string
  documents?: CompanyDocument[]
}

export interface SessionCreateReq {
  contract_id: string
  seller_company_name: string
  seller_constraints: PrivateConstraint[]
  seller_agent_style: string
  seller_context?: string
}

export interface SessionJoinReq {
  invite_token: string
  client_company_name: string
  client_constraints: PrivateConstraint[]
  client_agent_style: string
  client_context?: string
}

export interface Clause {
  id: string
  title: string
  text: string
  category: ClauseCategory
  is_deal_breaker: boolean
  ground_truth_label: ClauseLabel | null
  current_proposed_text: string | null
  status: 'pending' | 'agreed' | 'rejected' | 'in_negotiation'
}

export interface NegotiationTurn {
  turn_number: number
  speaker: 'seller_agent' | 'client_agent' | 'system'
  action_type: ActionType
  clause_id: string
  content: string
  proposed_text?: string | null
  reward_delta?: number
  internal_reasoning?: string | null
  is_visible_to_both: boolean
}

export interface Observation {
  contract_id: string
  contract_title: string
  contract_text: string
  clauses: Clause[]
  negotiation_history: NegotiationTurn[]
  current_clause_id: string | null
  turn: number
  max_turns: number
  task_id: string
  agreements_reached: number
  total_clauses: number
  session_id?: string | null
  role?: NegotiationRole | null
  data_room?: CompanyDocument[]
}

export interface Action {
  clause_id: string
  action_type: ActionType
  label?: ClauseLabel | null
  reason?: string | null
  proposed_text?: string | null
  internal_reasoning?: string | null
}

export interface RewardBreakdown {
  flag_correct: number
  label_correct: number
  proposal_quality: number
  agreement_bonus: number
  constraint_satisfaction: number
  deal_breaker_penalty: number
  false_positive_penalty: number
  turn_efficiency_penalty: number
}

export interface Reward {
  value: number
  breakdown: RewardBreakdown
  done: boolean
  info: any
}

export interface TaskConfig {
  task_id: string
  name: string
  difficulty: 'easy' | 'medium' | 'hard'
  description: string
  max_turns: number
  target_score: number
}

export interface GradeResult {
  task_id: string
  score: number
  breakdown: any
  passed: boolean
  details: string[]
}

export interface NegotiationSession {
  session_id: string
  status: SessionStatus
  seller_config: PartyConfig | null
  client_config: PartyConfig | null
  contract_id: string
  contract_title: string
  clauses: Clause[]
  negotiation_history: NegotiationTurn[]
  final_agreed_clauses: Record<string, string>
  seller_signed: boolean
  client_signed: boolean
  created_at: string
  invite_token: string
  turn: number
  max_turns: number
}

export interface EpisodeState {
  observation: Observation
  reward: Reward | null
  done: boolean
  gradeResult: GradeResult | null
}

export interface StepResponse {
  observation: Observation
  reward: Reward
  done: boolean
  info: any
}
