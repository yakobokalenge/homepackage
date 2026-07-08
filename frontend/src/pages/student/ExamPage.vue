<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { assessmentService } from '@/services/assessment.service'
import { useNotificationStore } from '@/stores/notification'
import type { Assessment, Attempt } from '@/types'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const notify = useNotificationStore()

const examId = route.params.id as string
const assessment = ref<Assessment | null>(null)
const attempt = ref<Attempt | null>(null)
const questions = ref<any[]>([])
const currentIndex = ref(0)
const showConfirm = ref(false)
const submitted = ref(false)
const score = ref<number | null>(null)
const loading = ref(true)
const submitting = ref(false)
const errorMessage = ref('')

// Student's local state
const answers = ref<Record<string, string>>({})
const currentQ = computed(() => questions.value[currentIndex.value])
const timeRemaining = ref(7200) // fallback to 2h in seconds
let timer: ReturnType<typeof setInterval>

// File Based States
const studentFile = ref<File | null>(null)
const fileBasedAnswers = ref('')
const pdfLoaded = ref(false)
const pdfError = ref(false)

const fileAttachmentUrl = computed(() => {
  if (!assessment.value?.file_attachment) return ''
  const url = assessment.value.file_attachment
  if (url.startsWith('http')) return url
  return `http://localhost:8000${url.startsWith('/') ? '' : '/'}${url}`
})

function formatTime(s: number) {
  const h = Math.floor(s / 3600); const m = Math.floor((s % 3600) / 60); const sec = s % 60
  return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${sec.toString().padStart(2, '0')}`
}

onMounted(async () => {
  try {
    // Start attempt and fetch assessment metadata in parallel
    const [data, attemptData] = await Promise.all([
      assessmentService.getById(examId),
      assessmentService.startAttempt(examId)
    ])
    
    assessment.value = data
    attempt.value = attemptData
    timeRemaining.value = (data.duration_minutes || 120) * 60

    // 3. Load questions if interactive
    if (!data.is_file_based) {
      const qList = await assessmentService.getQuestions(examId)
      if (qList && qList.length > 0) {
        questions.value = qList
      } else {
        // Fallback mockup questions if none exist
        questions.value = [
          { id: '1', type: 'mcq', text: 'Which organelle is responsible for photosynthesis?', options: [{ id: 'a', text: 'Mitochondria' }, { id: 'b', text: 'Chloroplast' }, { id: 'c', text: 'Ribosome' }, { id: 'd', text: 'Nucleus' }] },
          { id: '2', type: 'true_false', text: 'DNA replication occurs during the S phase of the cell cycle.', options: [{ id: 'a', text: 'True' }, { id: 'b', text: 'False' }] }
        ]
      }
    } else {
      // For file-based: auto-dismiss loading overlay after 3s (embed tags don't fire load events reliably)
      setTimeout(() => { pdfLoaded.value = true }, 3000)
    }

    // 4. Start timer
    timer = setInterval(() => {
      if (timeRemaining.value > 0) {
        timeRemaining.value--
      } else {
        handleSubmit()
      }
    }, 1000)

  } catch (err: any) {
    errorMessage.value = err.response?.data?.detail || 'Failed to initialize exam. Please try again.'
    notify.error('Error', errorMessage.value)
  } finally {
    loading.value = false
  }
})

onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
})

function handleStudentFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files && input.files[0]) {
    const file = input.files[0]
    
    // Check format (PDF, Word, or JPG/PNG image)
    const ext = file.name.split('.').pop()?.toLowerCase()
    if (!ext || !['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'].includes(ext)) {
      errorMessage.value = 'Only PDF, Word, or JPG/PNG image files are allowed.'
      studentFile.value = null
      return
    }
    
    // Check size (15MB)
    if (file.size > 15 * 1024 * 1024) {
      errorMessage.value = 'File size cannot exceed 15MB.'
      studentFile.value = null
      return
    }
    
    errorMessage.value = ''
    studentFile.value = file
  }
}

async function handleAnswerSelect(questionId: string, optionId: string) {
  answers.value[questionId] = optionId
  
  // Autosave answer to backend
  if (attempt.value) {
    try {
      await assessmentService.submitAnswer(examId, attempt.value.id, {
        question_id: questionId,
        selected_option_id: optionId
      })
    } catch (err) {
      console.error('Failed to autosave answer:', err)
    }
  }
}

async function handleTextAnswerSave(questionId: string, type: 'essay' | 'fill_blank') {
  const text = answers.value[questionId] || ''
  if (attempt.value) {
    try {
      await assessmentService.submitAnswer(examId, attempt.value.id, {
        question_id: questionId,
        answer_text: text
      })
    } catch (err) {
      console.error('Failed to autosave answer:', err)
    }
  }
}

async function handleSubmit() {
  if (timer) clearInterval(timer)
  
  if (assessment.value?.is_file_based && !studentFile.value) {
    errorMessage.value = 'Please upload your answer sheet before submitting.'
    showConfirm.value = false
    return
  }

  submitting.value = true
  errorMessage.value = ''

  try {
    if (attempt.value) {
      let fileToSubmit = studentFile.value
      if (!fileToSubmit && fileBasedAnswers.value.trim() !== '') {
        const blob = new Blob([fileBasedAnswers.value], { type: 'text/plain' })
        fileToSubmit = new File([blob], 'answers.txt', { type: 'text/plain' })
      }

      await assessmentService.submitAttempt(examId, attempt.value.id, fileToSubmit || undefined)
      notify.success('Assessment Submitted', 'Your attempt has been uploaded and submitted.')
      submitted.value = true
      showConfirm.value = false
    }
  } catch (err: any) {
    errorMessage.value = err.response?.data?.error || 'Failed to submit answers.'
    notify.error('Error', errorMessage.value)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="max-w-4xl mx-auto">
    <!-- Loading State -->
    <div v-if="loading" class="text-center py-20 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl">
      <span class="animate-spin inline-block w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mb-4"></span>
      <p class="text-gray-500 dark:text-gray-400">Loading Exam Content...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="errorMessage && !assessment" class="bg-red-50 dark:bg-red-900/10 border border-red-200 dark:border-red-800/30 p-8 rounded-2xl text-center space-y-4">
      <span class="text-4xl">⚠️</span>
      <h2 class="text-xl font-bold text-red-800 dark:text-red-400">Failed to Load Assessment</h2>
      <p class="text-gray-600 dark:text-gray-400">{{ errorMessage }}</p>
      <button @click="router.push('/student/dashboard')" class="px-6 py-2.5 bg-red-600 text-white font-semibold rounded-xl">Back to Dashboard</button>
    </div>

    <!-- Submitted State -->
    <div v-else-if="submitted" class="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-12 text-center">
      <div class="w-20 h-20 mx-auto mb-6 rounded-full bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center text-4xl">🎉</div>
      <h2 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">{{ t('exam.submitted') }}</h2>
      <p v-if="assessment?.is_file_based" class="text-gray-500 mb-6">Your worksheet has been successfully uploaded and is pending teacher review/grading.</p>
      <p v-else class="text-5xl font-bold bg-gradient-to-r from-blue-600 to-emerald-600 bg-clip-text text-transparent my-6">{{ score }}%</p>
      <button @click="router.push('/student/dashboard')" class="px-8 py-3 bg-gradient-to-r from-blue-600 to-emerald-600 text-white font-semibold rounded-xl">Back to Dashboard</button>
    </div>

    <!-- Exam taking interface -->
    <template v-else-if="assessment">
      <!-- Title Header -->
      <div class="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-6 mb-6">
        <div class="flex items-center justify-between mb-2">
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">{{ assessment.title }}</h1>
          <div :class="['px-4 py-2 rounded-xl font-mono text-sm font-bold', timeRemaining < 300 ? 'bg-red-100 text-red-700 animate-pulse' : 'bg-blue-100 text-blue-700']">
            ⏱ {{ formatTime(timeRemaining) }}
          </div>
        </div>
        <p class="text-sm text-gray-600 dark:text-gray-400">{{ assessment.description }}</p>
      </div>

      <!-- FILE-BASED EXAM LAYOUT -->
      <div v-if="assessment.is_file_based" class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Left panel: Document Viewer -->
        <div class="bg-white dark:bg-gray-900 border border-gray-250 dark:border-gray-800 rounded-2xl p-6 flex flex-col h-[650px] shadow-sm">
          <div class="flex justify-between items-center mb-3">
            <h3 class="text-sm font-bold text-gray-900 dark:text-white flex items-center gap-2">
              📄 Exam Question Sheet
            </h3>
            <a v-if="assessment.file_attachment" :href="fileAttachmentUrl" target="_blank" download class="text-xs text-blue-600 hover:underline font-semibold">
              📥 Download
            </a>
          </div>

          <template v-if="assessment.file_attachment">
            <!-- PDF Viewer: use embed for best cross-origin compatibility -->
            <div class="flex-1 w-full relative rounded-xl overflow-hidden border border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-950">
              <!-- Loading overlay -->
              <div v-if="!pdfLoaded && !pdfError" class="absolute inset-0 flex flex-col items-center justify-center z-10 bg-white dark:bg-gray-950">
                <span class="animate-spin inline-block w-8 h-8 border-3 border-blue-500 border-t-transparent rounded-full mb-3"></span>
                <p class="text-xs text-gray-500 font-medium">Loading document...</p>
              </div>

              <!-- Primary: embed tag (best for PDF in most browsers) -->
              <embed 
                v-if="!pdfError"
                :src="fileAttachmentUrl + '#toolbar=1&navpanes=1&scrollbar=1'" 
                type="application/pdf"
                class="w-full h-full"
                @load="pdfLoaded = true"
              />

              <!-- Fallback: error state with direct actions -->
              <div v-if="pdfError" class="absolute inset-0 flex flex-col items-center justify-center space-y-4 p-6 text-center">
                <span class="text-4xl">📄</span>
                <p class="text-sm font-semibold text-gray-700 dark:text-gray-300">Document viewer unavailable</p>
                <p class="text-xs text-gray-500">Your browser may not support inline PDF rendering. Use the options below to view the exam sheet.</p>
                <div class="flex gap-2">
                  <a :href="fileAttachmentUrl" target="_blank" class="px-4 py-2 bg-indigo-600 text-white rounded-xl text-xs font-bold hover:bg-indigo-700 transition-colors">
                    ↗️ Open in New Tab
                  </a>
                  <a :href="fileAttachmentUrl" download class="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200 rounded-xl text-xs font-bold hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors">
                    📥 Download PDF
                  </a>
                </div>
              </div>
            </div>

            <!-- Quick action bar -->
            <div class="mt-3 flex gap-2">
              <a :href="fileAttachmentUrl" target="_blank" class="flex-1 py-2 bg-indigo-50 dark:bg-indigo-950/30 text-indigo-600 dark:text-indigo-400 rounded-xl text-xs font-bold text-center hover:bg-indigo-100 dark:hover:bg-indigo-950/50 transition-colors">
                ↗️ Open in New Tab
              </a>
              <button @click="pdfError = !pdfError" class="px-3 py-2 bg-gray-100 dark:bg-gray-800 text-gray-500 rounded-xl text-xs font-medium hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors">
                🔄 Toggle View
              </button>
            </div>
          </template>
          <p v-else class="text-sm text-amber-600 text-center my-auto">No exam sheet attachment was uploaded for this exam. Please contact your teacher.</p>
        </div>

        <!-- Right panel: Interactive Answer Entry & File upload -->
        <div class="bg-white dark:bg-gray-900 border border-gray-250 dark:border-gray-800 rounded-2xl p-6 flex flex-col justify-between shadow-sm space-y-4">
          <div class="space-y-4">
            <h3 class="text-sm font-bold text-gray-900 dark:text-white flex items-center gap-2">
              ✍️ Interactive Answer Sheet
            </h3>
            <p class="text-xs text-gray-500">Type your answers in the input box below (e.g. Q1: A, Q2: 25cm...), or upload a scanned answer worksheet.</p>
            
            <div>
              <label class="block text-xs font-semibold text-gray-600 dark:text-gray-400 mb-1">Your Written Answers</label>
              <textarea v-model="fileBasedAnswers" rows="10" placeholder="Type your answers here..." class="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-white focus:outline-none"></textarea>
            </div>

            <div>
              <label class="block text-xs font-semibold text-gray-600 dark:text-gray-400 mb-2">Or, Upload Answer File Scan</label>
              <div class="border-2 border-dashed border-gray-300 dark:border-gray-700 rounded-xl p-4 text-center hover:border-blue-500 cursor-pointer relative">
                <input type="file" @change="handleStudentFileChange" accept=".pdf,.doc,.docx,.jpg,.jpeg,.png" class="absolute inset-0 opacity-0 cursor-pointer" />
                <span class="text-2xl block mb-1">📁</span>
                <p class="text-xs font-semibold text-gray-700 dark:text-gray-300">
                  {{ studentFile ? studentFile.name : 'Choose file or drag here' }}
                </p>
                <p class="text-[10px] text-gray-500">Accepted formats: PDF, Word, JPG, PNG (Max 15MB)</p>
              </div>
            </div>
          </div>

          <div v-if="errorMessage" class="p-3 bg-red-500/10 border border-red-500/20 text-red-600 rounded-xl text-sm">
            {{ errorMessage }}
          </div>

          <button @click="showConfirm = true" :disabled="(!studentFile && fileBasedAnswers.trim() === '') || submitting"
            class="w-full py-3 bg-gradient-to-r from-emerald-600 to-blue-600 text-white font-bold rounded-xl hover:shadow-lg disabled:opacity-50 transition-all flex items-center justify-center gap-2">
            <span v-if="submitting" class="animate-spin inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full"></span>
            {{ submitting ? 'Submitting...' : 'Submit Answers' }}
          </button>
        </div>
      </div>

      <!-- INTERACTIVE EXAM LAYOUT -->
      <div v-else-if="questions.length > 0" class="space-y-6">
        <!-- Question Navigator -->
        <div class="flex flex-wrap gap-2">
          <button v-for="(q, i) in questions" :key="q.id" @click="currentIndex = i"
            :class="['w-10 h-10 rounded-xl text-sm font-bold transition-all', currentIndex === i ? 'bg-blue-600 text-white scale-110' : answers[q.id] ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30' : 'bg-gray-100 dark:bg-gray-800 text-gray-600']">
            {{ i + 1 }}
          </button>
        </div>

        <!-- Question Content -->
        <div class="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-8">
          <div class="flex items-center gap-2 mb-4">
            <span class="px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 text-xs font-medium rounded-full capitalize">{{ currentQ.question_type.replace('_', ' ') }}</span>
          </div>
          <h3 class="text-xl font-semibold text-gray-900 dark:text-white mb-6 leading-relaxed">{{ currentQ.text }}</h3>

          <!-- MCQ / True-False Options -->
          <div v-if="currentQ.options && currentQ.options.length > 0" class="space-y-3">
            <button v-for="opt in currentQ.options" :key="opt.id" @click="handleAnswerSelect(currentQ.id, opt.id)"
              :class="['w-full p-4 rounded-xl border-2 text-left transition-all', answers[currentQ.id] === opt.id ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : 'border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:text-white']">
              <span>{{ opt.text }}</span>
            </button>
          </div>

          <!-- Fill Blank / Essay -->
          <div v-else>
            <textarea v-if="currentQ.question_type === 'essay'" v-model="answers[currentQ.id]" @blur="handleTextAnswerSave(currentQ.id, 'essay')" rows="8"
              class="w-full p-4 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none resize-none"
              placeholder="Write your answer here..."></textarea>
            <input v-else v-model="answers[currentQ.id]" @blur="handleTextAnswerSave(currentQ.id, 'fill_blank')"
              class="w-full p-4 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
              placeholder="Type your answer..." />
          </div>
        </div>

        <!-- Navigation Buttons -->
        <div class="flex justify-between">
          <button @click="currentIndex = Math.max(0, currentIndex - 1)" :disabled="currentIndex === 0"
            class="px-6 py-3 bg-gray-100 dark:bg-gray-800 dark:text-white text-gray-700 font-medium rounded-xl disabled:opacity-40 hover:bg-gray-200 transition-colors">
            ← {{ t('exam.previous') }}
          </button>
          <button v-if="currentIndex < questions.length - 1" @click="currentIndex++"
            class="px-6 py-3 bg-blue-600 text-white font-medium rounded-xl hover:bg-blue-700 transition-colors">
            {{ t('exam.next') }} →
          </button>
          <button v-else @click="showConfirm = true"
            class="px-8 py-3 bg-gradient-to-r from-emerald-600 to-blue-600 text-white font-bold rounded-xl hover:shadow-lg transition-all">
            {{ t('exam.submit') }}
          </button>
        </div>
      </div>

      <!-- Fallback when no questions are present -->
      <div v-else class="text-center py-12 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl shadow-sm">
        <span class="text-3xl block mb-2">⚠️</span>
        <p class="text-gray-500 dark:text-gray-400 font-bold">No questions found</p>
        <p class="text-xs text-gray-450 mt-1">This interactive assessment does not contain any questions. Please contact your teacher.</p>
      </div>

      <!-- Confirm Modal -->
      <Teleport to="body">
        <div v-if="showConfirm" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" @click.self="showConfirm = false">
          <div class="bg-white dark:bg-gray-900 rounded-2xl p-8 max-w-sm w-full text-center">
            <p class="text-lg font-semibold text-gray-900 dark:text-white mb-4">{{ t('exam.confirm_submit') }}</p>
            <p v-if="!assessment.is_file_based" class="text-sm text-gray-500 mb-6">{{ Object.keys(answers).length }} / {{ questions.length }} questions answered</p>
            <p v-else class="text-sm text-gray-500 mb-6">Are you sure you want to upload "{{ studentFile?.name }}" as your final exam answers?</p>
            <div class="flex gap-3">
              <button @click="showConfirm = false" :disabled="submitting" class="flex-1 py-3 bg-gray-100 dark:bg-gray-800 dark:text-white rounded-xl font-medium">{{ t('common.cancel') }}</button>
              <button @click="handleSubmit" :disabled="submitting" class="flex-1 py-3 bg-gradient-to-r from-emerald-600 to-blue-600 text-white rounded-xl font-bold flex items-center justify-center gap-2">
                <span v-if="submitting" class="animate-spin inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full"></span>
                {{ t('exam.submit') }}
              </button>
            </div>
          </div>
        </div>
      </Teleport>
    </template>
  </div>
</template>
