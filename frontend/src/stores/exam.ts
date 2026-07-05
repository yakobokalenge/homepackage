import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Assessment, Question, Attempt, SubmitAnswerPayload, AnswerResponse } from '@/types'
import { assessmentService } from '@/services/assessment.service'

export const useExamStore = defineStore('exam', () => {
  const currentExam = ref<Assessment | null>(null)
  const questions = ref<Question[]>([])
  const currentAttempt = ref<Attempt | null>(null)
  const answers = ref<Map<string, AnswerResponse>>(new Map())
  const currentQuestionIndex = ref(0)
  const loading = ref(false)
  const submitting = ref(false)
  const error = ref<string | null>(null)
  const timeRemainingSeconds = ref(0)
  const timerInterval = ref<ReturnType<typeof setInterval> | null>(null)

  const currentQuestion = computed(() => questions.value[currentQuestionIndex.value] || null)
  const totalQuestions = computed(() => questions.value.length)
  const answeredCount = computed(() => answers.value.size)
  const progressPercent = computed(() =>
    totalQuestions.value > 0
      ? Math.round((answeredCount.value / totalQuestions.value) * 100)
      : 0
  )
  const isLastQuestion = computed(() => currentQuestionIndex.value === totalQuestions.value - 1)
  const isFirstQuestion = computed(() => currentQuestionIndex.value === 0)
  const timeFormatted = computed(() => {
    const mins = Math.floor(timeRemainingSeconds.value / 60)
    const secs = timeRemainingSeconds.value % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  })
  const isTimeWarning = computed(() => timeRemainingSeconds.value <= 300 && timeRemainingSeconds.value > 60)
  const isTimeCritical = computed(() => timeRemainingSeconds.value <= 60)

  async function startExam(assessmentId: string) {
    loading.value = true
    error.value = null
    try {
      currentExam.value = await assessmentService.getById(assessmentId)
      const questionsData = await assessmentService.getQuestions(assessmentId)
      questions.value = currentExam.value.shuffle_questions
        ? shuffleArray(questionsData)
        : questionsData
      currentAttempt.value = await assessmentService.startAttempt(assessmentId)
      answers.value = new Map()
      currentQuestionIndex.value = 0
      startTimer(currentExam.value.duration_minutes * 60)
      return currentAttempt.value
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to start exam'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function submitAnswer(payload: SubmitAnswerPayload) {
    if (!currentExam.value || !currentAttempt.value) return
    try {
      const response = await assessmentService.submitAnswer(
        currentExam.value.id,
        currentAttempt.value.id,
        payload
      )
      answers.value.set(payload.question_id, response)
      return response
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to submit answer'
      throw err
    }
  }

  async function submitExam() {
    if (!currentExam.value || !currentAttempt.value) return
    submitting.value = true
    try {
      stopTimer()
      const result = await assessmentService.submitAttempt(
        currentExam.value.id,
        currentAttempt.value.id
      )
      currentAttempt.value = result
      return result
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to submit exam'
      throw err
    } finally {
      submitting.value = false
    }
  }

  function goToQuestion(index: number) {
    if (index >= 0 && index < totalQuestions.value) {
      currentQuestionIndex.value = index
    }
  }

  function nextQuestion() {
    if (!isLastQuestion.value) {
      currentQuestionIndex.value++
    }
  }

  function previousQuestion() {
    if (!isFirstQuestion.value) {
      currentQuestionIndex.value--
    }
  }

  function startTimer(seconds: number) {
    timeRemainingSeconds.value = seconds
    timerInterval.value = setInterval(() => {
      if (timeRemainingSeconds.value > 0) {
        timeRemainingSeconds.value--
      } else {
        submitExam()
      }
    }, 1000)
  }

  function stopTimer() {
    if (timerInterval.value) {
      clearInterval(timerInterval.value)
      timerInterval.value = null
    }
  }

  function resetExam() {
    stopTimer()
    currentExam.value = null
    questions.value = []
    currentAttempt.value = null
    answers.value = new Map()
    currentQuestionIndex.value = 0
    error.value = null
  }

  function isQuestionAnswered(questionId: string): boolean {
    return answers.value.has(questionId)
  }

  function getAnswer(questionId: string): AnswerResponse | undefined {
    return answers.value.get(questionId)
  }

  function shuffleArray<T>(array: T[]): T[] {
    const shuffled = [...array]
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1))
      ;[shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]
    }
    return shuffled
  }

  return {
    currentExam,
    questions,
    currentAttempt,
    answers,
    currentQuestionIndex,
    loading,
    submitting,
    error,
    timeRemainingSeconds,
    currentQuestion,
    totalQuestions,
    answeredCount,
    progressPercent,
    isLastQuestion,
    isFirstQuestion,
    timeFormatted,
    isTimeWarning,
    isTimeCritical,
    startExam,
    submitAnswer,
    submitExam,
    goToQuestion,
    nextQuestion,
    previousQuestion,
    resetExam,
    isQuestionAnswered,
    getAnswer
  }
})
