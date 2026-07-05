<script setup lang="ts">
import { ref, onMounted } from 'vue'
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
  fileAttachment: null as File | null
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
const aiType = ref('mcq')
const aiDifficulty = ref('medium')
const aiPrompt = ref('')
const aiLoading = ref(false)
const aiSuccessMessage = ref('')
const createdAssessmentId = ref('')

async function handleAIGenerate() {
  if (!createdAssessmentId.value) return
  
  aiLoading.value = true
  aiSuccessMessage.value = ''
  errorMessage.value = ''
  
  try {
    const res = await api.post(`/assessments/${createdAssessmentId.value}/generate-questions-ai/`, {
      question_type: aiType.value,
      difficulty: aiDifficulty.value,
      count: aiCount.value,
      prompt: aiPrompt.value
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
          <button type="button" @click="form.isFileBased = false"
            :class="['py-3 px-4 rounded-xl border text-sm font-semibold flex items-center justify-center gap-2 transition-all', !form.isFileBased ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 text-blue-700' : 'border-gray-200 dark:border-gray-800 dark:text-white']">
            📝 Online Quiz / Exam
          </button>
          <button type="button" @click="form.isFileBased = true"
            :class="['py-3 px-4 rounded-xl border text-sm font-semibold flex items-center justify-center gap-2 transition-all', form.isFileBased ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 text-blue-700' : 'border-gray-200 dark:border-gray-800 dark:text-white']">
            📁 Document Upload (PDF/Word)
          </button>
        </div>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Title</label>
        <input v-model="form.title" class="w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none" placeholder="e.g., Biology Mid-Term Exam" />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Type</label>
        <div class="grid grid-cols-3 sm:grid-cols-5 gap-2">
          <button v-for="tp in ['quiz', 'test', 'assignment', 'exam', 'home_package'] as const" :key="tp" @click="form.type = tp"
            :class="['py-2 px-3 rounded-xl border text-sm font-medium capitalize transition-all', form.type === tp ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 text-blue-700' : 'border-gray-200 dark:border-gray-700 dark:text-white']">
            {{ tp.replace('_', ' ') }}
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

    <!-- Step 3: Success -->
    <div v-if="step === 3" class="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-12 text-center">
      <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center text-3xl">✅</div>
      <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-2">Assessment Created!</h2>
      <p class="text-gray-500 mb-6">
        {{ form.isFileBased ? 'The exam document has been uploaded. Students can now access and submit their responses.' : 'You can now configure interactive questions using AI assistance.' }}
      </p>

      <!-- AI Assisted Question Generation Panel for Interactive Assessments -->
      <div v-if="!form.isFileBased" class="mt-8 p-6 bg-gray-50 dark:bg-gray-800/40 border border-gray-100 dark:border-gray-800/80 rounded-2xl text-left space-y-4 max-w-xl mx-auto mb-8">
        <div>
          <h3 class="text-md font-bold text-gray-900 dark:text-white flex items-center gap-2">
            ✨ AI-Assisted Question Generation
          </h3>
          <p class="text-xs text-gray-500 mt-1">Populate this assessment with randomized syllabus-aligned questions instantly.</p>
        </div>

        <div class="grid grid-cols-3 gap-3">
          <div>
            <label class="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">Question Count</label>
            <input v-model.number="aiCount" type="number" min="1" max="10" class="w-full px-3 py-2 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:outline-none" />
          </div>
          <div>
            <label class="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">Type</label>
            <select v-model="aiType" class="w-full px-3 py-2 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:outline-none">
              <option value="mcq">MCQ</option>
              <option value="short_answer">Short Answer</option>
              <option value="essay">Essay</option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">Difficulty</label>
            <select v-model="aiDifficulty" class="w-full px-3 py-2 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:outline-none">
              <option value="easy">Easy</option>
              <option value="medium">Medium</option>
              <option value="hard">Hard</option>
            </select>
          </div>
        </div>

        <div>
          <label class="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">Custom Prompt / Focus Area (Optional)</label>
          <input v-model="aiPrompt" type="text" placeholder="e.g., Focus on chloroplast and plant respiration" class="w-full px-3 py-2 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:outline-none" />
        </div>

        <div v-if="aiSuccessMessage" class="p-3 bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 rounded-xl text-xs font-semibold">
          {{ aiSuccessMessage }}
        </div>

        <button @click="handleAIGenerate" :disabled="aiLoading" class="w-full py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-semibold flex items-center justify-center gap-2">
          <span v-if="aiLoading" class="animate-spin inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full"></span>
          {{ aiLoading ? 'Generating Questions...' : 'Generate Questions via AI' }}
        </button>
      </div>

      <div class="flex gap-3 justify-center">
        <button @click="step = 1; form.title = ''; form.fileAttachment = null; aiSuccessMessage = ''" class="px-6 py-3 bg-gray-100 dark:bg-gray-800 dark:text-white rounded-xl font-medium hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors">Create Another</button>
        <button @click="$router.push('/teacher/dashboard')" class="px-6 py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 transition-colors">Go to Dashboard</button>
      </div>
    </div>
  </div>
</template>
