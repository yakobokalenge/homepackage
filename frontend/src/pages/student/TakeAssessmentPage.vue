<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useExamStore } from '../../stores/exam'
import { useNotificationStore } from '../../stores/notification'
import { useProctoring } from '../../composables/useProctoring'
import { proctoringService } from '../../services/proctoring.service'
import QuestionRenderer from '../../components/assessment/QuestionRenderer.vue'
import QuestionNavigator from '../../components/assessment/QuestionNavigator.vue'
import ExamTimer from '../../components/assessment/ExamTimer.vue'
import ProctoringOverlay from '../../components/assessment/ProctoringOverlay.vue'

const route = useRoute()
const router = useRouter()
const examStore = useExamStore()
const notificationStore = useNotificationStore()

const assessmentId = route.params.id as string

// States
const loading = ref(true)
const preExamMode = ref(true)
const consentGiven = ref(false)
const photoCaptured = ref(false)
const photoBlob = ref<Blob | null>(null)
const photoUrl = ref('')
const verifying = ref(false)
const submitting = ref(false)

// Video refs
const setupVideo = ref<HTMLVideoElement | null>(null)
const examVideo = ref<HTMLVideoElement | null>(null)

// Proctoring Composable
const proctoring = useProctoring()
const sessionRecord = ref<any>(null)

const activePageIndex = ref(0)

// Group questions by page number
const questionsByPage = computed(() => {
  const grouped: Record<number, any[]> = {}
  examStore.questions.forEach(aq => {
    // Read page_num from metadata, default to 1 if not present
    const pageNum = aq.question?.metadata?.page_num || 1
    if (!grouped[pageNum]) {
      grouped[pageNum] = []
    }
    grouped[pageNum].push(aq)
  })
  
  // Sort by page number keys ascending
  return Object.keys(grouped)
    .map(Number)
    .sort((a, b) => a - b)
    .map(pageNum => ({
      pageNum,
      questions: grouped[pageNum]
    }))
})

const currentPage = computed(() => {
  if (questionsByPage.value.length === 0) return null
  return questionsByPage.value[activePageIndex.value] || null
})

const isFirstPage = computed(() => {
  return activePageIndex.value === 0
})

const isLastPage = computed(() => {
  return activePageIndex.value === questionsByPage.value.length - 1
})

function prevPage() {
  if (!isFirstPage.value) {
    activePageIndex.value--
  }
}

function nextPage() {
  if (!isLastPage.value) {
    activePageIndex.value++
  }
}

// Watch question selection from the navigator to switch to the correct page
watch(() => examStore.activeQuestionIndex, (newVal) => {
  const targetQuestion = examStore.questions[newVal]
  if (targetQuestion) {
    const targetPageNum = targetQuestion.question?.metadata?.page_num || 1
    const pageIndex = questionsByPage.value.findIndex(p => p.pageNum === targetPageNum)
    if (pageIndex !== -1 && pageIndex !== activePageIndex.value) {
      activePageIndex.value = pageIndex
    }
  }
})

async function loadExamDetails() {
  loading.value = true
  try {
    await examStore.startExam(assessmentId)
    // If not proctored, skip pre-exam camera consent setup steps
    if (!examStore.assessment?.is_proctored) {
      preExamMode.value = false
    } else {
      // Start camera for identity verification pre-exam
      setTimeout(async () => {
        if (setupVideo.value) {
          try {
            const stream = await proctoring.recorder.startCamera(true)
            setupVideo.value.srcObject = stream
            setupVideo.value.play()
          } catch {
            notificationStore.error('Camera or Microphone device blocked/unavailable.')
          }
        }
      }, 500)
    }
  } catch (err: any) {
    notificationStore.error(err.response?.data?.error || 'Failed to start assessment.')
    router.push('/student/assessments')
  } finally {
    loading.value = false
  }
}

// Pre-exam photos capture
async function handleCapturePhoto() {
  if (!setupVideo.value) return
  try {
    const blob = await proctoring.recorder.capturePhoto(setupVideo.value)
    photoBlob.value = blob
    photoUrl.value = URL.createObjectURL(blob)
    photoCaptured.value = true
  } catch (err) {
    notificationStore.error('Failed to capture verification photo.')
  }
}

// Start proctored exam attempt
async function handleStartProctoredExam() {
  if (!consentGiven.value || !photoBlob.value || !examStore.currentAttempt) return
  
  verifying.value = true
  try {
    // 1. Grant backend consent
    const session = await proctoringService.giveConsent(examStore.currentAttempt.id)
    sessionRecord.value = session
    
    // 2. Upload verification photo to backend
    await proctoringService.verifyIdentity(session.id, photoBlob.value)
    
    // 3. Stop pre-exam setup camera
    proctoring.recorder.stopCamera()
    
    // 4. Start proctoring engine with active session ID
    preExamMode.value = false
    
    setTimeout(async () => {
      if (examVideo.value && sessionRecord.value && examStore.assessment) {
        const config = await proctoringService.getConfig(assessmentId)
        await proctoring.startProctoring(sessionRecord.value.id, config, examVideo.value)
      }
    }, 500)
    
    notificationStore.success('Exam started. Screen lockdown active.')
  } catch (err: any) {
    notificationStore.error(err.response?.data?.error || 'Verification flow failed. Please retry.')
  } finally {
    verifying.value = false
  }
}

// Answer changes autosave
function handleAnswerChange(questionId: string, answerData: any) {
  examStore.updateAnswer(questionId, answerData)
}

// File uploading essay attachment
async function handleFileUpload(questionId: string, file: File) {
  try {
    await examStore.uploadFileAnswer(questionId, file)
    notificationStore.success('File response uploaded successfully.')
  } catch {
    notificationStore.error('Failed to upload file response.')
  }
}

// Final Submit
async function handleSubmitExam() {
  if (!confirm('Are you sure you want to submit your assessment? This will finalize your attempt.')) return
  
  submitting.value = true
  try {
    proctoring.stopProctoring()
    const attempt = await examStore.submitExam()
    notificationStore.success('Assessment submitted successfully.')
    router.push(`/student/attempts/${attempt?.id}/result`)
  } catch {
    notificationStore.error('Submission failed.')
  } finally {
    submitting.value = false
  }
}

onMounted(loadExamDetails)

onUnmounted(() => {
  proctoring.stopProctoring()
  examStore.stopTimer()
})
</script>

<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-950 flex flex-col justify-between">
    <!-- Loading Screen -->
    <div v-if="loading" class="flex-1 flex flex-col items-center justify-center p-6">
      <span class="animate-spin inline-block w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mb-3"></span>
      <p class="text-xs text-gray-500">Preparing assessment workstation...</p>
    </div>

    <!-- PRE-EXAM PROCTORING SETUP WIZARD -->
    <div v-else-if="preExamMode && examStore.assessment?.is_proctored" class="flex-1 flex items-center justify-center p-6">
      <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 max-w-lg w-full shadow-xl space-y-6">
        <div class="text-center space-y-2">
          <span class="text-3xl block">🛡️</span>
          <h2 class="text-lg font-bold text-gray-900 dark:text-white">Proctoring Identity Verification</h2>
          <p class="text-xs text-gray-500">This assessment requires webcam proctoring for academic integrity.</p>
        </div>

        <!-- Camera feed preview -->
        <div class="aspect-video bg-black rounded-xl overflow-hidden relative flex items-center justify-center border">
          <video v-show="!photoCaptured" ref="setupVideo" class="w-full h-full object-contain" muted></video>
          <img v-show="photoCaptured" :src="photoUrl" class="w-full h-full object-contain" />
          
          <button
            v-if="!photoCaptured"
            @click="handleCapturePhoto"
            class="absolute bottom-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-[10px] font-bold rounded-xl shadow-md"
          >
            📸 Capture Photo
          </button>
          <button
            v-else
            @click="photoCaptured = false; photoUrl = ''; photoBlob = null"
            class="absolute bottom-4 px-4 py-2 bg-gray-700 hover:bg-gray-800 text-white text-[10px] font-bold rounded-xl shadow-md"
          >
            🔄 Retake Photo
          </button>
        </div>

        <!-- Consent checklist checkboxes -->
        <div class="space-y-3 p-4 bg-gray-50 dark:bg-gray-950 rounded-2xl border">
          <label class="flex items-start gap-2.5 cursor-pointer text-[11px] text-gray-600 dark:text-gray-400 font-medium leading-relaxed">
            <input type="checkbox" v-model="consentGiven" class="rounded border-gray-300 text-blue-650 focus:ring-blue-500 mt-0.5" />
            <span>I consent to webcam stream recording, microphone voice VAD audio tracking, and browser lockdown fullscreen enforcement for the duration of this exam attempt.</span>
          </label>
        </div>

        <button
          @click="handleStartProctoredExam"
          :disabled="!consentGiven || !photoCaptured || verifying"
          class="w-full py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-bold text-xs rounded-xl shadow-md flex items-center justify-center gap-2"
        >
          <span v-if="verifying" class="animate-spin inline-block w-3 h-3 border-2 border-white border-t-transparent rounded-full"></span>
          Verify Identity & Start Exam
        </button>
      </div>
    </div>

    <!-- ACTIVE WORKSPACE INTERACTION MODE -->
    <template v-else-if="examStore.assessment">
      <!-- Floating Proctoring Webcam preview Overlay -->
      <ProctoringOverlay :proctoring="proctoring" :videoRef="examVideo">
        <video ref="examVideo" class="w-full h-full object-contain" muted></video>
      </ProctoringOverlay>

      <!-- Exam Slim Header -->
      <header class="bg-white dark:bg-gray-900 border-b border-gray-250 dark:border-gray-800 px-6 py-4 flex items-center justify-between sticky top-0 z-30 shadow-sm">
        <div class="min-w-0">
          <h1 class="text-sm md:text-base font-bold text-gray-900 dark:text-white truncate">{{ examStore.assessment.title }}</h1>
          <span class="text-[10px] text-gray-500">Attempt #{{ examStore.currentAttempt?.attempt_number }}</span>
        </div>
        <div class="flex items-center gap-4">
          <ExamTimer />
          <button
            @click="handleSubmitExam"
            :disabled="submitting"
            class="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-xl shadow-md flex items-center gap-1"
          >
            <span v-if="submitting" class="animate-spin inline-block w-3 h-3 border-2 border-white border-t-transparent rounded-full"></span>
            Submit Assessment
          </button>
        </div>
      </header>

      <!-- Central exam taking workspace -->
      <div class="flex-1 flex flex-col md:flex-row min-w-0">
        <!-- Sidebar Navigation -->
        <aside class="w-full md:w-60 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 p-6 flex flex-col justify-between flex-shrink-0">
          <div class="space-y-6">
            <QuestionNavigator />
          </div>
          
          <div class="pt-4 border-t border-gray-150 dark:border-gray-800 text-[10px] text-gray-500 font-bold">
            <span v-if="examStore.isSaving" class="text-blue-500 animate-pulse">Saving response changes...</span>
            <span v-else-if="examStore.saveError" class="text-red-500">{{ examStore.saveError }}</span>
            <span v-else class="text-emerald-600">✓ All responses saved</span>
          </div>
        </aside>

        <!-- Main Page-wise Details renderer body -->
        <main class="flex-1 p-6 overflow-y-auto max-w-3xl mx-auto w-full space-y-6">
          <div v-if="currentPage" class="space-y-8">
            <!-- Header for Page -->
            <div class="border-b border-gray-200 dark:border-gray-800 pb-3 flex items-center justify-between">
              <h2 class="text-xs font-bold text-gray-500 uppercase tracking-wider">
                Worksheet Page {{ currentPage.pageNum }} of {{ questionsByPage.length }}
              </h2>
            </div>
            
            <!-- List of Questions on this Page -->
            <div 
              v-for="aq in currentPage.questions" 
              :key="aq.id"
              class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm space-y-4"
            >
              <div class="flex items-center justify-between pb-2 border-b border-gray-155 dark:border-gray-800">
                <span class="text-[10px] font-bold text-gray-500 uppercase tracking-wider">
                  Question {{ examStore.questions.indexOf(aq) + 1 }}
                </span>
                <span class="px-1.5 py-0.5 bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 text-[9px] font-bold rounded uppercase">
                  {{ aq.question.question_type }}
                </span>
              </div>
              <QuestionRenderer
                :question="aq.question"
                :modelValue="examStore.getAnswerForQuestion(aq.question.id)"
                @update:modelValue="handleAnswerChange(aq.question.id, $event)"
                @upload-file="handleFileUpload(aq.question.id, $event)"
              />
            </div>
          </div>

          <!-- Bottom Page-wise Prev/Next pagination -->
          <div class="mt-8 flex items-center justify-between gap-4">
            <button
              @click="prevPage"
              :disabled="isFirstPage"
              class="px-4 py-2 border rounded-xl bg-white dark:bg-gray-900 text-gray-700 dark:text-gray-300 font-bold text-xs disabled:opacity-30 shadow-sm"
            >
              ◀ Previous Page
            </button>
            
            <button
              v-if="!isLastPage"
              @click="nextPage"
              class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl shadow-md"
            >
              Next Page ▶
            </button>
            <button
              v-else
              @click="handleSubmitExam"
              :disabled="submitting"
              class="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-xl shadow-md"
            >
              Finalize & Submit
            </button>
          </div>
        </main>
      </div>
    </template>
  </div>
</template>
