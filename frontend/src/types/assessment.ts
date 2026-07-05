export type QuestionType = 'mcq' | 'essay' | 'fill_blank' | 'matching' | 'true_false' | 'short_answer'

export interface QuestionOption {
  id: string
  text: string
  is_correct?: boolean
  order: number
}

export interface MatchingPair {
  id: string
  left: string
  right: string
}

export interface Question {
  id: string
  assessment_id: string
  type: QuestionType
  text: string
  points: number
  order: number
  options?: QuestionOption[]
  matching_pairs?: MatchingPair[]
  correct_answer?: string
  explanation?: string
  image_url?: string
  time_limit?: number
}

export interface Assessment {
  id: string
  title: string
  description?: string
  subject: string
  subject_name?: string
  grade_level: string
  teacher_id: string
  teacher_name?: string
  assessment_type: 'quiz' | 'test' | 'assignment' | 'exam' | 'home_package'
  duration_minutes: number
  total_points: number
  total_questions: number
  is_published: boolean
  is_proctored: boolean
  requires_proctoring: boolean
  is_file_based?: boolean
  file_attachment?: string
  proctoring_config?: ProctoringAssessmentConfig
  start_time?: string
  end_time?: string
  allowed_attempts: number
  shuffle_questions: boolean
  show_results: boolean
  passing_score: number
  created_at: string
  updated_at: string
  status: 'draft' | 'published' | 'closed' | 'archived'
}

export interface ProctoringAssessmentConfig {
  require_webcam: boolean
  require_fullscreen: boolean
  detect_face: boolean
  detect_multiple_faces: boolean
  detect_looking_away: boolean
  detect_audio: boolean
  record_video: boolean
  max_violations: number
  auto_submit_on_max: boolean
  require_identity_verification: boolean
}

export interface Attempt {
  id: string
  assessment_id: string
  student_id: string
  student_name?: string
  status: 'in_progress' | 'submitted' | 'graded' | 'abandoned'
  score?: number
  total_points: number
  percentage?: number
  started_at: string
  submitted_at?: string
  time_spent_seconds?: number
  answers: AnswerResponse[]
  violation_count?: number
  proctoring_flags?: number
  submission_file?: string
}

export interface AnswerResponse {
  id: string
  question_id: string
  attempt_id: string
  answer_text?: string
  selected_option_id?: string
  selected_option_ids?: string[]
  matching_answers?: Record<string, string>
  is_correct?: boolean
  points_earned?: number
  feedback?: string
}

export interface SubmitAnswerPayload {
  question_id: string
  answer_text?: string
  selected_option_id?: string
  selected_option_ids?: string[]
  matching_answers?: Record<string, string>
}

export interface AssessmentCreatePayload {
  title: string
  description?: string
  subject: string
  grade_level: string
  duration_minutes: number
  is_proctored: boolean
  is_file_based?: boolean
  file_attachment?: File
  proctoring_config?: ProctoringAssessmentConfig
  allowed_attempts: number
  shuffle_questions: boolean
  show_results: boolean
  passing_score: number
  questions?: QuestionCreatePayload[]
}

export interface QuestionCreatePayload {
  type: QuestionType
  text: string
  points: number
  order: number
  options?: Omit<QuestionOption, 'id'>[]
  matching_pairs?: Omit<MatchingPair, 'id'>[]
  correct_answer?: string
  explanation?: string
}
