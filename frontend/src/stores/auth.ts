import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User, LoginPayload, RegisterPayload } from '@/types'
import { authService } from '@/services/auth.service'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('access_token'))
  const refreshTokenValue = ref<string | null>(localStorage.getItem('refresh_token'))
  const loading = ref(false)
  const error = ref<string | null>(null)

  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const isStudent = computed(() => user.value?.role === 'student')
  const isTeacher = computed(() => user.value?.role === 'teacher')
  const isSchoolAdmin = computed(() => user.value?.role === 'school_admin')
  const isSuperAdmin = computed(() => user.value?.role === 'super_admin' || user.value?.role === 'admin')
  const isAdmin = computed(() => isSuperAdmin.value || isSchoolAdmin.value)
  const fullName = computed(() =>
    user.value ? `${user.value.first_name} ${user.value.last_name}` : ''
  )
  const initials = computed(() =>
    user.value
      ? `${user.value.first_name[0]}${user.value.last_name[0]}`.toUpperCase()
      : ''
  )

  function parseError(err: any, defaultMsg: string): string {
    if (err.response?.data && typeof err.response.data === 'object') {
      const data = err.response.data
      const errorSource = (data.errors && typeof data.errors === 'object') ? data.errors : data
      if (errorSource.detail) return String(errorSource.detail)
      if (errorSource.non_field_errors) {
        return Array.isArray(errorSource.non_field_errors) ? errorSource.non_field_errors.join(', ') : String(errorSource.non_field_errors)
      }
      const messages = Object.entries(errorSource)
        .filter(([field]) => !['success', 'status_code', 'message'].includes(field))
        .map(([field, msgs]) => {
          const prefix = field.charAt(0).toUpperCase() + field.slice(1).replace('_', ' ')
          const msgText = Array.isArray(msgs) ? msgs.join(', ') : String(msgs)
          return `${prefix}: ${msgText}`
        })
        .join('; ')
      return messages || defaultMsg
    }
    return defaultMsg
  }

  async function login(payload: LoginPayload) {
    loading.value = true
    error.value = null
    try {
      const response = await authService.login(payload)
      token.value = response.access_token
      refreshTokenValue.value = response.refresh_token
      user.value = response.user
      localStorage.setItem('access_token', response.access_token)
      localStorage.setItem('refresh_token', response.refresh_token)
      return response
    } catch (err: any) {
      error.value = parseError(err, 'Login failed. Please try again.')
      throw err
    } finally {
      loading.value = false
    }
  }

  async function register(payload: RegisterPayload) {
    loading.value = true
    error.value = null
    try {
      const response = await authService.register(payload)
      token.value = response.access_token
      refreshTokenValue.value = response.refresh_token
      user.value = response.user
      localStorage.setItem('access_token', response.access_token)
      localStorage.setItem('refresh_token', response.refresh_token)
      return response
    } catch (err: any) {
      error.value = parseError(err, 'Registration failed. Please try again.')
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchUser() {
    if (!token.value) return
    loading.value = true
    try {
      user.value = await authService.me()
    } catch {
      logout()
    } finally {
      loading.value = false
    }
  }

  async function refreshToken() {
    if (!refreshTokenValue.value) return
    try {
      const response = await authService.refreshToken(refreshTokenValue.value)
      token.value = response.access_token
      refreshTokenValue.value = response.refresh_token
      localStorage.setItem('access_token', response.access_token)
      localStorage.setItem('refresh_token', response.refresh_token)
    } catch {
      logout()
    }
  }

  function logout() {
    authService.logout()
    user.value = null
    token.value = null
    refreshTokenValue.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  function clearError() {
    error.value = null
  }

  return {
    user,
    token,
    loading,
    error,
    isAuthenticated,
    isStudent,
    isTeacher,
    isSchoolAdmin,
    isSuperAdmin,
    isAdmin,
    fullName,
    initials,
    login,
    register,
    fetchUser,
    refreshToken,
    logout,
    clearError
  }
})
