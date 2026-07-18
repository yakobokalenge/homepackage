import { defineStore } from 'pinia'
import { ref } from 'vue'
import { Assessment, AssessmentAttempt } from '../types/assessment'
import { assessmentService } from '../services/assessment.service'

export const useAssessmentStore = defineStore('assessment', () => {
  const assessments = ref<Assessment[]>([])
  const currentAssessment = ref<Assessment | null>(null)
  const studentAttempts = ref<AssessmentAttempt[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchAssessments(params?: Record<string, any>) {
    loading.value = true
    error.value = null
    try {
      assessments.value = await assessmentService.getAssessments(params)
    } catch (err: any) {
      error.value = err.response?.data?.message || 'Failed to load assessments.'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchAssessment(id: string) {
    loading.value = true
    error.value = null
    try {
      currentAssessment.value = await assessmentService.getAssessment(id)
      return currentAssessment.value
    } catch (err: any) {
      error.value = err.response?.data?.message || 'Failed to load assessment details.'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createAssessment(data: Partial<Assessment> & { questions_data?: any[] }) {
    loading.value = true
    try {
      const newAssessment = await assessmentService.createAssessment(data)
      assessments.value.unshift(newAssessment)
      return newAssessment
    } catch (err: any) {
      error.value = err.response?.data?.message || 'Failed to create assessment.'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateAssessment(id: string, data: Partial<Assessment> & { questions_data?: any[] }) {
    loading.value = true
    try {
      const updated = await assessmentService.updateAssessment(id, data)
      const index = assessments.value.findIndex(a => a.id === id)
      if (index !== -1) {
        assessments.value[index] = updated
      }
      if (currentAssessment.value?.id === id) {
        currentAssessment.value = updated
      }
      return updated
    } catch (err: any) {
      error.value = err.response?.data?.message || 'Failed to update assessment.'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteAssessment(id: string) {
    loading.value = true
    try {
      await assessmentService.deleteAssessment(id)
      assessments.value = assessments.value.filter(a => a.id !== id)
      if (currentAssessment.value?.id === id) {
        currentAssessment.value = null
      }
    } catch (err: any) {
      error.value = err.response?.data?.message || 'Failed to delete assessment.'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function duplicateAssessment(id: string) {
    loading.value = true
    try {
      const dup = await assessmentService.duplicateAssessment(id)
      assessments.value.unshift(dup)
      return dup
    } catch (err: any) {
      error.value = err.response?.data?.message || 'Failed to duplicate assessment.'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchStudentAttempts() {
    loading.value = true
    error.value = null
    try {
      studentAttempts.value = await assessmentService.getStudentAttempts()
    } catch (err: any) {
      error.value = err.response?.data?.message || 'Failed to load attempts.'
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    assessments,
    currentAssessment,
    studentAttempts,
    loading,
    error,
    fetchAssessments,
    fetchAssessment,
    createAssessment,
    updateAssessment,
    deleteAssessment,
    duplicateAssessment,
    fetchStudentAttempts
  }
})
