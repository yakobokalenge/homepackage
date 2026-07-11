// Let's define the Question interfaces here or import from content types.
// Let's make it fully independent and complete.

export interface QuestionOption {
  id?: string
  text: string
  is_correct: boolean
  order: number
}

export interface AssessmentQuestionDetail {
  id: string
  text: string
  question_type: 'mcq' | 'true_false' | 'fill_blank' | 'short_answer' | 'essay'
  difficulty: 'easy' | 'medium' | 'hard' | 'critical'
  explanation?: string
  points: number
  options?: QuestionOption[]
}

export interface AssessmentQuestion {
  id: string
  question: AssessmentQuestionDetail
  order: number
  points_override?: number
}

export interface Assessment {
  id: string
  title: string
  description?: string
  assessment_type: 'quiz' | 'test' | 'assignment' | 'exam' | 'home_package'
  subject: string
  subject_name?: string
  classroom?: string
  classroom_name?: string
  status: 'draft' | 'published' | 'closed'
  start_time?: string
  end_time?: string
  duration_minutes?: number
  total_points: number
  pass_percentage: number
  questions_limit?: number
  questions?: AssessmentQuestion[]
  created_at: string
}

export interface AnswerResponse {
  id?: string
  attempt: string
  question: string
  selected_option?: string
  answer_text?: string
  points_awarded?: number
  is_correct?: boolean
  teacher_feedback?: string
  question_detail?: AssessmentQuestionDetail
}

export interface AssessmentAttempt {
  id: string
  assessment: string
  assessment_title?: string
  student: string
  student_name?: string
  started_at: string
  submitted_at?: string
  score?: number
  percentage?: number
  status: 'in_progress' | 'submitted' | 'graded'
  responses?: AnswerResponse[]
}

// Extracted Draft from PDF parser
export interface ExtractedOption {
  text: string
  is_correct: boolean
  order: number
}

export interface ExtractedQuestionDraft {
  text: string
  question_type: 'mcq' | 'true_false' | 'fill_blank' | 'short_answer' | 'essay'
  difficulty: 'easy' | 'medium' | 'hard'
  points: number
  explanation?: string
  options: ExtractedOption[]
}
