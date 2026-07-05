import api from './api'
import type {
  Assessment,
  AssessmentCreatePayload,
  Attempt,
  Question,
  SubmitAnswerPayload,
  AnswerResponse
} from '@/types'

export const assessmentService = {
  async list(params?: {
    subject?: string
    grade_level?: string
    status?: string
    page?: number
    limit?: number
  }): Promise<{ assessments: Assessment[]; total: number }> {
    const { data } = await api.get('/assessments', { params })
    return data
  },

  async getById(id: string): Promise<Assessment> {
    const { data } = await api.get<Assessment>(`/assessments/${id}`)
    return data
  },

  async create(payload: AssessmentCreatePayload | FormData): Promise<Assessment> {
    const headers: any = {}
    if (payload instanceof FormData) {
      headers['Content-Type'] = undefined
    }
    const { data } = await api.post<Assessment>('/assessments/', payload, { headers })
    return data
  },

  async update(id: string, payload: Partial<AssessmentCreatePayload>): Promise<Assessment> {
    const { data } = await api.patch<Assessment>(`/assessments/${id}`, payload)
    return data
  },

  async delete(id: string): Promise<void> {
    await api.delete(`/assessments/${id}`)
  },

  async publish(id: string): Promise<Assessment> {
    const { data } = await api.post<Assessment>(`/assessments/${id}/publish`)
    return data
  },

  async getQuestions(assessmentId: string): Promise<Question[]> {
    const { data } = await api.get<Question[]>(`/assessments/${assessmentId}/questions/`)
    return data
  },

  async startAttempt(assessmentId: string): Promise<Attempt> {
    const { data } = await api.post<Attempt>(`/assessments/${assessmentId}/start/`)
    return data
  },

  async getAttempt(assessmentId: string, attemptId: string): Promise<Attempt> {
    const { data } = await api.get<Attempt>(`/attempts/${attemptId}/`)
    return data
  },

  async submitAnswer(
    assessmentId: string,
    attemptId: string,
    payload: SubmitAnswerPayload
  ): Promise<AnswerResponse> {
    const { data } = await api.post<AnswerResponse>(
      `/attempts/${attemptId}/answers/`,
      payload
    )
    return data
  },

  async submitAttempt(assessmentId: string, attemptId: string, submissionFile?: File): Promise<Attempt> {
    let payload: any = null
    const headers: any = {}
    if (submissionFile) {
      const formData = new FormData()
      formData.append('submission_file', submissionFile)
      payload = formData
      headers['Content-Type'] = undefined
    }
    const { data } = await api.post<Attempt>(
      `/assessments/${assessmentId}/submit/`,
      payload,
      { headers }
    )
    return data
  },

  async getMyAttempts(assessmentId: string): Promise<Attempt[]> {
    const { data } = await api.get<Attempt[]>(`/assessments/${assessmentId}/results/`)
    return data
  },

  async getSubmissions(assessmentId: string): Promise<Attempt[]> {
    const { data } = await api.get<Attempt[]>(`/attempts/`, {
      params: { assessment: assessmentId }
    })
    return data
  },

  async gradeAnswer(
    assessmentId: string,
    attemptId: string,
    answerId: string,
    payload: { points_earned: number; feedback?: string }
  ): Promise<AnswerResponse> {
    const { data } = await api.patch<AnswerResponse>(
      `/assessments/${assessmentId}/attempts/${attemptId}/answers/${answerId}`,
      payload
    )
    return data
  },

  async getStudentStats(): Promise<{
    total_assessments: number
    average_score: number
    total_time_minutes: number
    subjects: Array<{ subject: string; average_score: number; count: number }>
    recent_scores: Array<{ date: string; score: number; assessment_title: string }>
    weak_topics: Array<{ topic: string; score: number; total: number }>
  }> {
    const { data } = await api.get('/assessments/stats/student')
    return data
  },

  async getTeacherStats(): Promise<{
    total_assessments: number
    total_students: number
    total_submissions: number
    average_score: number
    recent_submissions: Attempt[]
    subject_breakdown: Array<{ subject: string; count: number; avg_score: number }>
  }> {
    const { data } = await api.get('/assessments/stats/teacher')
    return data
  }
}
