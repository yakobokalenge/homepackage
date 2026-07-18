import { User } from './user'

export type AssessmentType = 'quiz' | 'test' | 'assignment' | 'exam' | 'home_package'
export type AssessmentStatus = 'draft' | 'published' | 'active' | 'closed' | 'archived'
export type DifficultyLevel = 'easy' | 'medium' | 'hard' | 'mixed'
export type AttemptStatus = 'not_started' | 'in_progress' | 'submitted' | 'graded' | 'timed_out'

export interface SubjectDetails {
  id: string
  name: string
  name_sw: string
  code: string
  education_level: string
  icon: string
  is_active: boolean
}

export interface QuestionOption {
  id: string
  text: string
  is_correct?: boolean
  order: number
  match_pair: string
}

export interface Question {
  id: string
  subject: string
  subject_name?: string
  topic?: string
  question_type: 'mcq' | 'multi_select' | 'true_false' | 'fill_blank' | 'short_answer' | 'essay' | 'matching' | 'ordering'
  difficulty: 'easy' | 'medium' | 'hard'
  text: string
  text_sw: string
  explanation: string
  points: string
  time_limit_seconds?: number | null
  media: string[]
  options: QuestionOption[]
  metadata?: any
}

export interface AssessmentQuestion {
  id: string
  question: Question
  order: number
  points_override?: string | null
  is_required: boolean
}

export interface Assessment {
  id: string
  subject: string
  subject_name?: string
  subject_details?: SubjectDetails
  classroom?: string | null
  classroom_name?: string
  created_by: string
  created_by_name?: string
  title: string
  description: string
  instructions: string
  assessment_type: AssessmentType
  status: AssessmentStatus
  difficulty: DifficultyLevel
  time_limit_minutes?: number | null
  max_attempts: number
  passing_score: string
  shuffle_questions: boolean
  shuffle_options: boolean
  show_results_immediately: boolean
  show_correct_answers: boolean
  is_proctored: boolean
  allow_late_submission: boolean
  start_datetime?: string | null
  end_datetime?: string | null
  attachments: string[]
  assessment_questions?: AssessmentQuestion[]
  question_count?: number
  total_points?: string
  created_at: string
  updated_at: string
}

export interface AnswerResponse {
  id: string
  attempt: string
  question: string
  selected_options: string[]
  text_answer: string
  matching_pairs: Record<string, string>
  ordering_sequence: string[]
  file_attachment?: string | null
  is_correct?: boolean | null
  points_awarded: string
  teacher_feedback: string
  auto_graded: boolean
  answered_at: string
  
  // Extra fields populated during results retrieval
  question_type?: string
  question_points?: number
  question_text?: string
}

export interface AssessmentAttempt {
  id: string
  assessment: string
  assessment_title?: string
  assessment_type?: AssessmentType
  is_proctored?: boolean
  student: string
  student_name?: string
  status: AttemptStatus
  started_at: string
  submitted_at?: string | null
  graded_at?: string | null
  score?: string | null
  percentage?: string | null
  time_spent_seconds: number
  attempt_number: number
  ip_address?: string | null
  user_agent?: string
  is_late: boolean
  graded_by?: string | null
  feedback: string
  responses?: AnswerResponse[]
}

export interface SaveAnswerPayload {
  question_id: string
  selected_options?: string[]
  text_answer?: string
  matching_pairs?: Record<string, string>
  ordering_sequence?: string[]
  file_attachment?: string | null
}

export interface SubmitAssessmentPayload {
  answers: SaveAnswerPayload[]
}
