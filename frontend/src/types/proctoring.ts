export interface ProctoringConfig {
  require_webcam: boolean
  require_microphone: boolean
  require_screen_share: boolean
  browser_lockdown: boolean
  block_copy_paste: boolean
  block_right_click: boolean
  face_detection: boolean
  audio_detection: boolean
  record_video: boolean
  max_tab_switches: number
  max_violations_before_auto_submit: number
  auto_submit_on_violation: boolean
  identity_verification: boolean
  video_chunk_seconds: number
  retention_days: number

  // Legacy/Helper fields
  require_fullscreen?: boolean
  detect_face?: boolean
  detect_multiple_faces?: boolean
  detect_looking_away?: boolean
  detect_audio?: boolean
  max_violations?: number
  auto_submit_on_max?: boolean
  require_identity_verification?: boolean
  face_detection_interval_ms?: number
  audio_threshold_db?: number
  video_chunk_duration_ms?: number
  video_bitrate?: number
}

export interface ProctoringSession {
  id: string
  attempt_id: string
  student_id: string
  status: 'initializing' | 'active' | 'paused' | 'ended' | 'flagged'
  started_at: string
  ended_at?: string
  total_violations: number
  flags: ProctoringFlag[]
  video_chunks_uploaded: number
  identity_verified: boolean
}

export interface ProctoringFlag {
  id: string
  session_id: string
  type: ProctoringFlagType
  severity: 'low' | 'medium' | 'high' | 'critical'
  description: string
  timestamp: string
  screenshot_url?: string
  metadata?: Record<string, unknown>
  reviewed: boolean
  reviewer_action?: 'dismissed' | 'warning' | 'violation_confirmed'
}

export type ProctoringFlagType =
  | 'no_face'
  | 'multiple_faces'
  | 'looking_away'
  | 'tab_switch'
  | 'fullscreen_exit'
  | 'copy_paste'
  | 'right_click'
  | 'dev_tools'
  | 'audio_detected'
  | 'identity_mismatch'
  | 'browser_resize'
  | 'shortcut_blocked'
  | 'window_blur'
  | 'screenshot'
  | 'other'
  | 'unknown'

export interface VideoChunk {
  id: string
  session_id: string
  chunk_number: number
  blob: Blob
  duration_ms: number
  uploaded: boolean
  upload_attempts: number
}

export interface FaceDetectionResult {
  face_count: number
  looking_away: boolean
  head_yaw: number
  head_pitch: number
  head_roll: number
  confidence: number
}

export interface AudioAnalysisResult {
  is_speaking: boolean
  volume_db: number
  frequency_peak: number
}

export const DEFAULT_PROCTORING_CONFIG: ProctoringConfig = {
  require_webcam: true,
  require_microphone: false,
  require_screen_share: false,
  browser_lockdown: true,
  block_copy_paste: true,
  block_right_click: true,
  face_detection: true,
  audio_detection: false,
  record_video: true,
  max_tab_switches: 0,
  max_violations_before_auto_submit: 5,
  auto_submit_on_violation: false,
  identity_verification: false,
  video_chunk_seconds: 10,
  retention_days: 30,

  require_fullscreen: true,
  detect_face: true,
  detect_multiple_faces: true,
  detect_looking_away: true,
  detect_audio: true,
  max_violations: 5,
  auto_submit_on_max: true,
  require_identity_verification: false,
  face_detection_interval_ms: 500,
  audio_threshold_db: -30,
  video_chunk_duration_ms: 10000,
  video_bitrate: 500000
}
