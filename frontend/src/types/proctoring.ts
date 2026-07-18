import { AssessmentAttempt } from './assessment'

export type ProctoringFlagType =
  | 'no_face'
  | 'multiple_faces'
  | 'looking_away'
  | 'audio_detected'
  | 'tab_switch'
  | 'fullscreen_exit'
  | 'copy_paste'
  | 'right_click'
  | 'devtools'
  | 'identity_mismatch'
  | 'other'

export type ProctoringSeverity = 'low' | 'medium' | 'high' | 'critical'
export type ProctoringSessionStatus = 'pending_consent' | 'active' | 'completed' | 'terminated'

export interface ProctoringConfig {
  id: string
  assessment: string
  require_webcam: boolean
  require_microphone: boolean
  require_fullscreen: boolean
  block_copy_paste: boolean
  block_right_click: boolean
  block_devtools: boolean
  require_identity_verification: boolean
  max_tab_switches: number
  allowed_urls: string[]
  record_video: boolean
  record_audio: boolean
  ai_monitoring_enabled: boolean
  auto_submit_on_violation_count?: number | null
  review_period_days: number
  created_at: string
  updated_at: string
}

export interface ProctoringFlag {
  id: string
  session: string
  flag_type: ProctoringFlagType
  severity: ProctoringSeverity
  timestamp: number // Offset in seconds
  actual_time: string
  description: string
  screenshot?: string | null
  metadata: Record<string, any>
}

export interface ProctoringSession {
  id: string
  attempt: string
  assessment_title?: string
  student_name?: string
  consent_given: boolean
  consent_given_at?: string | null
  identity_photo?: string | null
  identity_verified: boolean
  identity_verification_score?: string | null
  status: ProctoringSessionStatus
  suspicion_score: string
  recording_urls: string[]
  started_at: string
  ended_at?: string | null
  teacher_reviewed: boolean
  teacher_review_notes: string
  reviewed_by?: string | null
  flags?: ProctoringFlag[]
  total_violations?: number
}

export interface ProctoringFlagReportPayload {
  flag_type: ProctoringFlagType
  severity: ProctoringSeverity
  timestamp: number
  description: string
  screenshot?: File | Blob | string | null
  metadata?: Record<string, any>
}
