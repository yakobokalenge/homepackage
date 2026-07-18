import api from './api'
import {
  ProctoringConfig,
  ProctoringSession,
  ProctoringFlagReportPayload
} from '../types/proctoring'

export const proctoringService = {
  // Config
  async getConfig(assessmentId: string): Promise<ProctoringConfig> {
    const res = await api.get(`/proctoring/sessions/config/${assessmentId}/`)
    return res.data
  },

  async updateConfig(assessmentId: string, data: Partial<ProctoringConfig>): Promise<ProctoringConfig> {
    const res = await api.post(`/proctoring/sessions/config/${assessmentId}/`, data)
    return res.data
  },

  // Consent
  async giveConsent(attemptId: string): Promise<ProctoringSession> {
    const res = await api.post('/proctoring/sessions/give_consent/', { attempt: attemptId })
    return res.data
  },

  // Identity verification
  async verifyIdentity(sessionId: string, photo: Blob | File): Promise<ProctoringSession> {
    const formData = new FormData()
    formData.append('photo', photo, 'verification.jpg')
    const res = await api.post(`/proctoring/sessions/${sessionId}/verify_identity/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return res.data
  },

  // Flags reporting
  async reportFlag(sessionId: string, flag: ProctoringFlagReportPayload): Promise<any> {
    const formData = new FormData()
    formData.append('flag_type', flag.flag_type)
    formData.append('severity', flag.severity)
    formData.append('timestamp', String(flag.timestamp))
    formData.append('description', flag.description)
    if (flag.screenshot) {
      formData.append('screenshot', flag.screenshot)
    }
    if (flag.metadata) {
      formData.append('metadata', JSON.stringify(flag.metadata))
    }
    const res = await api.post(`/proctoring/sessions/${sessionId}/report_flag/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return res.data
  },

  // Upload chunk video
  async uploadRecordingChunk(sessionId: string, chunkBlob: Blob): Promise<any> {
    const formData = new FormData()
    formData.append('chunk', chunkBlob, 'chunk.webm')
    const res = await api.post(`/proctoring/sessions/${sessionId}/upload_chunk/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return res.data
  },

  // Teacher actions
  async getSessions(params?: Record<string, any>): Promise<ProctoringSession[]> {
    const res = await api.get('/proctoring/sessions/', { params })
    return Array.isArray(res.data) ? res.data : res.data.results || []
  },

  async getSession(id: string): Promise<ProctoringSession> {
    const res = await api.get(`/proctoring/sessions/${id}/`)
    return res.data
  },

  async submitReview(sessionId: string, reviewNotes: string): Promise<ProctoringSession> {
    const res = await api.post(`/proctoring/sessions/${sessionId}/review/`, { notes: reviewNotes })
    return res.data
  }
}
