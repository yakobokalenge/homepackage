import api from './api'
import type { ProctoringSession, ProctoringFlag, ProctoringFlagType } from '@/types'

export const proctoringService = {
  async startSession(attemptId: string): Promise<ProctoringSession> {
    const { data } = await api.post<ProctoringSession>('/proctoring/sessions', {
      attempt_id: attemptId
    })
    return data
  },

  async endSession(sessionId: string): Promise<ProctoringSession> {
    const { data } = await api.post<ProctoringSession>(
      `/proctoring/sessions/${sessionId}/end`
    )
    return data
  },

  async getSession(sessionId: string): Promise<ProctoringSession> {
    const { data } = await api.get<ProctoringSession>(`/proctoring/sessions/${sessionId}`)
    return data
  },

  async reportFlag(
    sessionId: string,
    flag: {
      type: ProctoringFlagType
      severity: 'low' | 'medium' | 'high' | 'critical'
      description: string
      timestamp: string
      metadata?: Record<string, unknown>
    }
  ): Promise<ProctoringFlag> {
    const { data } = await api.post<ProctoringFlag>(
      `/proctoring/sessions/${sessionId}/flags`,
      flag
    )
    return data
  },

  async uploadVideoChunk(
    sessionId: string,
    chunkNumber: number,
    blob: Blob
  ): Promise<{ chunk_id: string; uploaded: boolean }> {
    const formData = new FormData()
    formData.append('video', blob, `chunk_${chunkNumber}.webm`)
    formData.append('chunk_number', chunkNumber.toString())

    const { data } = await api.post(
      `/proctoring/sessions/${sessionId}/video`,
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 60000
      }
    )
    return data
  },

  async uploadIdentityPhoto(
    sessionId: string,
    photo: Blob
  ): Promise<{ verified: boolean; confidence: number }> {
    const formData = new FormData()
    formData.append('photo', photo, 'identity.jpg')

    const { data } = await api.post(
      `/proctoring/sessions/${sessionId}/identity`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    )
    return data
  },

  async getFlags(sessionId: string): Promise<ProctoringFlag[]> {
    const { data } = await api.get<ProctoringFlag[]>(
      `/proctoring/sessions/${sessionId}/flags`
    )
    return data
  },

  async reviewFlag(
    sessionId: string,
    flagId: string,
    action: 'dismissed' | 'warning' | 'violation_confirmed'
  ): Promise<ProctoringFlag> {
    const { data } = await api.patch<ProctoringFlag>(
      `/proctoring/sessions/${sessionId}/flags/${flagId}`,
      { reviewer_action: action }
    )
    return data
  },

  async getSessionsByAttempt(attemptId: string): Promise<ProctoringSession[]> {
    const { data } = await api.get<ProctoringSession[]>(
      `/proctoring/sessions?attempt_id=${attemptId}`
    )
    return data
  }
}
