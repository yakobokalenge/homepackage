import api from './api'
import {
  Assessment,
  AssessmentAttempt,
  SaveAnswerPayload,
  SubmitAssessmentPayload
} from '../types/assessment'

export const assessmentService = {
  // Assessment CRUD
  async getAssessments(params?: Record<string, any>): Promise<Assessment[]> {
    const res = await api.get('/assessments/assessments/', { params })
    return Array.isArray(res.data) ? res.data : res.data.results || []
  },

  async getAssessment(id: string): Promise<Assessment> {
    const res = await api.get(`/assessments/assessments/${id}/`)
    return res.data
  },

  async createAssessment(data: Partial<Assessment> & { questions_data?: any[] }): Promise<Assessment> {
    const cleaned = { ...data }
    if (cleaned.classroom === '') cleaned.classroom = null
    if (cleaned.start_datetime === '') cleaned.start_datetime = null
    if (cleaned.end_datetime === '') cleaned.end_datetime = null
    if (cleaned.time_limit_minutes === ('' as any)) cleaned.time_limit_minutes = null
    const res = await api.post('/assessments/assessments/', cleaned)
    return res.data
  },

  async updateAssessment(id: string, data: Partial<Assessment> & { questions_data?: any[] }): Promise<Assessment> {
    const cleaned = { ...data }
    if (cleaned.classroom === '') cleaned.classroom = null
    if (cleaned.start_datetime === '') cleaned.start_datetime = null
    if (cleaned.end_datetime === '') cleaned.end_datetime = null
    if (cleaned.time_limit_minutes === ('' as any)) cleaned.time_limit_minutes = null
    const res = await api.patch(`/assessments/assessments/${id}/`, cleaned)
    return res.data
  },

  async deleteAssessment(id: string): Promise<void> {
    await api.delete(`/assessments/assessments/${id}/`)
  },

  async publishAssessment(id: string): Promise<any> {
    const res = await api.post(`/assessments/assessments/${id}/publish/`)
    return res.data
  },

  async closeAssessment(id: string): Promise<any> {
    const res = await api.post(`/assessments/assessments/${id}/close/`)
    return res.data
  },

  async duplicateAssessment(id: string): Promise<Assessment> {
    const res = await api.post(`/assessments/assessments/${id}/duplicate/`)
    return res.data
  },

  // AI-Assisted Question Generation & PDF Extraction
  async generateAIQuestions(id: string, data: {
    topic?: string
    question_types: string[]
    difficulty: string
    count: number
    prompt?: string
  }): Promise<any> {
    const res = await api.post(`/assessments/assessments/${id}/generate_ai/`, data)
    return res.data
  },

  async extractDocumentQuestions(file: File, subjectId: string): Promise<any> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('subject', subjectId)
    const res = await api.post('/assessments/assessments/extract_document/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return res.data
  },

  async saveExtractedQuestions(id: string, questions: any[]): Promise<any> {
    const res = await api.post(`/assessments/assessments/${id}/save_extracted/`, { questions })
    return res.data
  },

  // Assessment attempts (Student workflow)
  async startAttempt(assessmentId: string): Promise<AssessmentAttempt> {
    const res = await api.post('/assessments/attempts/start/', { assessment: assessmentId })
    return res.data
  },

  async saveAnswer(attemptId: string, answer: SaveAnswerPayload): Promise<any> {
    const res = await api.post(`/assessments/attempts/${attemptId}/save_answer/`, answer)
    return res.data
  },

  async uploadAnswerFile(attemptId: string, questionId: string, file: File): Promise<any> {
    const formData = new FormData()
    formData.append('question_id', questionId)
    formData.append('file_attachment', file)
    const res = await api.post(`/assessments/attempts/${attemptId}/save_answer/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return res.data
  },

  async submitAttempt(attemptId: string, payload?: SubmitAssessmentPayload): Promise<AssessmentAttempt> {
    const res = await api.post(`/assessments/attempts/${attemptId}/submit/`, payload || {})
    return res.data
  },

  async getAttempt(attemptId: string): Promise<AssessmentAttempt> {
    const res = await api.get(`/assessments/attempts/${attemptId}/`)
    return res.data
  },

  async getStudentAttempts(): Promise<AssessmentAttempt[]> {
    const res = await api.get('/assessments/attempts/')
    return Array.isArray(res.data) ? res.data : res.data.results || []
  },

  // Grading & Roster results (Teacher workflow)
  async getAssessmentResults(id: string): Promise<any> {
    const res = await api.get(`/assessments/assessments/${id}/results/`)
    return res.data
  },

  async gradeAttempt(attemptId: string, data: {
    grades: Record<string, { points_awarded: number; teacher_feedback: string }>
    feedback?: string
  }): Promise<AssessmentAttempt> {
    const res = await api.post(`/assessments/attempts/${attemptId}/grade/`, data)
    return res.data
  }
}
