<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useNotificationStore } from '@/stores/notification'
import { assessmentService } from '@/services/assessment.service'
import api from '@/services/api'

const { t } = useI18n()
const notify = useNotificationStore()

const form = ref({
  title: '',
  description: '',
  type: 'quiz' as 'quiz' | 'test' | 'assignment' | 'exam' | 'home_package',
  subject: '',
  classroom: '',
  questionsLimit: null as number | null,
  duration: 30,
  proctored: false,
  public: false,
  shuffle: false,
  startTime: '',
  endTime: '',
  passPct: 50,
  maxAttempts: 1,
  isFileBased: false,
  fileAttachment: null as File | null,
  weekNumber: null as number | null,
  month: '',
  academicYear: new Date().getFullYear().toString()
})

watch(() => form.value.type, (newType) => {
  if (newType === 'home_package') {
    form.value.isFileBased = true
  } else if (newType === 'exam') {
    form.value.isFileBased = false
    form.value.proctored = true
  } else if (newType === 'quiz') {
    form.value.isFileBased = false
    form.value.proctored = false
  }
})

const step = ref(1)
const loading = ref(false)
const errorMessage = ref('')

const subjects = ref<{ id: string, name: string }[]>([
  { id: 'c9a08ad2-829b-4fde-83f2-6bc86b14c01a', name: 'Mathematics' },
  { id: '89b99f22-d6b7-4bca-9d60-70bb1babcbd5', name: 'Biology' },
  { id: 'e01db9c3-708f-49ee-b8e6-8222e8cecb10', name: 'Physics' },
  { id: '93cf651e-220e-4bcd-9be5-735fd428158e', name: 'Chemistry' },
  { id: '3dc40791-d370-458d-8d26-afa63c6e2587', name: 'English' },
  { id: '0ddac904-426c-40f0-9fcf-d7af48fc6c1e', name: 'Kiswahili' },
  { id: 'dddc4f58-68ca-4b11-bc19-896b9220882a', name: 'History' },
  { id: 'c080250d-0877-4b56-bc37-40a4275a76c3', name: 'Geography' },
])

onMounted(async () => {
  try {
    const { data } = await api.get('/content/subjects/')
    let resultsList: any[] = []
    if (Array.isArray(data)) {
      resultsList = data
    } else if (data.results && Array.isArray(data.results)) {
      resultsList = data.results
    }
    if (resultsList.length > 0) {
      subjects.value = resultsList.map((s: any) => ({ id: s.id, name: s.name }))
    }
  } catch (err) {
    console.error('Failed to load subjects:', err)
  }

  // Load topics
  try {
    const { data } = await api.get('/content/topics/')
    const list = Array.isArray(data) ? data : data?.results || []
    topics.value = list.map((t: any) => ({ id: t.id, name: t.name, subject: t.subject }))
  } catch (err) {
    console.error('Failed to load topics:', err)
  }
})

function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files && input.files[0]) {
    const file = input.files[0]
    
    // Check format
    const ext = file.name.split('.').pop()?.toLowerCase()
    if (!ext || !['pdf', 'doc', 'docx'].includes(ext)) {
      errorMessage.value = 'Only PDF and Word (.doc, .docx) files are allowed.'
      form.value.fileAttachment = null
      return
    }
    
    // Check size (50MB)
    if (file.size > 50 * 1024 * 1024) {
      errorMessage.value = 'File size cannot exceed 50MB.'
      form.value.fileAttachment = null
      return
    }
    
    errorMessage.value = ''
    form.value.fileAttachment = file
  }
}

function parseError(err: any): string {
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
    return messages || 'Failed to create assessment.'
  }
  return 'Failed to create assessment.'
}

const aiCount = ref(3)
const selectedQuestionTypes = ref<string[]>(['mcq'])
const aiDifficulty = ref('medium')
const aiPrompt = ref('')
const aiLoading = ref(false)
const aiSuccessMessage = ref('')
const createdAssessmentId = ref('')
const aiProvider = ref('auto')
const selectedTopic = ref('')
const topics = ref<{ id: string, name: string }[]>([])

const aiProviders = [
  { value: 'auto', label: 'Auto (Best Available)', icon: '🤖' },
  { value: 'gemini', label: 'Google Gemini', icon: '💎' },
  { value: 'openai', label: 'OpenAI (ChatGPT)', icon: '🧠' },
  { value: 'claude', label: 'Anthropic Claude', icon: '🔮' },
]

const filteredTopics = computed(() => {
  if (!form.value.subject) return []
  return topics.value
})

const questionTypesConfig = [
  { value: 'mcq', label: 'MCQ', icon: '📝' },
  { value: 'true_false', label: 'True/False', icon: '⚖️' },
  { value: 'fill_blank', label: 'Fill Blanks', icon: '✏️' },
  { value: 'short_answer', label: 'Short Answer', icon: '💬' },
  { value: 'essay', label: 'Essay', icon: '✍️' },
  { value: 'matching', label: 'Matching', icon: '🔗' },
  { value: 'practical', label: 'Practical', icon: '🧪' }
]

function toggleQuestionType(type: string) {
  if (selectedQuestionTypes.value.includes(type)) {
    if (selectedQuestionTypes.value.length > 1) {
      selectedQuestionTypes.value = selectedQuestionTypes.value.filter(t => t !== type)
    }
  } else {
    selectedQuestionTypes.value.push(type)
  }
}

async function handleAIGenerate() {
  if (!createdAssessmentId.value) return
  
  aiLoading.value = true
  aiSuccessMessage.value = ''
  errorMessage.value = ''
  
  try {
    const res = await api.post(`/assessments/${createdAssessmentId.value}/generate-questions-ai/`, {
      question_types: selectedQuestionTypes.value,
      difficulty: aiDifficulty.value,
      count: aiCount.value,
      prompt: aiPrompt.value,
      provider: aiProvider.value,
      topic: selectedTopic.value || undefined
    })
    aiSuccessMessage.value = res.data?.message || 'Questions generated successfully!'
    notify.success('AI Generation Success', aiSuccessMessage.value)
  } catch (err: any) {
    errorMessage.value = err.response?.data?.error || 'AI generation failed.'
    notify.error('Error', errorMessage.value)
  } finally {
    aiLoading.value = false
  }
}

// ─── Question Bank Browser ───
const bankQuestions = ref<any[]>([])
const bankLoading = ref(false)
const selectedBankIds = ref<Set<string>>(new Set())
const bankLinkLoading = ref(false)
const bankLinkMessage = ref('')
const bankSearchText = ref('')
const bankFilterType = ref('')
const bankFilterDifficulty = ref('')
const showBankPanel = ref(false)

async function loadBankQuestions() {
  bankLoading.value = true
  bankQuestions.value = []
  bankLinkMessage.value = ''
  try {
    const params: Record<string, string> = {}
    if (form.value.subject) params.subject = form.value.subject
    if (bankFilterType.value) params.question_type = bankFilterType.value
    if (bankFilterDifficulty.value) params.difficulty = bankFilterDifficulty.value
    if (bankSearchText.value.trim()) params.search = bankSearchText.value.trim()

    const res = await api.get('/content/questions/', { params })
    const list = Array.isArray(res.data) ? res.data : res.data?.results || []
    bankQuestions.value = list
  } catch (err) {
    console.error('Failed to load question bank:', err)
  } finally {
    bankLoading.value = false
  }
}

function toggleBankQuestion(id: string) {
  const s = new Set(selectedBankIds.value)
  if (s.has(id)) {
    s.delete(id)
  } else {
    s.add(id)
  }
  selectedBankIds.value = s
}

async function linkSelectedQuestions() {
  if (!createdAssessmentId.value || selectedBankIds.value.size === 0) return
  bankLinkLoading.value = true
  bankLinkMessage.value = ''
  try {
    const res = await api.post(`/assessments/${createdAssessmentId.value}/add-questions/`, {
      question_ids: Array.from(selectedBankIds.value)
    })
    bankLinkMessage.value = res.data?.message || `Linked ${selectedBankIds.value.size} questions successfully.`
    notify.success('Questions Linked', bankLinkMessage.value)
    selectedBankIds.value = new Set()
  } catch (err: any) {
    bankLinkMessage.value = err.response?.data?.error || 'Failed to link questions.'
    notify.error('Error', bankLinkMessage.value)
  } finally {
    bankLinkLoading.value = false
  }
}

// ─── PDF conversion ───
const pdfConverting = ref(false)
const pdfConvertMessage = ref('')
const pdfConvertSuccess = ref(false)

async function handlePDFConvert() {
  if (!createdAssessmentId.value) return
  pdfConverting.value = true
  pdfConvertMessage.value = ''
  errorMessage.value = ''
  try {
    const res = await api.post(`/assessments/${createdAssessmentId.value}/convert-pdf-to-questions/`, {
      provider: aiProvider.value
    })
    pdfConvertSuccess.value = true
    pdfConvertMessage.value = res.data?.message || 'PDF converted successfully!'
    notify.success('PDF Conversion Success', pdfConvertMessage.value)
    // Toggle state to structured questions so Step 3 updates the UI to show the question bank/AI panels
    form.value.isFileBased = false
  } catch (err: any) {
    errorMessage.value = err.response?.data?.error || 'PDF conversion failed.'
    notify.error('Error', errorMessage.value)
  } finally {
    pdfConverting.value = false
  }
}

async function handleCreate() {
  if (form.value.isFileBased && !form.value.fileAttachment) {
    errorMessage.value = 'Please select a document file to upload.'
    return
  }

  loading.value = true
  errorMessage.value = ''

  try {
    const formData = new FormData()
    formData.append('title', form.value.title)
    formData.append('description', form.value.description)
    formData.append('assessment_type', form.value.type)
    formData.append('subject', form.value.subject)
    if (form.value.classroom) {
      formData.append('classroom', form.value.classroom)
    }
    if (form.value.questionsLimit !== null && form.value.questionsLimit !== undefined && String(form.value.questionsLimit) !== '') {
      formData.append('questions_limit', String(form.value.questionsLimit))
    }
    formData.append('duration_minutes', String(form.value.duration))
    formData.append('pass_percentage', String(form.value.passPct))
    formData.append('requires_proctoring', String(form.value.proctored))
    formData.append('shuffle_questions', String(form.value.shuffle))
    formData.append('is_public', String(form.value.public))
    formData.append('max_attempts', String(form.value.maxAttempts))
    formData.append('is_file_based', String(form.value.isFileBased))
    formData.append('status', 'published')
    
    if (form.value.type === 'home_package') {
      if (form.value.weekNumber !== null && form.value.weekNumber !== undefined && String(form.value.weekNumber) !== '') {
        formData.append('week_number', String(form.value.weekNumber))
      }
      formData.append('month', form.value.month)
      formData.append('academic_year', form.value.academicYear)
    }
    
    if (form.value.isFileBased && form.value.fileAttachment) {
      formData.append('file_attachment', form.value.fileAttachment)
    }

    const res = await assessmentService.create(formData)
    createdAssessmentId.value = (res as any)?.id || ''
    notify.success('Assessment Created', `"${form.value.title}" has been saved successfully.`)
    step.value = 3
  } catch (err: any) {
    errorMessage.value = parseError(err)
    notify.error('Error', errorMessage.value)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="max-w-3xl mx-auto space-y-6">
    <h1 class="text-2xl font-bold text-gray-900 dark:text-white">{{ t('common.create') }} Assessment</h1>

    <!-- Progress Steps -->
    <div class="flex items-center gap-2">
      <div v-for="s in 3" :key="s" :class="['flex-1 h-1.5 rounded-full transition-colors', s <= step ? 'bg-blue-600' : 'bg-gray-200 dark:bg-gray-800']"></div>
    </div>

    <!-- Step 1: Basic Info -->
    <div v-if="step === 1" class="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-8 space-y-5">
      <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Basic Information</h2>
      
      <!-- Assessment Mode Toggle -->
      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Assessment Method</label>
        <div class="grid grid-cols-2 gap-4">
          <button type="button" @click="form.isFileBased = false" :disabled="form.type === 'home_package'"
            :class="['py-3 px-4 rounded-xl border text-sm font-semibold flex items-center justify-center gap-2 transition-all disabled:opacity-40', !form.isFileBased ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 text-blue-700 font-bold shadow-sm' : 'border-gray-200 dark:border-gray-800 dark:text-white']">
            📝 Online Interactive Questions
          </button>
          <button type="button" @click="form.isFileBased = true" :disabled="form.type === 'exam'"
            :class="['py-3 px-4 rounded-xl border text-sm font-semibold flex items-center justify-center gap-2 transition-all disabled:opacity-40', form.isFileBased ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 text-blue-700 font-bold shadow-sm' : 'border-gray-200 dark:border-gray-800 dark:text-white']">
            📁 Document Upload (PDF/Word Worksheet)
          </button>
        </div>
        <p v-if="form.type === 'home_package'" class="text-[10px] text-gray-500 dark:text-gray-400 mt-1">💡 Home Packages are worksheet-based by default.</p>
        <p v-if="form.type === 'exam'" class="text-[10px] text-gray-500 dark:text-gray-400 mt-1">💡 Exams require interactive questions to support automated/manual grading and browser proctoring locks.</p>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Title</label>
        <input v-model="form.title" class="w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none" placeholder="e.g., Biology Mid-Term Exam" />
      </div>
      
      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Delivery Type</label>
        <div class="grid grid-cols-1 sm:grid-cols-5 gap-3">
          <button 
            v-for="tp in [
              { value: 'quiz' as const, label: 'Quiz', icon: '📝', desc: 'Short check, auto-graded' },
              { value: 'test' as const, label: 'Test', icon: '🧪', desc: 'Periodic evaluation' },
              { value: 'assignment' as const, label: 'Assignment', icon: '✍️', desc: 'Homework and tasks' },
              { value: 'exam' as const, label: 'Exam', icon: '🎓', desc: 'High-stakes proctored lockdown' },
              { value: 'home_package' as const, label: 'Home Package', icon: '🏠', desc: 'Weekly/monthly worksheet' }
            ]" 
            :key="tp.value" 
            type="button"
            @click="form.type = tp.value"
            :class="['p-4 rounded-2xl border text-left transition-all flex flex-col justify-between h-28', form.type === tp.value ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 text-blue-700 font-bold shadow-sm' : 'border-gray-200 dark:border-gray-800 dark:text-white hover:border-gray-300']"
          >
            <div class="flex justify-between items-center w-full">
              <span class="text-xl">{{ tp.icon }}</span>
              <span v-if="form.type === tp.value" class="text-[8px] bg-blue-600 text-white font-bold px-2 py-0.5 rounded-full">ACTIVE</span>
            </div>
            <div class="mt-2">
              <p class="text-xs font-bold leading-tight">{{ tp.label }}</p>
              <p class="text-[9px] text-gray-500 dark:text-gray-400 mt-0.5 leading-tight font-normal">{{ tp.desc }}</p>
            </div>
          </button>
        </div>
      </div>
      
      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Subject</label>
        <select v-model="form.subject" class="w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none">
          <option value="">Select subject</option>
          <option v-for="s in subjects" :key="s.id" :value="s.id">{{ s.name }}</option>
        </select>
      </div>
      
      <!-- Home Package Specific Fields -->
      <div v-if="form.type === 'home_package'" class="grid grid-cols-3 gap-4 p-4 bg-gray-50 dark:bg-gray-800/40 rounded-2xl border border-gray-100 dark:border-gray-800/80">
        <div>
          <label class="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">Academic Year</label>
          <input v-model="form.academicYear" type="text" class="w-full px-3 py-2 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-xs focus:outline-none" placeholder="e.g. 2026" />
        </div>
        <div>
          <label class="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">Month</label>
          <select v-model="form.month" class="w-full px-3 py-2 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-xs focus:outline-none">
            <option value="">Select Month</option>
            <option v-for="m in ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']" :key="m" :value="m">{{ m }}</option>
          </select>
        </div>
        <div>
          <label class="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">Week Number</label>
          <input v-model.number="form.weekNumber" type="number" min="1" max="5" class="w-full px-3 py-2 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-xs focus:outline-none" placeholder="e.g. 1" />
        </div>
      </div>
      
      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Description</label>
        <textarea v-model="form.description" rows="3" class="w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"></textarea>
      </div>

      <!-- File Upload Zone for File Based Assessment -->
      <div v-if="form.isFileBased" class="space-y-2">
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">Upload Exam Document</label>
        <div class="border-2 border-dashed border-gray-300 dark:border-gray-700 rounded-xl p-6 text-center hover:border-blue-500 transition-all cursor-pointer relative">
          <input type="file" @change="handleFileChange" accept=".pdf,.doc,.docx" class="absolute inset-0 opacity-0 cursor-pointer" />
          <div class="space-y-1">
            <span class="text-3xl">📥</span>
            <p class="text-sm font-medium text-gray-700 dark:text-gray-300">
              {{ form.fileAttachment ? form.fileAttachment.name : 'Click or drag PDF or Word file to upload' }}
            </p>
            <p class="text-xs text-gray-500">Maximum file size: 50MB (PDF, DOC, DOCX)</p>
          </div>
        </div>
      </div>

      <div v-if="errorMessage" class="p-3 bg-red-500/10 border border-red-500/20 text-red-600 rounded-xl text-sm">
        {{ errorMessage }}
      </div>

      <button @click="step = 2" :disabled="!form.title || !form.subject || (form.isFileBased && !form.fileAttachment)" class="w-full py-3 bg-blue-600 text-white font-semibold rounded-xl disabled:opacity-50 hover:bg-blue-700 transition-colors">Next: Settings →</button>
    </div>

    <!-- Step 2: Settings -->
    <div v-if="step === 2" class="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-8 space-y-5">
      <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Settings</h2>
      
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Duration (min)</label>
          <input v-model.number="form.duration" type="number" class="w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Pass %</label>
          <input v-model.number="form.passPct" type="number" class="w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Questions Limit</label>
          <input v-model.number="form.questionsLimit" type="number" placeholder="No limit (all)" class="w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none" />
        </div>
      </div>
      
      <div class="space-y-3">
        <label class="flex items-center gap-3 cursor-pointer">
          <input v-model="form.proctored" type="checkbox" class="w-5 h-5 rounded-lg border-gray-300 text-blue-600 focus:ring-blue-500" />
          <span class="text-sm text-gray-700 dark:text-gray-300">🔒 Enable AI Proctoring (webcam, face detection, browser lockdown)</span>
        </label>
        <label v-if="!form.isFileBased" class="flex items-center gap-3 cursor-pointer">
          <input v-model="form.shuffle" type="checkbox" class="w-5 h-5 rounded-lg border-gray-300 text-blue-600 focus:ring-blue-500" />
          <span class="text-sm text-gray-700 dark:text-gray-300">🔀 Shuffle questions and options</span>
        </label>
        <label class="flex items-center gap-3 cursor-pointer">
          <input v-model="form.public" type="checkbox" class="w-5 h-5 rounded-lg border-gray-300 text-blue-600 focus:ring-blue-500" />
          <span class="text-sm text-gray-700 dark:text-gray-300">🌍 Make public (accessible to all students)</span>
        </label>
      </div>

      <div v-if="errorMessage" class="p-3 bg-red-500/10 border border-red-500/20 text-red-600 rounded-xl text-sm">
        {{ errorMessage }}
      </div>

      <div class="flex gap-3">
        <button @click="step = 1" :disabled="loading" class="px-6 py-3 bg-gray-100 dark:bg-gray-800 dark:text-white rounded-xl text-sm font-medium hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors">← Back</button>
        <button @click="handleCreate" :disabled="loading" class="flex-1 py-3 bg-gradient-to-r from-blue-600 to-emerald-600 text-white font-bold rounded-xl hover:shadow-lg transition-all flex items-center justify-center gap-2">
          <span v-if="loading" class="animate-spin inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full"></span>
          {{ loading ? 'Saving...' : 'Create Assessment' }}
        </button>
      </div>
    </div>

    <!-- Step 3: Success + Question Configuration -->
    <div v-if="step === 3" class="space-y-6">
      <div class="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-8 text-center">
        <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center text-3xl">✅</div>
        <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-2">Assessment Created!</h2>
        <p class="text-gray-500 text-sm">
          {{ form.isFileBased ? 'The exam document has been uploaded. Students can now access and submit their responses.' : 'Now add questions using AI generation or by selecting from your Question Bank.' }}
        </p>
      </div>

      <!-- Question Configuration Panels for Interactive Assessments -->
      <template v-if="!form.isFileBased">

        <!-- ═══ PANEL 1: AI-Assisted Question Generation ═══ -->
        <div class="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 overflow-hidden">
          <div class="p-6 border-b border-gray-100 dark:border-gray-800">
            <h3 class="text-base font-bold text-gray-900 dark:text-white flex items-center gap-2">
              ✨ AI-Assisted Question Generation
            </h3>
            <p class="text-xs text-gray-500 mt-1">Generate syllabus-aligned questions instantly using ChatGPT, Gemini, Claude, or built-in templates.</p>
          </div>

          <div class="p-6 space-y-5">
            <!-- AI Provider Selector -->
            <div>
              <label class="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2">AI Provider</label>
              <div class="grid grid-cols-2 sm:grid-cols-4 gap-2">
                <button 
                  v-for="p in aiProviders" 
                  :key="p.value"
                  type="button"
                  @click="aiProvider = p.value"
                  :class="['px-3 py-2.5 rounded-xl border text-xs font-bold transition-all text-center flex items-center justify-center gap-1.5', aiProvider === p.value ? 'bg-violet-50 border-violet-300 text-violet-700 dark:bg-violet-950/40 dark:border-violet-800 dark:text-violet-400 shadow-sm ring-1 ring-violet-200 dark:ring-violet-900' : 'border-gray-200 hover:border-gray-400 dark:border-gray-700 dark:text-gray-300 bg-transparent']"
                >
                  <span class="text-sm">{{ p.icon }}</span>
                  {{ p.label }}
                </button>
              </div>
              <p class="text-[10px] text-gray-400 mt-1.5">💡 <strong>Auto</strong> tries Gemini → OpenAI → Claude → built-in templates. Requires API keys in server settings.</p>
            </div>

            <div class="grid grid-cols-3 gap-3">
              <div>
                <label class="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">Question Count</label>
                <input v-model.number="aiCount" type="number" min="1" max="30" class="w-full px-3 py-2 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500" />
              </div>
              <div>
                <label class="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">Difficulty</label>
                <select v-model="aiDifficulty" class="w-full px-3 py-2 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500">
                  <option value="easy">Easy</option>
                  <option value="medium">Medium</option>
                  <option value="hard">Hard</option>
                </select>
              </div>
              <div>
                <label class="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">Topic (Optional)</label>
                <select v-model="selectedTopic" class="w-full px-3 py-2 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500">
                  <option value="">All Topics</option>
                  <option v-for="t in filteredTopics" :key="t.id" :value="t.id">{{ t.name }}</option>
                </select>
              </div>
            </div>

            <div>
              <label class="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2">Question Types to Include</label>
              <div class="grid grid-cols-2 sm:grid-cols-4 gap-2">
                <button 
                  v-for="type in questionTypesConfig" 
                  :key="type.value"
                  type="button"
                  @click="toggleQuestionType(type.value)"
                  :class="['px-3 py-2 rounded-xl border text-xs font-bold transition-all text-center flex items-center justify-center gap-1.5', selectedQuestionTypes.includes(type.value) ? 'bg-indigo-50 border-indigo-300 text-indigo-700 dark:bg-indigo-950/40 dark:border-indigo-800 dark:text-indigo-400 shadow-sm' : 'border-gray-200 hover:border-gray-400 dark:border-gray-700 dark:text-gray-300 bg-transparent']"
                >
                  <span class="text-sm">{{ type.icon }}</span>
                  {{ type.label }}
                </button>
              </div>
            </div>

            <div>
              <label class="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">Custom Prompt / Focus Area (Optional)</label>
              <input v-model="aiPrompt" type="text" placeholder="e.g., Focus on chloroplast and plant respiration, or Trigonometric identities" class="w-full px-3 py-2 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500" />
            </div>

            <div v-if="aiSuccessMessage" class="p-3 bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 rounded-xl text-xs font-semibold">
              {{ aiSuccessMessage }}
            </div>

            <button @click="handleAIGenerate" :disabled="aiLoading" class="w-full py-3 bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-700 hover:to-indigo-700 text-white rounded-xl text-sm font-bold flex items-center justify-center gap-2 shadow-sm transition-all">
              <span v-if="aiLoading" class="animate-spin inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full"></span>
              {{ aiLoading ? 'Generating Questions...' : '✨ Generate Questions via AI' }}
            </button>
          </div>
        </div>

        <!-- ═══ PANEL 2: Question Bank Browser ═══ -->
        <div class="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 overflow-hidden">
          <div class="p-6 border-b border-gray-100 dark:border-gray-800 flex justify-between items-center">
            <div>
              <h3 class="text-base font-bold text-gray-900 dark:text-white flex items-center gap-2">
                📚 Question Bank Browser
              </h3>
              <p class="text-xs text-gray-500 mt-1">Browse and manually select existing questions from your question pool to add to this assessment.</p>
            </div>
            <button @click="showBankPanel = !showBankPanel; if (showBankPanel && bankQuestions.length === 0) loadBankQuestions()" 
              :class="['px-4 py-2 rounded-xl text-xs font-bold transition-all', showBankPanel ? 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300' : 'bg-indigo-600 text-white hover:bg-indigo-700']">
              {{ showBankPanel ? 'Collapse ▲' : 'Browse Questions ▼' }}
            </button>
          </div>

          <div v-if="showBankPanel" class="p-6 space-y-4">
            <!-- Filters Bar -->
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div>
                <label class="block text-[10px] font-semibold text-gray-500 mb-1">Search</label>
                <input v-model="bankSearchText" type="text" placeholder="Search question text..." class="w-full px-3 py-2 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-xs focus:outline-none focus:ring-1 focus:ring-indigo-500" />
              </div>
              <div>
                <label class="block text-[10px] font-semibold text-gray-500 mb-1">Question Type</label>
                <select v-model="bankFilterType" class="w-full px-3 py-2 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-xs focus:outline-none">
                  <option value="">All Types</option>
                  <option v-for="type in questionTypesConfig" :key="type.value" :value="type.value">{{ type.icon }} {{ type.label }}</option>
                </select>
              </div>
              <div>
                <label class="block text-[10px] font-semibold text-gray-500 mb-1">Difficulty</label>
                <select v-model="bankFilterDifficulty" class="w-full px-3 py-2 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-xs focus:outline-none">
                  <option value="">All</option>
                  <option value="easy">Easy</option>
                  <option value="medium">Medium</option>
                  <option value="hard">Hard</option>
                </select>
              </div>
              <div class="flex items-end">
                <button @click="loadBankQuestions" :disabled="bankLoading" class="w-full py-2 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-xl text-xs font-bold hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors flex items-center justify-center gap-1.5">
                  <span v-if="bankLoading" class="animate-spin inline-block w-3 h-3 border-2 border-gray-600 border-t-transparent rounded-full"></span>
                  {{ bankLoading ? 'Loading...' : '🔍 Search' }}
                </button>
              </div>
            </div>

            <!-- Results -->
            <div v-if="bankLoading" class="flex flex-col items-center justify-center py-10 space-y-2">
              <div class="animate-spin rounded-full h-8 w-8 border-2 border-indigo-600 border-t-transparent"></div>
              <p class="text-xs text-gray-500">Loading question bank...</p>
            </div>

            <div v-else-if="bankQuestions.length === 0" class="text-center py-10 space-y-1">
              <p class="text-2xl">📭</p>
              <p class="text-sm text-gray-500 font-semibold">No questions found</p>
              <p class="text-xs text-gray-400">Try adjusting your filters or create questions first.</p>
            </div>

            <div v-else class="space-y-2 max-h-[400px] overflow-y-auto pr-1">
              <div v-for="q in bankQuestions" :key="q.id" 
                @click="toggleBankQuestion(q.id)"
                :class="['p-4 rounded-xl border-2 cursor-pointer transition-all flex items-start gap-3', selectedBankIds.has(q.id) ? 'border-indigo-500 bg-indigo-50/50 dark:bg-indigo-950/20 ring-1 ring-indigo-200 dark:ring-indigo-900' : 'border-gray-100 dark:border-gray-800 hover:border-gray-300 dark:hover:border-gray-700']">
                
                <!-- Checkbox -->
                <div :class="['w-5 h-5 rounded-md border-2 flex items-center justify-center flex-shrink-0 mt-0.5 transition-colors', selectedBankIds.has(q.id) ? 'bg-indigo-600 border-indigo-600 text-white' : 'border-gray-300 dark:border-gray-600']">
                  <span v-if="selectedBankIds.has(q.id)" class="text-[10px] font-bold">✓</span>
                </div>

                <!-- Question Content -->
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2 mb-1 flex-wrap">
                    <span class="px-2 py-0.5 bg-blue-50 dark:bg-blue-950/30 text-blue-600 dark:text-blue-400 text-[10px] font-bold rounded-md uppercase">{{ q.question_type.replace('_', ' ') }}</span>
                    <span :class="['px-2 py-0.5 text-[10px] font-bold rounded-md uppercase', q.difficulty === 'easy' ? 'bg-emerald-50 text-emerald-600' : q.difficulty === 'hard' ? 'bg-red-50 text-red-600' : 'bg-amber-50 text-amber-600']">{{ q.difficulty }}</span>
                    <span class="text-[10px] text-gray-400 font-mono">{{ q.points }} pts</span>
                  </div>
                  <p class="text-sm text-gray-900 dark:text-white font-medium leading-snug">{{ q.text }}</p>
                  <div v-if="q.options && q.options.length > 0" class="flex flex-wrap gap-1.5 mt-2">
                    <span v-for="opt in q.options" :key="opt.id" 
                      :class="['px-2 py-0.5 text-[10px] rounded-md border', opt.is_correct ? 'bg-emerald-50 border-emerald-200 text-emerald-700 dark:bg-emerald-950/20 dark:text-emerald-400 font-bold' : 'border-gray-100 dark:border-gray-800 text-gray-500']">
                      {{ opt.is_correct ? '✅' : '⚪' }} {{ opt.text }}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Link Selected Button -->
            <div v-if="bankQuestions.length > 0" class="flex items-center justify-between pt-2 border-t border-gray-100 dark:border-gray-800">
              <p class="text-xs text-gray-500 font-medium">
                <span v-if="selectedBankIds.size > 0" class="text-indigo-600 font-bold">{{ selectedBankIds.size }} question{{ selectedBankIds.size > 1 ? 's' : '' }} selected</span>
                <span v-else>Click questions to select them</span>
              </p>
              <button @click="linkSelectedQuestions" :disabled="selectedBankIds.size === 0 || bankLinkLoading"
                class="px-5 py-2 bg-gradient-to-r from-emerald-600 to-blue-600 text-white rounded-xl text-xs font-bold disabled:opacity-40 hover:shadow-md transition-all flex items-center gap-1.5">
                <span v-if="bankLinkLoading" class="animate-spin inline-block w-3 h-3 border-2 border-white border-t-transparent rounded-full"></span>
                {{ bankLinkLoading ? 'Linking...' : '➕ Link Selected to Assessment' }}
              </button>
            </div>

            <div v-if="bankLinkMessage" class="p-3 bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 rounded-xl text-xs font-semibold">
              {{ bankLinkMessage }}
            </div>
          </div>
        </div>
      </template>
      <template v-else>
        <!-- ═══ PANEL: AI PDF-to-Assessment Converter ═══ -->
        <div class="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 overflow-hidden shadow-sm">
          <div class="p-6 border-b border-gray-100 dark:border-gray-800 bg-gradient-to-r from-violet-50/50 to-indigo-50/50 dark:from-violet-950/10 dark:to-indigo-950/10">
            <h3 class="text-base font-bold text-gray-900 dark:text-white flex items-center gap-2">
              ✨ AI PDF-to-Assessment Converter
            </h3>
            <p class="text-xs text-gray-500 mt-1">Extract text from your uploaded PDF worksheet and convert it into fully structured online interactive questions.</p>
          </div>

          <div class="p-6 space-y-5">
            <!-- AI Provider Selector -->
            <div>
              <label class="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2">Select AI Extraction Model</label>
              <div class="grid grid-cols-2 sm:grid-cols-4 gap-2">
                <button 
                  v-for="p in aiProviders" 
                  :key="p.value"
                  type="button"
                  @click="aiProvider = p.value"
                  :class="['px-3 py-2.5 rounded-xl border text-xs font-bold transition-all text-center flex items-center justify-center gap-1.5', aiProvider === p.value ? 'bg-violet-50 border-violet-300 text-violet-700 dark:bg-violet-950/40 dark:border-violet-800 dark:text-violet-400 shadow-sm ring-1 ring-violet-200 dark:ring-violet-900' : 'border-gray-200 hover:border-gray-400 dark:border-gray-700 dark:text-gray-300 bg-transparent']"
                >
                  <span class="text-sm">{{ p.icon }}</span>
                  {{ p.label }}
                </button>
              </div>
              <p class="text-[10px] text-gray-400 mt-1.5">💡 Model will parse layout, extract question text, options/keys, and save them to the online platform database.</p>
            </div>

            <div v-if="pdfConvertMessage" class="p-3 bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 rounded-xl text-xs font-semibold">
              {{ pdfConvertMessage }}
            </div>

            <div v-if="errorMessage" class="p-3 bg-red-500/10 border border-red-500/20 text-red-600 rounded-xl text-xs font-semibold">
              {{ errorMessage }}
            </div>

            <button 
              @click="handlePDFConvert" 
              :disabled="pdfConverting || pdfConvertSuccess" 
              class="w-full py-3 bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-700 hover:to-indigo-700 text-white rounded-xl text-sm font-bold flex items-center justify-center gap-2 shadow-sm transition-all disabled:opacity-50"
            >
              <span v-if="pdfConverting" class="animate-spin inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full"></span>
              {{ pdfConverting ? 'Converting Document...' : pdfConvertSuccess ? '✓ Converted to Interactive Assessment' : '⚡ Extract & Convert to Interactive Assessment' }}
            </button>
          </div>
        </div>
      </template>

      <div class="flex gap-3 justify-center">
        <button @click="step = 1; form.title = ''; form.fileAttachment = null; aiSuccessMessage = ''; bankLinkMessage = ''" class="px-6 py-3 bg-gray-100 dark:bg-gray-800 dark:text-white rounded-xl font-medium hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors">Create Another</button>
        <button @click="$router.push('/teacher/dashboard')" class="px-6 py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 transition-colors">Go to Dashboard</button>
      </div>
    </div>
  </div>
</template>
