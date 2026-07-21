import api from './api'
import type { AuthResponse, LoginPayload, RegisterPayload, User } from '@/types'

export const authService = {
  async login(payload: LoginPayload): Promise<AuthResponse> {
    const { data } = await api.post<AuthResponse>('/auth/login/', payload)
    return data
  },

  async register(payload: RegisterPayload): Promise<AuthResponse> {
    const { data } = await api.post<AuthResponse>('/auth/register/', payload)
    return data
  },

  async me(): Promise<User> {
    const { data } = await api.get<User>('/auth/me/')
    return data
  },

  async refreshToken(refreshToken: string): Promise<AuthResponse> {
    const { data } = await api.post<AuthResponse>('/auth/refresh/', {
      refresh_token: refreshToken
    })
    return data
  },

  async logout(): Promise<void> {
    try {
      await api.post('/auth/logout/')
    } catch {
      // Ignore errors on logout
    }
  },

  async forgotPassword(email: string): Promise<void> {
    await api.post('/auth/forgot-password/', { email })
  },

  async resetPassword(token: string, password: string): Promise<void> {
    await api.post('/auth/reset-password/', { token, password })
  },

  async updateProfile(payload: Partial<User>): Promise<User> {
    const { data } = await api.patch<User>('/auth/profile', payload)
    return data
  },

  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    await api.post('/auth/change-password/', {
      current_password: currentPassword,
      new_password: newPassword
    })
  }
}
