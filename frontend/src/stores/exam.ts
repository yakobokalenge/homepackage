import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { Assessment, AssessmentAttempt, SaveAnswerPayload } from '../types/assessment'
import { assessmentService } from '../services/assessment.service'

export const useExamStore = defineStore('exam', () => {
  const currentAttempt = ref<AssessmentAttempt | null>(null)
  const assessment = ref<Assessment | null>(null)
  const activeQuestionIndex = ref(0)
  
  // Track local modifications to answers to prevent redundant API calls
  const localAnswers = ref<Record<string, SaveAnswerPayload>>({})
  const dirtyAnswers = ref<Record<string, boolean>>({})
  const timeRemainingSeconds = ref<number | null>(null)
  const isSaving = ref(false)
  const saveError = ref<string | null>(null)
  let timerInterval: any = null
  let autoSaveInterval: any = null

  const questions = computed(() => {
    return assessment.value?.assessment_questions || []
  })

  const currentQuestion = computed(() => {
    if (questions.value.length === 0) return null
    return questions.value[activeQuestionIndex.value]?.question || null
  })

  const isLastQuestion = computed(() => {
    return activeQuestionIndex.value === questions.value.length - 1
  })

  const isFirstQuestion = computed(() => {
    return activeQuestionIndex.value === 0
  })

  // Start exam session
  async function startExam(assessmentId: string) {
    stopTimer()
    stopAutoSaveTimer()
    isSaving.value = false
    saveError.value = null
    localAnswers.value = {}
    dirtyAnswers.value = {}
    activeQuestionIndex.value = 0
    
    try {
      const attempt = await assessmentService.startAttempt(assessmentId)
      currentAttempt.value = attempt
      assessment.value = await assessmentService.getAssessment(assessmentId)
      
      // Load any existing responses already submitted
      if (attempt.responses && attempt.responses.length > 0) {
        attempt.responses.forEach(resp => {
          localAnswers.value[resp.question] = {
            question_id: resp.question,
            selected_options: resp.selected_options || [],
            text_answer: resp.text_answer || '',
            matching_pairs: resp.matching_pairs || {},
            ordering_sequence: resp.ordering_sequence || []
          }
        })
      }

      // Initialize remaining time
      if (assessment.value?.time_limit_minutes) {
        const timeLimitSecs = assessment.value.time_limit_minutes * 60
        const timeSpentSecs = attempt.time_spent_seconds || 0
        timeRemainingSeconds.value = Math.max(0, timeLimitSecs - timeSpentSecs)
        startTimer()
      } else {
        timeRemainingSeconds.value = null
      }

      // Start periodic auto-save
      startAutoSaveTimer()

      return attempt
    } catch (err: any) {
      saveError.value = err.response?.data?.message || 'Failed to start exam.'
      throw err
    }
  }

  // Answer tracking
  function getAnswerForQuestion(questionId: string): SaveAnswerPayload {
    if (!localAnswers.value[questionId]) {
      localAnswers.value[questionId] = {
        question_id: questionId,
        selected_options: [],
        text_answer: '',
        matching_pairs: {},
        ordering_sequence: []
      }
    }
    return localAnswers.value[questionId]
  }

  async function updateAnswer(questionId: string, answerData: Partial<SaveAnswerPayload>) {
    if (!currentAttempt.value) return

    const answer = getAnswerForQuestion(questionId)
    Object.assign(answer, answerData)
    
    // Mark as dirty
    dirtyAnswers.value[questionId] = true

    // Autosave response to backend in background
    isSaving.value = true
    saveError.value = null
    try {
      await assessmentService.saveAnswer(currentAttempt.value.id, answer)
      dirtyAnswers.value[questionId] = false // successfully saved
    } catch (err: any) {
      saveError.value = 'Failed to autosave response. Check your connection.'
      console.error('Autosave failed:', err)
    } finally {
      isSaving.value = false
    }
  }

  async function uploadFileAnswer(questionId: string, file: File) {
    if (!currentAttempt.value) return
    isSaving.value = true
    saveError.value = null
    try {
      const resp = await assessmentService.uploadAnswerFile(currentAttempt.value.id, questionId, file)
      // Update local storage
      const answer = getAnswerForQuestion(questionId)
      answer.file_attachment = resp.file_attachment
      dirtyAnswers.value[questionId] = false // file uploads are direct and complete
    } catch (err: any) {
      saveError.value = 'Failed to upload file response.'
      throw err
    } finally {
      isSaving.value = false
    }
  }

  // Flush all dirty responses
  async function flushDirtyAnswers() {
    if (!currentAttempt.value) return
    const dirtyIds = Object.keys(dirtyAnswers.value).filter(id => dirtyAnswers.value[id])
    if (dirtyIds.length === 0) return

    isSaving.value = true
    try {
      for (const qId of dirtyIds) {
        const answer = localAnswers.value[qId]
        if (answer) {
          await assessmentService.saveAnswer(currentAttempt.value.id, answer)
          dirtyAnswers.value[qId] = false
        }
      }
    } catch (err) {
      console.error('Periodic autosave flush failed:', err)
      saveError.value = 'Failed to auto-save some responses. Retrying later...'
    } finally {
      isSaving.value = false
    }
  }

  function startAutoSaveTimer() {
    stopAutoSaveTimer()
    autoSaveInterval = setInterval(() => {
      flushDirtyAnswers()
    }, 30000) // 30 seconds

    window.addEventListener('visibilitychange', handleVisibilityChange)
  }

  function stopAutoSaveTimer() {
    if (autoSaveInterval) {
      clearInterval(autoSaveInterval)
      autoSaveInterval = null
    }
    window.removeEventListener('visibilitychange', handleVisibilityChange)
  }

  function handleVisibilityChange() {
    if (document.visibilityState === 'hidden') {
      console.log('Tab switched/window hidden. Flushing dirty answers.')
      flushDirtyAnswers()
    }
  }

  // Submit entire exam
  async function submitExam() {
    stopTimer()
    stopAutoSaveTimer()
    if (!currentAttempt.value) return
    
    isSaving.value = true
    try {
      // Flush any remaining dirty answers first
      await flushDirtyAnswers()

      // Bulk submission payload
      const answersPayload = Object.values(localAnswers.value)
      const res = await assessmentService.submitAttempt(currentAttempt.value.id, {
        answers: answersPayload
      })
      currentAttempt.value = res
      return res
    } catch (err: any) {
      saveError.value = err.response?.data?.message || 'Failed to submit exam.'
      throw err
    } finally {
      isSaving.value = false
    }
  }

  // Question navigation
  function nextQuestion() {
    if (!isLastQuestion.value) {
      activeQuestionIndex.value++
    }
  }

  function prevQuestion() {
    if (!isFirstQuestion.value) {
      activeQuestionIndex.value--
    }
  }

  function setQuestionIndex(index: number) {
    if (index >= 0 && index < questions.value.length) {
      activeQuestionIndex.value = index
    }
  }

  // Countdown timer logic
  function startTimer() {
    if (timerInterval) clearInterval(timerInterval)
    timerInterval = setInterval(() => {
      if (timeRemainingSeconds.value !== null && timeRemainingSeconds.value > 0) {
        timeRemainingSeconds.value--
        
        // Auto-submit when time runs out
        if (timeRemainingSeconds.value === 0) {
          submitExam()
        }
      }
    }, 1000)
  }

  function stopTimer() {
    if (timerInterval) {
      clearInterval(timerInterval)
      timerInterval = null
    }
    stopAutoSaveTimer()
  }

  return {
    currentAttempt,
    assessment,
    activeQuestionIndex,
    questions,
    currentQuestion,
    isFirstQuestion,
    isLastQuestion,
    timeRemainingSeconds,
    isSaving,
    saveError,
    localAnswers,
    dirtyAnswers,
    startExam,
    getAnswerForQuestion,
    updateAnswer,
    uploadFileAnswer,
    submitExam,
    nextQuestion,
    prevQuestion,
    setQuestionIndex,
    stopTimer
  }
})
