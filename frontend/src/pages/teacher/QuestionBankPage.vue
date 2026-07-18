<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import api from '../../services/api'
import { useNotificationStore } from '../../stores/notification'

const router = useRouter()
const notificationStore = useNotificationStore()

// State variables
const loadingBanks = ref(false)
const loadingQuestions = ref(false)
const questionBanks = ref<any[]>([])
const selectedBankId = ref<string>('')
const questionsList = ref<any[]>([])

// Filter options
const subjectsList = ref<any[]>([])
const classroomsList = ref<any[]>([])
const topicsList = ref<any[]>([])
const filterSubject = ref('')
const filterTopic = ref('')
const filterType = ref('')
const filterDifficulty = ref('')
const filterStatus = ref('')
const searchKeyword = ref('')

// Bank Creation & File Import
const newBankName = ref('')
const newBankDesc = ref('')
const newBankSubject = ref('')
const showCreateBankModal = ref(false)
const showImportModal = ref(false)
const importingFile = ref<File | null>(null)
const importSaving = ref(false)

// Auto-generation Exam Modal
const showGenerateModal = ref(false)
const genTitle = ref('Auto-Generated Term Test')
const genClassroom = ref('')
const genTotal = ref(10)
const genEasy = ref(3)
const genMedium = ref(5)
const genHard = ref(2)
const genDuration = ref(60)
const genSaving = ref(false)

// Rejection Feedback Modal
const showRejectModal = ref(false)
const rejectQuestionId = ref('')
const rejectFeedback = ref('')
const rejectSaving = ref(false)

// User info
const userRole = ref('')

async function fetchUserInfo() {
  try {
    const res = await api.get('/accounts/profile/')
    userRole.value = res.data.role
  } catch (err) {
    console.error('Failed to get user profile:', err)
  }
}

async function loadBanks() {
  loadingBanks.value = true
  try {
    const res = await api.get('/content/question-banks/')
    questionBanks.value = Array.isArray(res.data) ? res.data : res.data.results || []
  } catch (err) {
    notificationStore.error('Failed to load question banks.')
  } finally {
    loadingBanks.value = false
  }
}

async function loadQuestions() {
  loadingQuestions.value = true
  try {
    let url = '/content/questions/'
    const params: Record<string, any> = {}
    
    if (selectedBankId.value) {
      // Load specific bank details
      const bankRes = await api.get(`/content/question-banks/${selectedBankId.value}/`)
      questionsList.value = bankRes.data.questions_detail || []
      loadingQuestions.value = false
      return
    }

    // Apply filters for global bank list
    if (filterSubject.value) params.subject = filterSubject.value
    if (filterTopic.value) params.topic = filterTopic.value
    if (filterType.value) params.question_type = filterType.value
    if (filterDifficulty.value) params.difficulty = filterDifficulty.value
    if (filterStatus.value) params.status = filterStatus.value
    if (searchKeyword.value) params.search = searchKeyword.value

    const res = await api.get(url, { params })
    questionsList.value = Array.isArray(res.data) ? res.data : res.data.results || []
  } catch (err) {
    notificationStore.error('Failed to load questions list.')
  } finally {
    loadingQuestions.value = false
  }
}

async function loadMetadata() {
  try {
    const subRes = await api.get('/content/subjects/')
    subjectsList.value = Array.isArray(subRes.data) ? subRes.data : subRes.data.results || []

    const clsRes = await api.get('/schools/classrooms/')
    classroomsList.value = Array.isArray(clsRes.data) ? clsRes.data : clsRes.data.results || []
  } catch (err) {
    console.error('Failed to load filter metadata:', err)
  }
}

// Watch subject to load topics dynamically
watch(filterSubject, async (newVal) => {
  filterTopic.value = ''
  if (!newVal) {
    topicsList.value = []
    return
  }
  try {
    const res = await api.get('/content/topics/', { params: { subject: newVal } })
    topicsList.value = Array.isArray(res.data) ? res.data : res.data.results || []
  } catch (err) {
    console.error('Failed to load topics:', err)
  }
})

// Trigger reload on filter/bank select changes
watch([selectedBankId, filterSubject, filterTopic, filterType, filterDifficulty, filterStatus], () => {
  loadQuestions()
})

// Search debounce / keyword watch
let searchTimer: any = null
watch(searchKeyword, () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    loadQuestions()
  }, 400)
})

async function handleCreateBank() {
  if (!newBankName.value || !newBankSubject.value) {
    notificationStore.warning('Name and Subject are required.')
    return
  }

  try {
    await api.post('/content/question-banks/', {
      name: newBankName.value,
      description: newBankDesc.value,
      subject: newBankSubject.value
    })
    notificationStore.success(`Question bank "${newBankName.value}" created successfully.`)
    newBankName.value = ''
    newBankDesc.value = ''
    newBankSubject.value = ''
    showCreateBankModal.value = false
    loadBanks()
  } catch (err) {
    notificationStore.error('Failed to create question bank.')
  }
}

// Export Bank Handler
async function handleExportBank(bankId: string, format: string) {
  try {
    notificationStore.info(`Preparing export file (${format.toUpperCase()})...`)
    const res = await api.get(`/content/question-banks/${bankId}/export_bank/`, {
      params: { format },
      responseType: format === 'json' ? 'json' : 'blob'
    })
    
    // Create download link
    const blob = format === 'json' ? new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' }) : res.data
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    
    // Find bank name
    const bank = questionBanks.value.find(b => b.id === bankId)
    const bankName = bank ? bank.name.replace(/\s+/g, '_') : 'Question_Bank'
    
    link.setAttribute('download', `${bankName}.${format === 'xlsx' ? 'xlsx' : format === 'docx' ? 'docx' : 'json'}`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    notificationStore.success('Download started.')
  } catch (err) {
    notificationStore.error('Failed to export question bank.')
  }
}

// Import File Select Handler
function selectImportFile(event: any) {
  const file = event.target.files[0]
  if (file) {
    importingFile.value = file
  }
}

// Upload File Questions Handler
async function handleImportQuestions() {
  if (!selectedBankId.value) {
    notificationStore.warning('Please select a Question Bank from the left sidebar list first.')
    return
  }
  if (!importingFile.value) {
    notificationStore.warning('Please select a file to import.')
    return
  }

  const formData = new FormData()
  formData.append('file', importingFile.value)

  importSaving.value = true
  try {
    const res = await api.post(`/content/question-banks/${selectedBankId.value}/import_questions/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    notificationStore.success(res.data.message || 'Questions imported successfully.')
    showImportModal.value = false
    importingFile.value = null
    loadQuestions()
    loadBanks()
  } catch (err: any) {
    notificationStore.error(err.response?.data?.error || 'Failed to import questions.')
  } finally {
    importSaving.value = false
  }
}

// Auto-generation assessment builder
async function handleAutoGenerateExam() {
  if (genTotal.value !== (Number(genEasy.value) + Number(genMedium.value) + Number(genHard.value))) {
    notificationStore.warning('Easy, Medium and Hard question count sum must match the Total questions count.')
    return
  }

  genSaving.value = true
  try {
    const payload = {
      subject: filterSubject.value,
      classroom: genClassroom.value || null,
      total_questions: genTotal.value,
      easy_count: genEasy.value,
      medium_count: genMedium.value,
      hard_count: genHard.value,
      title: genTitle.value,
      time_limit_minutes: genDuration.value
    }

    const res = await api.post('/content/question-banks/auto_generate_exam/', payload)
    notificationStore.success(res.data.message)
    showGenerateModal.value = false
    // Redirect to assessments list where the new draft is listed
    router.push('/teacher/assessments')
  } catch (err: any) {
    notificationStore.error(err.response?.data?.error || 'Failed to generate assessment.')
  } finally {
    genSaving.value = false
  }
}

// HOD Workflows (Approve / Reject)
async function handleApproveQuestion(qId: string) {
  try {
    await api.post(`/content/questions/${qId}/approve/`)
    notificationStore.success('Question approved and published successfully.')
    loadQuestions()
  } catch (err) {
    notificationStore.error('Failed to approve question.')
  }
}

function openRejectModal(qId: string) {
  rejectQuestionId.value = qId
  rejectFeedback.value = ''
  showRejectModal.value = true
}

async function handleRejectQuestion() {
  if (!rejectQuestionId.value) return
  
  rejectSaving.value = true
  try {
    await api.post(`/content/questions/${rejectQuestionId.value}/reject/`, {
      feedback: rejectFeedback.value
    })
    notificationStore.success('Question rejected.')
    showRejectModal.value = false
    loadQuestions()
  } catch (err) {
    notificationStore.error('Failed to reject question.')
  } finally {
    rejectSaving.value = false
  }
}

onMounted(() => {
  fetchUserInfo()
  loadBanks()
  loadQuestions()
  loadMetadata()
})
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Question Library Bank</h1>
        <p class="text-sm text-gray-500 mt-1">Manage reusable questions, review pending curriculum worksheets, and auto-generate assessments.</p>
      </div>
      <div class="flex items-center gap-3">
        <button
          v-if="filterSubject"
          @click="showGenerateModal = true"
          class="px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-xl shadow-md flex items-center gap-1.5 transition-all"
        >
          🤖 Auto Exam Generator
        </button>
        <button
          @click="showCreateBankModal = true"
          class="px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl shadow-md flex items-center gap-1.5 transition-all"
        >
          ➕ Create Question Bank
        </button>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
      
      <!-- Left Column: Question Banks List -->
      <div class="lg:col-span-4 space-y-4">
        <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-4 shadow-sm">
          <h2 class="text-sm font-bold text-gray-800 dark:text-white mb-3 flex items-center gap-2">
            🗂️ Question Banks
          </h2>

          <div v-if="loadingBanks" class="space-y-2">
            <div v-for="i in 3" :key="i" class="h-12 bg-gray-100 dark:bg-gray-800 rounded-xl animate-pulse"></div>
          </div>

          <div v-else class="space-y-2 max-h-[400px] overflow-y-auto pr-1">
            <div
              @click="selectedBankId = ''"
              :class="[!selectedBankId ? 'bg-blue-50 dark:bg-blue-900/30 border-blue-200 dark:border-blue-800 text-blue-600' : 'bg-gray-50 dark:bg-gray-850/50 border-gray-150 dark:border-gray-800 text-gray-700 dark:text-gray-300']"
              class="p-3 border rounded-xl cursor-pointer hover:border-blue-400 transition-all flex items-center justify-between"
            >
              <div class="flex flex-col">
                <span class="text-xs font-bold">All Shared Questions</span>
                <span class="text-[9px] text-gray-500 mt-0.5">Global repository</span>
              </div>
              <span class="text-[10px] font-bold px-1.5 py-0.5 bg-white dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700">All</span>
            </div>

            <div
              v-for="bank in questionBanks"
              :key="bank.id"
              @click="selectedBankId = bank.id"
              :class="[selectedBankId === bank.id ? 'bg-blue-50 dark:bg-blue-900/30 border-blue-200 dark:border-blue-800 text-blue-600' : 'bg-gray-50 dark:bg-gray-850/50 border-gray-150 dark:border-gray-800 text-gray-700 dark:text-gray-300']"
              class="p-3 border rounded-xl cursor-pointer hover:border-blue-400 transition-all flex flex-col gap-2"
            >
              <div class="flex items-start justify-between gap-2">
                <div class="flex flex-col">
                  <span class="text-xs font-bold truncate max-w-[180px]">{{ bank.name }}</span>
                  <span class="text-[9px] text-gray-500 mt-0.5">{{ bank.description || 'No description' }}</span>
                </div>
                <span class="text-[9px] font-bold px-1.5 py-0.5 bg-white dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700 shrink-0">
                  {{ bank.question_count }} Qs
                </span>
              </div>

              <!-- Export / Import Action Row for Bank -->
              <div class="flex items-center gap-2 mt-1 border-t border-gray-150 dark:border-gray-800/80 pt-2 text-[10px]">
                <button @click.stop="handleExportBank(bank.id, 'docx')" class="text-blue-600 dark:text-blue-400 font-bold hover:underline">DOCX</button>
                <span class="text-gray-350">•</span>
                <button @click.stop="handleExportBank(bank.id, 'xlsx')" class="text-emerald-600 dark:text-emerald-400 font-bold hover:underline">XLSX</button>
                <span class="text-gray-350">•</span>
                <button @click.stop="handleExportBank(bank.id, 'json')" class="text-violet-600 dark:text-violet-400 font-bold hover:underline">JSON</button>
                <div class="ml-auto">
                  <button @click.stop="showImportModal = true; selectedBankId = bank.id" class="text-gray-500 hover:text-blue-600 font-bold">📥 Import</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Column: Question Filtering & Searching -->
      <div class="lg:col-span-8 space-y-4">
        <!-- Filter Bar -->
        <div class="p-4 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl shadow-sm space-y-4">
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div class="flex flex-col gap-1">
              <label class="text-[9px] font-bold text-gray-500 uppercase">Subject</label>
              <select v-model="filterSubject" class="px-3 py-1.5 border border-gray-200 dark:border-gray-800 rounded-lg text-xs bg-white dark:bg-gray-900 text-gray-800 dark:text-white focus:outline-none">
                <option value="">All Subjects</option>
                <option v-for="sub in subjectsList" :key="sub.id" :value="sub.id">{{ sub.name }}</option>
              </select>
            </div>
            <div class="flex flex-col gap-1">
              <label class="text-[9px] font-bold text-gray-500 uppercase">Topic</label>
              <select v-model="filterTopic" :disabled="!filterSubject" class="px-3 py-1.5 border border-gray-200 dark:border-gray-800 rounded-lg text-xs bg-white dark:bg-gray-900 text-gray-800 dark:text-white focus:outline-none disabled:opacity-50">
                <option value="">All Topics</option>
                <option v-for="top in topicsList" :key="top.id" :value="top.id">{{ top.name }}</option>
              </select>
            </div>
            <div class="flex flex-col gap-1">
              <label class="text-[9px] font-bold text-gray-500 uppercase">Question Type</label>
              <select v-model="filterType" class="px-3 py-1.5 border border-gray-200 dark:border-gray-800 rounded-lg text-xs bg-white dark:bg-gray-900 text-gray-800 dark:text-white focus:outline-none">
                <option value="">All Types</option>
                <option value="mcq">Multiple Choice</option>
                <option value="true_false">True / False</option>
                <option value="short_answer">Short Answer</option>
                <option value="essay">Essay / Freeform</option>
              </select>
            </div>
            <div class="flex flex-col gap-1">
              <label class="text-[9px] font-bold text-gray-500 uppercase">Difficulty</label>
              <select v-model="filterDifficulty" class="px-3 py-1.5 border border-gray-200 dark:border-gray-800 rounded-lg text-xs bg-white dark:bg-gray-900 text-gray-800 dark:text-white focus:outline-none">
                <option value="">All Levels</option>
                <option value="easy">Easy</option>
                <option value="medium">Medium</option>
                <option value="hard">Hard</option>
              </select>
            </div>
          </div>

          <div class="flex gap-4">
            <div class="flex-1 flex flex-col gap-1">
              <input type="text" v-model="searchKeyword" placeholder="🔍 Search questions by keywords..." class="w-full px-3 py-1.5 border border-gray-200 dark:border-gray-800 rounded-xl text-xs bg-white dark:bg-gray-900 text-gray-800 dark:text-white focus:outline-none" />
            </div>
            <div class="flex flex-col gap-1">
              <select v-model="filterStatus" class="px-3 py-1.5 border border-gray-200 dark:border-gray-800 rounded-lg text-xs bg-white dark:bg-gray-900 text-gray-800 dark:text-white focus:outline-none">
                <option value="">All Statuses</option>
                <option value="approved">Approved / Published</option>
                <option value="pending">Pending Review</option>
                <option value="rejected">Rejected</option>
                <option value="draft">Draft</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Questions List -->
        <div v-if="loadingQuestions" class="space-y-4">
          <div v-for="i in 3" :key="i" class="h-24 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl animate-pulse"></div>
        </div>

        <div v-else-if="questionsList.length === 0" class="p-8 text-center bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl">
          <span class="text-3xl">🗂️</span>
          <p class="text-xs font-bold text-gray-550 mt-2">No questions found matching your filter criteria.</p>
        </div>

        <div v-else class="space-y-4">
          <div
            v-for="q in questionsList"
            :key="q.id"
            class="p-4 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl shadow-sm flex flex-col gap-3 relative"
          >
            <!-- Question Heading Metadata Row -->
            <div class="flex flex-wrap items-center gap-2">
              <span class="px-1.5 py-0.5 bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 text-[9px] font-bold rounded uppercase">{{ q.question_type }}</span>
              <span class="px-1.5 py-0.5 bg-purple-50 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 text-[9px] font-bold rounded uppercase">Pts: {{ q.points }}</span>
              <span :class="[q.difficulty === 'easy' ? 'bg-emerald-50 text-emerald-600 dark:bg-emerald-900/30' : q.difficulty === 'hard' ? 'bg-rose-50 text-rose-600 dark:bg-rose-900/30' : 'bg-amber-50 text-amber-600 dark:bg-amber-900/30']" class="px-1.5 py-0.5 text-[9px] font-bold rounded uppercase">{{ q.difficulty }}</span>
              <span class="text-[9px] text-gray-400 font-bold ml-auto">{{ q.created_by_name || 'System' }}</span>
              
              <!-- Status Indicators -->
              <span v-if="q.status === 'pending'" class="px-1.5 py-0.5 bg-amber-100 dark:bg-amber-900 text-amber-800 dark:text-amber-200 text-[9px] font-bold rounded">Pending Review</span>
              <span v-if="q.status === 'rejected'" class="px-1.5 py-0.5 bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200 text-[9px] font-bold rounded">Rejected</span>
            </div>

            <!-- Question Text Body -->
            <div class="text-xs text-gray-800 dark:text-gray-200 leading-relaxed" v-html="q.text"></div>

            <!-- MCQ / True-False Options List -->
            <div v-if="q.options && q.options.length > 0" class="grid grid-cols-1 sm:grid-cols-2 gap-2 pl-3 border-l-2 border-gray-150 dark:border-gray-800 py-1">
              <div v-for="(opt, oIdx) in q.options" :key="oIdx" class="text-[11px] flex items-center gap-1.5">
                <span :class="[opt.is_correct ? 'text-emerald-500 font-bold' : 'text-gray-400']">{{ opt.is_correct ? '✓' : '•' }}</span>
                <span :class="[opt.is_correct ? 'text-gray-900 dark:text-white font-semibold' : 'text-gray-650 dark:text-gray-450']">{{ opt.text }}</span>
              </div>
            </div>

            <!-- Performance Statistics Panel -->
            <div v-if="q.usage_stats" class="bg-gray-50 dark:bg-gray-850/50 p-2.5 rounded-xl border border-gray-100 dark:border-gray-850 flex flex-wrap items-center gap-6 mt-1 text-[10px]">
              <div class="flex flex-col gap-0.5">
                <span class="text-gray-400">Exams Used</span>
                <span class="font-bold text-gray-800 dark:text-gray-200">{{ q.usage_stats.used_count }}</span>
              </div>
              <div class="flex flex-col gap-0.5">
                <span class="text-gray-400">Total Attempts</span>
                <span class="font-bold text-gray-800 dark:text-gray-200">{{ q.usage_stats.attempts_count }}</span>
              </div>
              <div class="flex flex-col gap-0.5">
                <span class="text-gray-400">Success Rate</span>
                <div class="flex items-center gap-1.5">
                  <span class="font-bold text-emerald-600 dark:text-emerald-400">{{ Math.round(q.usage_stats.difficulty_index * 100) }}%</span>
                  <div class="w-16 h-1 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                    <div :style="`width: ${q.usage_stats.difficulty_index * 100}%`" class="h-full bg-emerald-500"></div>
                  </div>
                </div>
              </div>
              <div class="flex flex-col gap-0.5">
                <span class="text-gray-400">Discrimination Index</span>
                <span :class="[q.usage_stats.discrimination_index >= 0.3 ? 'text-emerald-600' : 'text-amber-500']" class="font-bold">
                  {{ q.usage_stats.discrimination_index }}
                </span>
              </div>
            </div>

            <!-- Approval Workflow Buttons -->
            <div v-if="q.status === 'pending' && ['teacher', 'school_admin', 'super_admin'].includes(userRole)" class="flex gap-2 justify-end border-t border-gray-150 dark:border-gray-800/80 pt-3 mt-1">
              <button
                @click="handleApproveQuestion(q.id)"
                class="px-3 py-1 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-[10px] rounded-lg shadow"
              >
                ✓ Approve
              </button>
              <button
                @click="openRejectModal(q.id)"
                class="px-3 py-1 bg-red-600 hover:bg-red-700 text-white font-bold text-[10px] rounded-lg shadow"
              >
                ✗ Reject
              </button>
            </div>
            
            <div v-if="q.status === 'rejected' && q.metadata?.rejection_feedback" class="p-2 bg-red-50 dark:bg-red-950/20 text-red-700 dark:text-red-300 text-[10px] rounded-lg border border-red-100 dark:border-red-900/50 mt-1">
              <strong>Rejection Reason:</strong> {{ q.metadata.rejection_feedback }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal: Create Question Bank -->
    <div v-if="showCreateBankModal" class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-fade-in">
      <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-3xl p-6 max-w-md w-full shadow-2xl space-y-4">
        <h3 class="text-sm font-bold text-gray-900 dark:text-white uppercase">Create Question Bank</h3>
        
        <div class="flex flex-col gap-1">
          <label class="text-xs font-bold text-gray-700 dark:text-gray-300">Bank Name</label>
          <input type="text" v-model="newBankName" placeholder="e.g. Algebra Questions Bank" class="px-3 py-2 text-xs border border-gray-300 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none" />
        </div>

        <div class="flex flex-col gap-1">
          <label class="text-xs font-bold text-gray-700 dark:text-gray-300">Description</label>
          <textarea v-model="newBankDesc" rows="2" placeholder="Explain the focus of this question library..." class="px-3 py-2 text-xs border border-gray-300 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none"></textarea>
        </div>

        <div class="flex flex-col gap-1">
          <label class="text-xs font-bold text-gray-700 dark:text-gray-300">Subject</label>
          <select v-model="newBankSubject" class="px-3 py-2 text-xs border border-gray-300 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none">
            <option value="">Select Subject</option>
            <option v-for="sub in subjectsList" :key="sub.id" :value="sub.id">{{ sub.name }}</option>
          </select>
        </div>

        <div class="flex gap-3 justify-end pt-2">
          <button @click="showCreateBankModal = false" class="px-4 py-2 border border-gray-200 dark:border-gray-850 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-xl text-xs font-bold text-gray-650 dark:text-gray-300">Cancel</button>
          <button @click="handleCreateBank" class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold">Save Bank</button>
        </div>
      </div>
    </div>

    <!-- Modal: Import Questions File -->
    <div v-if="showImportModal" class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-fade-in">
      <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-3xl p-6 max-w-md w-full shadow-2xl space-y-4">
        <h3 class="text-sm font-bold text-gray-900 dark:text-white uppercase">Import Questions</h3>
        <p class="text-xs text-gray-500 leading-normal">
          Upload spreadsheets, text sheets, or JSON collections. Make sure columns match: <strong>Question Text, Question Type, Difficulty, Points, Option A, Option B, Correct Option</strong>.
        </p>

        <div class="border-2 border-dashed border-gray-300 dark:border-gray-700 rounded-2xl p-6 flex flex-col items-center justify-center text-center cursor-pointer hover:border-blue-500 transition-all bg-gray-50/50 dark:bg-gray-850/10">
          <input type="file" @change="selectImportFile" class="hidden" id="import-file-elem" accept=".json,.xlsx,.csv" />
          <label for="import-file-elem" class="w-full h-full flex flex-col items-center cursor-pointer">
            <span class="text-3xl mb-1">📄</span>
            <span class="text-xs font-bold text-gray-700 dark:text-gray-300">
              {{ importingFile ? importingFile.name : 'Choose XLSX, CSV or JSON File' }}
            </span>
            <span class="text-[10px] text-gray-450 mt-1">Maximum size 10MB</span>
          </label>
        </div>

        <div class="flex gap-3 justify-end pt-2">
          <button @click="showImportModal = false" class="px-4 py-2 border border-gray-200 dark:border-gray-850 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-xl text-xs font-bold text-gray-650 dark:text-gray-300">Cancel</button>
          <button @click="handleImportQuestions" :disabled="importSaving || !importingFile" class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold flex items-center justify-center gap-2 disabled:opacity-50">
            <span v-if="importSaving" class="animate-spin inline-block w-3 h-3 border-2 border-white border-t-transparent rounded-full"></span>
            {{ importSaving ? 'Uploading...' : 'Start Import' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Modal: Auto Generate Exam Criteria -->
    <div v-if="showGenerateModal" class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-fade-in">
      <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-3xl p-6 max-w-md w-full shadow-2xl space-y-4">
        <h3 class="text-sm font-bold text-gray-900 dark:text-white uppercase flex items-center gap-2">
          🤖 Auto Exam Generator
        </h3>
        
        <div class="flex flex-col gap-1">
          <label class="text-xs font-bold text-gray-700 dark:text-gray-300">Assessment Title</label>
          <input type="text" v-model="genTitle" class="px-3 py-2 text-xs border border-gray-300 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none" />
        </div>

        <div class="flex flex-col gap-1">
          <label class="text-xs font-bold text-gray-700 dark:text-gray-300">Target Classroom</label>
          <select v-model="genClassroom" class="px-3 py-2 text-xs border border-gray-300 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none">
            <option value="">-- No Specific Classroom --</option>
            <option v-for="cls in classroomsList" :key="cls.id" :value="cls.id">{{ cls.name }}</option>
          </select>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div class="flex flex-col gap-1">
            <label class="text-xs font-bold text-gray-700 dark:text-gray-300">Total Questions</label>
            <input type="number" v-model="genTotal" class="px-3 py-2 text-xs border border-gray-300 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 focus:outline-none" />
          </div>
          <div class="flex flex-col gap-1">
            <label class="text-xs font-bold text-gray-700 dark:text-gray-300">Duration (Minutes)</label>
            <input type="number" v-model="genDuration" class="px-3 py-2 text-xs border border-gray-300 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 focus:outline-none" />
          </div>
        </div>

        <div class="bg-gray-50 dark:bg-gray-850 p-4 rounded-2xl border border-gray-155 dark:border-gray-800 space-y-3">
          <span class="text-[10px] font-bold text-gray-500 uppercase block">Difficulty Distribution Split</span>
          <div class="grid grid-cols-3 gap-3">
            <div class="flex flex-col gap-1">
              <label class="text-[9px] font-bold text-emerald-600 dark:text-emerald-450 uppercase">Easy</label>
              <input type="number" v-model="genEasy" class="px-2 py-1 text-xs border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 focus:outline-none" />
            </div>
            <div class="flex flex-col gap-1">
              <label class="text-[9px] font-bold text-amber-600 dark:text-amber-450 uppercase">Medium</label>
              <input type="number" v-model="genMedium" class="px-2 py-1 text-xs border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 focus:outline-none" />
            </div>
            <div class="flex flex-col gap-1">
              <label class="text-[9px] font-bold text-rose-600 dark:text-rose-455 uppercase">Hard</label>
              <input type="number" v-model="genHard" class="px-2 py-1 text-xs border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 focus:outline-none" />
            </div>
          </div>
        </div>

        <div class="flex gap-3 justify-end pt-2">
          <button @click="showGenerateModal = false" class="px-4 py-2 border border-gray-200 dark:border-gray-850 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-xl text-xs font-bold text-gray-650 dark:text-gray-300">Cancel</button>
          <button @click="handleAutoGenerateExam" :disabled="genSaving" class="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold flex items-center justify-center gap-2">
            <span v-if="genSaving" class="animate-spin inline-block w-3 h-3 border-2 border-white border-t-transparent rounded-full"></span>
            🤖 {{ genSaving ? 'Generating...' : 'Generate Test' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Modal: HOD Rejection Reason Feedback -->
    <div v-if="showRejectModal" class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-fade-in">
      <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-3xl p-6 max-w-md w-full shadow-2xl space-y-4">
        <h3 class="text-sm font-bold text-gray-900 dark:text-white uppercase">Reject Question</h3>
        
        <div class="flex flex-col gap-1">
          <label class="text-xs font-bold text-gray-700 dark:text-gray-300">Review Feedback / Reason for rejection</label>
          <textarea v-model="rejectFeedback" rows="3" placeholder="Provide details on how to improve this question..." class="px-3 py-2 text-xs border border-gray-300 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none"></textarea>
        </div>

        <div class="flex gap-3 justify-end pt-2">
          <button @click="showRejectModal = false" class="px-4 py-2 border border-gray-200 dark:border-gray-850 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-xl text-xs font-bold text-gray-650 dark:text-gray-300">Cancel</button>
          <button @click="handleRejectQuestion" :disabled="rejectSaving" class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-xl text-xs font-bold flex items-center justify-center gap-2">
            <span v-if="rejectSaving" class="animate-spin inline-block w-3 h-3 border-2 border-white border-t-transparent rounded-full"></span>
            ✗ Reject Question
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<style scoped>
.animate-fade-in {
  animation: fadeIn 0.2s ease-out;
}
@keyframes fadeIn {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}
</style>
