<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { assessmentService } from '@/services/assessment.service'
import type { Assessment, AssessmentAttempt, AssessmentQuestion } from '@/types/assessment'

const route = useRoute()
const router = useRouter()
const assessmentId = route.params.id as string

// States
const loading = ref(true)
const assessment = ref<Assessment | null>(null)
const attempt = ref<AssessmentAttempt | null>(null)
const activeQuestionIndex = ref(0)

// Answers saved state map: { [questionId: string]: { selected_option_id?: string, answer_text?: string } }
const answersMap = ref<Record<string, { selected_option_id?: string, answer_text?: string }>>({})
const savingStatus = ref<Record<string, 'idle' | 'saving' | 'saved' | 'error'>>({})

// Timer
const timeRemaining = ref(0)
let timerInterval: any = null

const activeQuestion = computed(() => {
  if (!assessment.value?.questions || assessment.value.questions.length === 0) return null
  return assessment.value.questions[activeQuestionIndex.value]
})

const timerDisplay = computed(() => {
  if (timeRemaining.value <= 0) return '00:00'
  const minutes = Math.floor(timeRemaining.value / 60)
  const seconds = timeRemaining.value % 60
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
})

// Autosave helper
async function autoSaveAnswer(questionId: string) {
  if (!attempt.value) return
  savingStatus.value[questionId] = 'saving'
  
  const payload = {
    question_id: questionId,
    selected_option_id: answersMap.value[questionId]?.selected_option_id,
    answer_text: answersMap.value[questionId]?.answer_text || ''
  }

  try {
    await assessmentService.saveAnswer(attempt.value.id, payload)
    savingStatus.value[questionId] = 'saved'
  } catch (err) {
    savingStatus.value[questionId] = 'error'
  }
}

function handleOptionSelect(questionId: string, optionId: string) {
  if (!answersMap.value[questionId]) {
    answersMap.value[questionId] = {}
  }
  answersMap.value[questionId].selected_option_id = optionId
  autoSaveAnswer(questionId)
}

function handleTextChange(questionId: string, text: string) {
  if (!answersMap.value[questionId]) {
    answersMap.value[questionId] = {}
  }
  answersMap.value[questionId].answer_text = text
  autoSaveAnswer(questionId)
}

// Timer tick
function startCountdown(durationMinutes: number) {
  timeRemaining.value = durationMinutes * 60
  timerInterval = setInterval(() => {
    if (timeRemaining.value > 0) {
      timeRemaining.value--
    } else {
      clearInterval(timerInterval)
      alert('Time limit reached! Submitting assessment automatically...')
      submitExam()
    }
  }, 1000)
}

// Final Submit
const isSubmitting = ref(false)
async function submitExam() {
  if (!attempt.value) return
  
  const unansweredCount = (assessment.value?.questions || []).filter(
    q => !answersMap.value[q.question.id]?.selected_option_id && !answersMap.value[q.question.id]?.answer_text
  ).length

  if (unansweredCount > 0 && timeRemaining.value > 0) {
    if (!confirm(`You have ${unansweredCount} unanswered questions. Are you sure you want to submit?`)) return
  }

  isSubmitting.value = true
  clearInterval(timerInterval)

  try {
    const finalAttempt = await assessmentService.submitAttempt(attempt.value.id)
    alert(`Assessment submitted! Score: ${Math.round(finalAttempt.percentage || 0)}%`)
    router.push('/student/dashboard')
  } catch (err) {
    alert('Failed to submit. Please try again.')
  } finally {
    isSubmitting.value = false
  }
}

onMounted(async () => {
  try {
    // 1. Fetch details
    assessment.value = await assessmentService.get(assessmentId)
    
    // 2. Start attempt
    attempt.value = await assessmentService.startAttempt(assessmentId)

    // Prepopulate responses if attempt already exists
    if (attempt.value.responses) {
      attempt.value.responses.forEach(resp => {
        answersMap.value[resp.question] = {
          selected_option_id: resp.selected_option,
          answer_text: resp.answer_text
        }
        savingStatus.value[resp.question] = 'saved'
      })
    }

    // 3. Start timer
    if (assessment.value.duration_minutes) {
      startCountdown(assessment.value.duration_minutes)
    }
  } catch (err) {
    console.error(err)
  } finally {
    loading.value = false
  }
})

onUnmounted(() => {
  if (timerInterval) clearInterval(timerInterval)
})
</script>

<template>
  <div class="max-w-6xl mx-auto space-y-6">
    <div v-if="loading" class="text-center py-20 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl">
      <span class="animate-spin inline-block w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mb-4"></span>
      <p class="text-gray-500">Entering Exam Room...</p>
    </div>

    <template v-else-if="assessment && activeQuestion">
      <!-- Top Exam Bar -->
      <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-5 flex items-center justify-between shadow-sm">
        <div>
          <h1 class="text-lg font-bold text-gray-900 dark:text-white">{{ assessment.title }}</h1>
          <p class="text-xs text-gray-500 mt-0.5">{{ assessment.subject_name }} · {{ assessment.assessment_type.replace('_', ' ') }}</p>
        </div>
        <div class="flex items-center gap-4">
          <div v-if="assessment.duration_minutes" class="flex items-center gap-2 px-4 py-2 bg-rose-50 border border-rose-100 rounded-xl text-rose-700 font-bold text-sm font-mono shadow-sm">
            ⏱️ {{ timerDisplay }}
          </div>
          <button @click="submitExam" :disabled="isSubmitting" class="px-5 py-2.5 bg-gradient-to-r from-blue-600 to-emerald-600 text-white font-bold rounded-xl text-xs hover:shadow-lg transition-all flex items-center gap-2">
            <span v-if="isSubmitting" class="animate-spin inline-block w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full"></span>
            Submit Exam
          </button>
        </div>
      </div>

      <!-- Main take grid split layout -->
      <div class="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <!-- Question Navigation block -->
        <div class="lg:col-span-1 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-5 space-y-4 max-h-[70vh] overflow-y-auto">
          <h3 class="font-bold text-gray-900 dark:text-white text-xs uppercase tracking-wider">Exam Progress</h3>
          <div class="grid grid-cols-4 gap-2">
            <button v-for="(q, idx) in assessment.questions" :key="q.id" @click="activeQuestionIndex = idx"
              :class="['w-9 h-9 rounded-xl font-semibold text-xs border transition-all flex items-center justify-center', 
                activeQuestionIndex === idx ? 'bg-blue-600 border-blue-600 text-white font-bold shadow-md' :
                (answersMap[q.question.id]?.selected_option_id || answersMap[q.question.id]?.answer_text) ? 'bg-emerald-100 border-emerald-100 text-emerald-700 font-bold' : 'bg-gray-50 border-gray-100 text-gray-500 hover:bg-gray-100']">
              {{ idx + 1 }}
            </button>
          </div>
        </div>

        <!-- Question View & Answer Box card -->
        <div class="lg:col-span-3 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-8 flex flex-col justify-between min-h-[50vh]">
          <div class="space-y-6">
            <!-- Active Question Text -->
            <div class="space-y-3">
              <div class="flex justify-between items-center text-xs">
                <span class="font-bold text-gray-500 uppercase">Question {{ activeQuestionIndex + 1 }} of {{ assessment.questions?.length }}</span>
                <span :class="['font-semibold px-2 py-0.5 rounded uppercase text-[10px]', 
                  savingStatus[activeQuestion.question.id] === 'saving' ? 'bg-yellow-50 text-yellow-600' :
                  savingStatus[activeQuestion.question.id] === 'saved' ? 'bg-emerald-50 text-emerald-600' : 'bg-gray-50 text-gray-400']">
                  {{ savingStatus[activeQuestion.question.id] === 'saving' ? 'Saving...' :
                     savingStatus[activeQuestion.question.id] === 'saved' ? 'Saved ✓' : 'Unsaved' }}
                </span>
              </div>
              
              <div class="text-gray-900 dark:text-white text-base leading-relaxed whitespace-pre-line" v-html="activeQuestion.question.text"></div>
            </div>

            <!-- Options Form Box -->
            <div class="pt-6 border-t border-gray-100 dark:border-gray-850">
              <!-- MCQs options selection -->
              <div v-if="['mcq', 'true_false'].includes(activeQuestion.question.question_type)" class="space-y-3">
                <div v-for="opt in activeQuestion.question.options" :key="opt.id" @click="handleOptionSelect(activeQuestion.question.id, opt.id!)"
                  :class="['p-4 rounded-2xl border text-sm font-semibold cursor-pointer transition-all flex items-center justify-between', 
                    answersMap[activeQuestion.question.id]?.selected_option_id === opt.id ? 'bg-blue-50/50 border-blue-300 text-blue-800 dark:bg-blue-950/20 dark:border-blue-900 dark:text-blue-400' : 'bg-gray-50/50 border-gray-100 hover:bg-gray-50 text-gray-700 dark:bg-gray-850 dark:border-gray-800']">
                  <span>{{ opt.text }}</span>
                  <span :class="['w-5 h-5 rounded-full border flex items-center justify-center text-xs transition-all', 
                    answersMap[activeQuestion.question.id]?.selected_option_id === opt.id ? 'bg-blue-500 border-blue-500 text-white font-bold' : 'border-gray-300 dark:border-gray-700']">
                    {{ answersMap[activeQuestion.question.id]?.selected_option_id === opt.id ? '✓' : '' }}
                  </span>
                </div>
              </div>

              <!-- Open-ended / written text responses -->
              <div v-else class="space-y-2">
                <label class="text-xs font-semibold text-gray-500">Your Answer:</label>
                <textarea :value="answersMap[activeQuestion.question.id]?.answer_text || ''" @change="handleTextChange(activeQuestion.question.id, ($event.target as HTMLTextAreaElement).value)" rows="6" placeholder="Type your answer text explanation fully here..." class="w-full px-4 py-3 border border-gray-300 dark:border-gray-750 rounded-xl bg-white dark:bg-gray-850 text-sm focus:outline-none focus:border-blue-500 leading-relaxed"></textarea>
                <p class="text-[10px] text-gray-500">Your changes are automatically saved when you click outside the answer box (autosave on focus blur).</p>
              </div>
            </div>
          </div>

          <!-- Bottom next/prev buttons navigator -->
          <div class="flex justify-between items-center border-t border-gray-100 dark:border-gray-850 pt-6 mt-6">
            <button @click="activeQuestionIndex--" :disabled="activeQuestionIndex === 0" class="px-5 py-2 border border-gray-300 dark:border-gray-700 disabled:opacity-50 hover:bg-gray-50 text-gray-700 dark:text-gray-300 font-semibold rounded-xl text-xs transition-all">
              Previous Question
            </button>
            <button @click="activeQuestionIndex++" :disabled="activeQuestionIndex === ((assessment?.questions?.length || 1) - 1)" class="px-5 py-2 bg-blue-600 disabled:opacity-50 hover:bg-blue-700 text-white font-semibold rounded-xl text-xs transition-all">
              Next Question
            </button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
