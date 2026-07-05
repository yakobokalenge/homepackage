export interface User {
  id: string
  email: string
  phone?: string
  first_name: string
  last_name: string
  role: 'student' | 'teacher' | 'admin' | 'super_admin' | 'school_admin'
  avatar_url?: string
  is_active: boolean
  email_verified: boolean
  created_at: string
  updated_at: string
  profile?: StudentProfile | TeacherProfile
}

export interface StudentProfile {
  id: string
  user_id: string
  school_name?: string
  grade_level?: string
  region?: string
  date_of_birth?: string
  guardian_phone?: string
  subjects: string[]
  total_assessments_taken: number
  average_score: number
}

export interface TeacherProfile {
  id: string
  user_id: string
  school_name?: string
  employee_id?: string
  subjects: string[]
  region?: string
  qualification?: string
  total_students: number
  total_assessments_created: number
}

export interface LoginPayload {
  email: string
  password: string
}

export interface RegisterPayload {
  email: string
  password: string
  password_confirm: string
  first_name: string
  last_name: string
  phone?: string
  role: 'student' | 'teacher'
  school?: string
  classroom?: string
}

export interface AuthResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: User
}

export interface TokenRefreshPayload {
  refresh_token: string
}
