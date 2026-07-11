import api from './api'
import type { Assessment, AssessmentAttempt } from '@/types/assessment'

export const assessmentService = {
  async list(params?: any): Promise<Assessment[]> {
    const res = await api.get('/assessments/', { params })
    return Array.isArray(res.data) ? res.data : res.data?.results || []
  },

  async get(id: string): Promise<Assessment> {
    const res = await api.get(`/assessments/${id}/`)
    return res.data
  },

  async create(data: Partial<Assessment>): Promise<Assessment> {
    const res = await api.post('/assessments/', data)
    return res.data
  },

  async update(id: string, data: Partial<Assessment>): Promise<Assessment> {
    const res = await api.patch(`/assessments/${id}/`, data)
    return res.data
  },

  async delete(id: string): Promise<void> {
    await api.delete(`/assessments/${id}/`)
  },

  async extractDocument(file: File, subjectId: string): Promise<{ questions: any[], provider: string }> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('subject', subjectId)
    formData.append('provider', 'auto')

    const res = await api.post('/assessments/extract-document/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return res.data
  },

  async saveExtracted(id: string, questions: any[]): Promise<{ count: number, total_points: number }> {
    const res = await api.post(`/assessments/${id}/save-extracted/`, { questions })
    return res.data
  },

  async startAttempt(id: string): Promise<AssessmentAttempt> {
    const res = await api.post(`/assessments/${id}/start/`)
    return res.data
  },

  async saveAnswer(attemptId: string, payload: { question_id: string, selected_option_id?: string, answer_text?: string }): Promise<any> {
    const res = await api.post(`/attempts/${attemptId}/save-answer/`, payload)
    return res.data
  },

  async submitAttempt(attemptId: string): Promise<AssessmentAttempt> {
    const res = await api.post(`/attempts/${attemptId}/submit/`)
    return res.data
  }
}
