<script setup lang="ts">
import { ref, onUnmounted } from 'vue'
import api from '../../services/api'
import { useNotificationStore } from '../../stores/notification'

const props = defineProps<{
  subjectId: string
}>()

const emit = defineEmits(['staged-ready', 'error', 'file-selected'])

const notificationStore = useNotificationStore()

const isDragActive = ref(false)
const loading = ref(false)
const progress = ref(0)
const fileName = ref('')
const jobStatusText = ref('Initializing...')

let pollInterval: any = null

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval)
})

async function uploadFile(file: File) {
  const extension = file.name.split('.').pop()?.toLowerCase() || ''
  const allowedExtensions = ['pdf', 'docx', 'doc', 'csv', 'xlsx', 'xls']
  
  if (!allowedExtensions.includes(extension)) {
    emit('error', 'Only PDF, Word (.docx), CSV, or Excel (.xlsx) documents are supported.')
    return
  }

  loading.value = true
  progress.value = 5
  fileName.value = file.name
  jobStatusText.value = 'Uploading document...'

  try {
    // 1. Emit file selection object URL if it's a PDF for resemblance view
    if (extension === 'pdf') {
      emit('file-selected', URL.createObjectURL(file))
    } else {
      emit('file-selected', '') // clear resemblance pane for non-PDFs
    }

    // 2. Upload file to backend
    const formData = new FormData()
    formData.append('file', file)
    formData.append('subject', props.subjectId)

    const res = await api.post('/assessments/assessments/extract_document/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    const job = res.data
    progress.value = job.progress || 10
    
    if (job.status === 'completed') {
      // Inline completed
      await fetchStagedQuestionsAndEmit(job.id)
    } else {
      // Async completed - start polling
      startPolling(job.id)
    }

  } catch (err: any) {
    console.error('File parsing failed:', err)
    emit('error', err.response?.data?.error || 'Failed to parse and upload document.')
    loading.value = false
    progress.value = 0
  }
}

function startPolling(jobId: string) {
  jobStatusText.value = 'Parsing document in background...'
  
  pollInterval = setInterval(async () => {
    try {
      const res = await api.get(`/assessments/extraction-jobs/${jobId}/`)
      const job = res.data
      progress.value = job.progress || progress.value
      
      if (job.status === 'processing') {
        jobStatusText.value = `Extracting question content (${progress.value}%)...`
      } else if (job.status === 'completed') {
        clearInterval(pollInterval)
        pollInterval = null
        jobStatusText.value = 'Extraction complete! Loading staging questions...'
        await fetchStagedQuestionsAndEmit(jobId)
      } else if (job.status === 'failed') {
        clearInterval(pollInterval)
        pollInterval = null
        emit('error', job.error_message || 'Background parsing failed.')
        loading.value = false
        progress.value = 0
      }
    } catch (err) {
      console.error('Polling job status failed:', err)
    }
  }, 2000) // Poll every 2 seconds
}

async function fetchStagedQuestionsAndEmit(jobId: string) {
  try {
    const res = await api.get(`/assessments/staged-questions/?job=${jobId}`)
    const questions = Array.isArray(res.data) ? res.data : (res.data?.results || [])
    emit('staged-ready', { questions, jobId })
  } catch (err) {
    console.error('Fetching staged questions failed:', err)
    emit('error', 'Failed to retrieve extracted staging questions.')
  } finally {
    loading.value = false
    progress.value = 0
  }
}

function handleDrop(e: DragEvent) {
  isDragActive.value = false
  if (e.dataTransfer && e.dataTransfer.files.length > 0) {
    uploadFile(e.dataTransfer.files[0])
  }
}

function handleFileInput(e: Event) {
  const target = e.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    uploadFile(target.files[0])
  }
}
</script>

<template>
  <div class="space-y-4">
    <div
      @dragover.prevent="isDragActive = true"
      @dragleave.prevent="isDragActive = false"
      @drop.prevent="handleDrop"
      :class="[
        isDragActive
          ? 'border-blue-500 bg-blue-50/30 dark:bg-blue-950/20 ring-2 ring-blue-400'
          : 'border-gray-300 dark:border-gray-700 hover:border-gray-400 dark:hover:border-gray-600',
        'border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all duration-200 bg-white dark:bg-gray-900 shadow-sm relative overflow-hidden group'
      ]"
    >
      <!-- Uploading/Polling progress overlay -->
      <div v-if="loading" class="absolute inset-0 bg-white/95 dark:bg-gray-950/95 flex flex-col items-center justify-center p-6 z-10 transition-all">
        <span class="animate-spin inline-block w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mb-3"></span>
        <p class="text-xs font-bold text-gray-700 dark:text-gray-300">{{ jobStatusText }}</p>
        
        <!-- Progress bar -->
        <div class="w-48 bg-gray-200 dark:bg-gray-800 rounded-full h-1.5 mt-3 overflow-hidden">
          <div class="bg-blue-600 h-1.5 rounded-full transition-all duration-300" :style="{ width: `${progress}%` }"></div>
        </div>
        <p class="text-[9px] text-gray-400 mt-1.5">{{ progress }}% complete</p>
        
        <p class="text-[10px] text-gray-500 mt-3 max-w-[240px] truncate">{{ fileName }}</p>
      </div>

      <input type="file" @change="handleFileInput" class="hidden" id="doc-file-input" accept=".pdf,.docx,.doc,.csv,.xlsx,.xls" />
      <label for="doc-file-input" class="cursor-pointer block space-y-3">
        <span class="text-3xl block group-hover:scale-110 transition-transform">📁</span>
        <div>
          <p class="text-xs font-bold text-gray-700 dark:text-gray-300">Drag & Drop Worksheet/Document</p>
          <p class="text-[10px] text-gray-500 mt-0.5">or click to browse local files (PDF, Word, CSV, Excel)</p>
        </div>
      </label>
    </div>
  </div>
</template>
