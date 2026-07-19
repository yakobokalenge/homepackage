<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAssessmentStore } from '../../stores/assessment'
import { useNotificationStore } from '../../stores/notification'
import api from '../../services/api'
import DocumentUploader from '../../components/assessment/DocumentUploader.vue'
import { proctoringService } from '../../services/proctoring.service'

import { AssessmentType, DifficultyLevel } from '../../types/assessment'

const router = useRouter()
const assessmentStore = useAssessmentStore()
const notificationStore = useNotificationStore()

// State
const currentStep = ref(1)
const loading = ref(false)

// Options Lists
const subjectsList = ref<any[]>([])
const classroomsList = ref<any[]>([])

// Assessment Form Payload
const form = ref({
  title: '',
  description: '',
  instructions: '',
  subject: '',
  classroom: '',
  assessment_type: 'quiz' as AssessmentType,
  difficulty: 'medium' as DifficultyLevel,
  time_limit_minutes: 30,
  max_attempts: 1,
  passing_score: '50.00',
  shuffle_questions: false,
  shuffle_options: false,
  show_results_immediately: true,
  show_correct_answers: true,
  is_proctored: false,
  allow_late_submission: false,
  start_datetime: '',
  end_datetime: '',
  questions_data: [] as any[] // List of linked questions
})

// Proctoring Config Form
const proctorForm = ref({
  require_webcam: true,
  require_microphone: true,
  require_fullscreen: true,
  block_copy_paste: true,
  block_right_click: true,
  block_devtools: true,
  require_identity_verification: true,
  max_tab_switches: 3,
  ai_monitoring_enabled: true,
  auto_submit_on_violation_count: 5
})

// Question Creator States
const questionTab = ref('ai') // 'ai' or 'upload' or 'manual'
const aiTopic = ref('')
const aiCount = ref(5)
const aiTypes = ref<string[]>(['mcq'])
const aiPrompt = ref('')
const aiGenerating = ref(false)

// Added questions list for preview
const addedQuestions = ref<any[]>([])
const pdfUrl = ref('')

const stagedQuestions = ref<any[]>([])
const showStagedReview = ref(false)
const selectedStagedIds = ref<string[]>([])
const editingStagedId = ref<string | null>(null)
const editingStagedQuestion = ref<any | null>(null)
const stagedApproving = ref(false)


// Question Bank Integration States
const questionBanksList = ref<any[]>([])
const selectedBankId = ref('')
const selectedBankQuestions = ref<any[]>([])
const selectedBankQuestionIds = ref<string[]>([])
const loadingBankQuestions = ref(false)
const saveToBank = ref(false)

// Draft Mode States
const draftId = ref<string | null>(null)
const autoSavingBackend = ref(false)


// Manual Question Creator States
const manualSaving = ref(false)
const manualQuestion = ref({
  text: '',
  question_type: 'mcq',
  points: 5.0,
  options: [
    { text: 'Option A', is_correct: true, order: 1, match_pair: '' },
    { text: 'Option B', is_correct: false, order: 2, match_pair: '' },
    { text: 'Option C', is_correct: false, order: 3, match_pair: '' },
    { text: 'Option D', is_correct: false, order: 4, match_pair: '' }
  ]
})

function addManualOption() {
  const nextOrder = manualQuestion.value.options.length + 1
  const letter = String.fromCharCode(65 + manualQuestion.value.options.length)
  manualQuestion.value.options.push({
    text: `Option ${letter}`,
    is_correct: false,
    order: nextOrder,
    match_pair: ''
  })
}

function removeManualOption(idx: number) {
  manualQuestion.value.options.splice(idx, 1)
  manualQuestion.value.options.forEach((opt, index) => {
    opt.order = index + 1
  })
}

// Watch question type to reset options structure accordingly
watch(() => manualQuestion.value.question_type, (newType) => {
  if (newType === 'true_false') {
    manualQuestion.value.options = [
      { text: 'True', is_correct: true, order: 1, match_pair: '' },
      { text: 'False', is_correct: false, order: 2, match_pair: '' }
    ]
  } else if (newType === 'mcq') {
    manualQuestion.value.options = [
      { text: 'Option A', is_correct: true, order: 1, match_pair: '' },
      { text: 'Option B', is_correct: false, order: 2, match_pair: '' },
      { text: 'Option C', is_correct: false, order: 3, match_pair: '' },
      { text: 'Option D', is_correct: false, order: 4, match_pair: '' }
    ]
  } else {
    manualQuestion.value.options = []
  }
})

async function handleAddManualQuestion() {
  if (!form.value.subject) {
    notificationStore.warning('Please select a subject first.')
    return
  }
  if (!manualQuestion.value.text.trim()) {
    notificationStore.warning('Please enter the question text.')
    return
  }

  // Validate options for MCQ and True/False questions
  if (['mcq', 'true_false'].includes(manualQuestion.value.question_type)) {
    const hasCorrect = manualQuestion.value.options.some(opt => opt.is_correct)
    if (!hasCorrect) {
      notificationStore.warning('Please select at least one correct option.')
      return
    }
    const hasEmpty = manualQuestion.value.options.some(opt => !opt.text.trim())
    if (hasEmpty) {
      notificationStore.warning('Please fill in all option text fields.')
      return
    }
  }

  manualSaving.value = true
  try {
    const payload = {
      subject: form.value.subject,
      topic: null,
      question_type: manualQuestion.value.question_type,
      difficulty: form.value.difficulty || 'medium',
      text: manualQuestion.value.text,
      points: String(manualQuestion.value.points),
      options: manualQuestion.value.options
    }

    const res = await api.post('/content/questions/', payload)
    const q = res.data

    if (saveToBank.value) {
      await saveQuestionToUserBank(q.id)
    }

    addedQuestions.value.push(q)
    form.value.questions_data.push({
      question_id: q.id,
      order: form.value.questions_data.length,
      points_override: q.points,
      is_required: true
    })

    // Reset manual question text while keeping the question type
    manualQuestion.value.text = ''
    if (manualQuestion.value.question_type === 'mcq') {
      manualQuestion.value.options = [
        { text: 'Option A', is_correct: true, order: 1, match_pair: '' },
        { text: 'Option B', is_correct: false, order: 2, match_pair: '' },
        { text: 'Option C', is_correct: false, order: 3, match_pair: '' },
        { text: 'Option D', is_correct: false, order: 4, match_pair: '' }
      ]
    } else if (manualQuestion.value.question_type === 'true_false') {
      manualQuestion.value.options = [
        { text: 'True', is_correct: true, order: 1, match_pair: '' },
        { text: 'False', is_correct: false, order: 2, match_pair: '' }
      ]
    }

    notificationStore.success('Question added successfully.')
  } catch (err) {
    console.error(err)
    notificationStore.error('Failed to save manual question.')
  } finally {
    manualSaving.value = false
  }
}

function setManualOptionCorrect(idx: number) {
  manualQuestion.value.options.forEach((opt, oIdx) => {
    opt.is_correct = (oIdx === idx)
  })
}

function moveQuestionUp(index: number) {
  if (index === 0) return
  const tempQ = addedQuestions.value[index]
  addedQuestions.value[index] = addedQuestions.value[index - 1]
  addedQuestions.value[index - 1] = tempQ

  const tempQD = form.value.questions_data[index]
  form.value.questions_data[index] = form.value.questions_data[index - 1]
  form.value.questions_data[index - 1] = tempQD

  form.value.questions_data.forEach((item, idx) => {
    item.order = idx
  })
}

function moveQuestionDown(index: number) {
  if (index === addedQuestions.value.length - 1) return
  const tempQ = addedQuestions.value[index]
  addedQuestions.value[index] = addedQuestions.value[index + 1]
  addedQuestions.value[index + 1] = tempQ

  const tempQD = form.value.questions_data[index]
  form.value.questions_data[index] = form.value.questions_data[index + 1]
  form.value.questions_data[index + 1] = tempQD

  form.value.questions_data.forEach((item, idx) => {
    item.order = idx
  })
}

function insertManualText(prefix: string, suffix: string = '') {
  const textarea = document.getElementById('manual-q-textarea') as HTMLTextAreaElement
  if (textarea) {
    const start = textarea.selectionStart
    const end = textarea.selectionEnd
    const currentVal = manualQuestion.value.text
    const selectedText = currentVal.substring(start, end)
    const toInsert = suffix ? prefix + selectedText + suffix : prefix
    manualQuestion.value.text = currentVal.substring(0, start) + toInsert + currentVal.substring(end)
    setTimeout(() => {
      textarea.focus()
      const newPos = suffix && start === end ? start + prefix.length : start + toInsert.length
      textarea.setSelectionRange(newPos, newPos)
    }, 50)
  } else {
    manualQuestion.value.text += suffix ? prefix + suffix : prefix
  }
}


async function loadQuestionBanks() {
  try {
    const res = await api.get('/content/question-banks/')
    questionBanksList.value = Array.isArray(res.data) ? res.data : res.data?.results || []
  } catch (err) {
    console.error('Failed to load question banks:', err)
  }
}

async function loadBankQuestions() {
  if (!selectedBankId.value) {
    selectedBankQuestions.value = []
    selectedBankQuestionIds.value = []
    return
  }

  loadingBankQuestions.value = true
  try {
    const res = await api.get(`/content/question-banks/${selectedBankId.value}/`)
    selectedBankQuestions.value = res.data.questions_detail || []
    selectedBankQuestionIds.value = []
  } catch (err) {
    console.error(err)
    notificationStore.error('Failed to load questions from bank.')
  } finally {
    loadingBankQuestions.value = false
  }
}

function toggleBankQuestionSelect(id: string) {
  const index = selectedBankQuestionIds.value.indexOf(id)
  if (index > -1) {
    selectedBankQuestionIds.value.splice(index, 1)
  } else {
    selectedBankQuestionIds.value.push(id)
  }
}

function selectAllBankQuestions() {
  if (selectedBankQuestionIds.value.length === selectedBankQuestions.value.length) {
    selectedBankQuestionIds.value = []
  } else {
    selectedBankQuestionIds.value = selectedBankQuestions.value.map(q => q.id)
  }
}

function handleImportFromBank() {
  if (selectedBankQuestionIds.value.length === 0) return

  const questionsToImport = selectedBankQuestions.value.filter(q => selectedBankQuestionIds.value.includes(q.id))
  
  questionsToImport.forEach(q => {
    if (!addedQuestions.value.some(existing => existing.id === q.id)) {
      addedQuestions.value.push(q)
      form.value.questions_data.push({
        question_id: q.id,
        order: form.value.questions_data.length,
        points_override: q.points,
        is_required: true
      })
    }
  })

  selectedBankId.value = ''
  selectedBankQuestions.value = []
  selectedBankQuestionIds.value = []
  notificationStore.success('Questions imported successfully.')
}

async function saveQuestionToUserBank(questionId: string) {
  try {
    let bank = questionBanksList.value.find(b => b.subject === form.value.subject && !b.is_public)
    
    if (!bank) {
      const subjectObj = subjectsList.value.find(s => s.id === form.value.subject)
      const subName = subjectObj ? subjectObj.name : 'Subject'
      
      const newBankRes = await api.post('/content/question-banks/', {
        name: `My Personal ${subName} Bank`,
        description: 'Auto-created bank for manual questions',
        subject: form.value.subject,
        questions: [questionId]
      })
      bank = newBankRes.data
      await loadQuestionBanks()
    } else {
      const existingQuestionIds = bank.questions || []
      if (!existingQuestionIds.includes(questionId)) {
        const updatedQuestions = [...existingQuestionIds, questionId]
        await api.patch(`/content/question-banks/${bank.id}/`, {
          questions: updatedQuestions
        })
        bank.questions = updatedQuestions
      }
    }
  } catch (err) {
    console.error('Failed to save question to bank:', err)
  }
}

// ------------------------------------------------------------------
// Draft Mode Logic
// ------------------------------------------------------------------
let draftTimer: any = null

function startDraftAutoSave() {
  draftTimer = setInterval(() => {
    // 1. Save to Local Storage backup
    const dataToSave = {
      form: form.value,
      addedQuestions: addedQuestions.value,
      currentStep: currentStep.value,
      proctorForm: proctorForm.value,
      updated_at: new Date().toISOString()
    }
    localStorage.setItem('homepackage_assessment_draft', JSON.stringify(dataToSave))
    
    // 2. Save draft to backend if title & subject are populated
    saveDraftToBackend()
  }, 15000)
}

async function saveDraftToBackend() {
  if (!form.value.title || !form.value.subject || autoSavingBackend.value) return
  
  autoSavingBackend.value = true
  try {
    const payload = {
      ...form.value,
      status: 'draft'
    }
    
    if (draftId.value) {
      await api.patch(`/assessments/assessments/${draftId.value}/`, payload)
    } else {
      const res = await api.post('/assessments/assessments/', payload)
      draftId.value = res.data.id
    }
    console.log('Draft autosaved successfully.')
  } catch (err) {
    console.warn('Backend draft autosave failed, local storage backup remains active.')
  } finally {
    autoSavingBackend.value = false
  }
}


async function loadInitialData() {
  try {
    const subRes = await api.get('/content/subjects/')
    subjectsList.value = Array.isArray(subRes.data) ? subRes.data : subRes.data?.results || []
    
    const clsRes = await api.get('/schools/classrooms/')
    classroomsList.value = Array.isArray(clsRes.data) ? clsRes.data : clsRes.data?.results || []
    
    if (subjectsList.value.length > 0) form.value.subject = subjectsList.value[0].id
    if (classroomsList.value.length > 0) form.value.classroom = classroomsList.value[0].id
  } catch (err) {
    console.error(err)
    notificationStore.error('Failed to load initial data.')
  }
}

// AI Question Generator call
async function handleAIGenerate() {
  if (!form.value.subject) {
    notificationStore.warning('Please select a subject first.')
    return
  }
  
  aiGenerating.value = true
  try {
    // Generate AI questions into a temporary draft assessment
    // Wait, since ViewSet generate_ai detail action is detail=True, let's create a temporary draft assessment, or call it directly.
    // Wait! Let's check detail=True, yes, detailed generate_ai requires an assessment ID.
    // So we first create the assessment draft at the end of Step 1, or we can use the main content generate_ai endpoint!
    // Wait, the main content app has a QuestionViewSet with a generate_ai list action: `/api/v1/content/questions/generate_ai/`.
    // Let's check content/views.py lines 44-46:
    // `@action(detail=False, methods=['post']) def generate_ai(self, request):`
    // YES! The list action `/api/v1/content/questions/generate_ai/` generates questions and saves them under the content app and returns them.
    // So we can call that directly! Let's call `/content/questions/generate_ai/`.
    const res = await api.post('/content/questions/generate_ai/', {
      subject: form.value.subject,
      topic: aiTopic.value || null,
      question_type: aiTypes.value[0] || 'mcq',
      difficulty: form.value.difficulty,
      count: aiCount.value,
      prompt: aiPrompt.value
    })
    
    const questions = Array.isArray(res.data) ? res.data : res.data?.results || []
    questions.forEach((q: any) => {
      addedQuestions.value.push(q)
      form.value.questions_data.push({
        question_id: q.id,
        order: form.value.questions_data.length,
        points_override: '5.00',
        is_required: true
      })
    })
    notificationStore.success(`AI successfully generated ${questions.length} questions.`)
  } catch (err) {
    notificationStore.error('AI generation failed.')
  } finally {
    aiGenerating.value = false
  }
}

// Document uploader parsed questions handler
function handleDocumentExtracted(questions: any[]) {
  questions.forEach((q: any) => {
    addedQuestions.value.push(q)
    form.value.questions_data.push({
      question_id: q.id,
      order: form.value.questions_data.length,
      points_override: q.points ? parseFloat(q.points).toFixed(2) : '5.00',
      is_required: true
    })
  })
  notificationStore.success(`Extracted ${questions.length} questions from document.`)
}

// Handle Staged questions loaded
function handleStagedQuestionsReady(data: { questions: any[], jobId: string }) {
  stagedQuestions.value = data.questions
  selectedStagedIds.value = data.questions.map(q => q.id)
  showStagedReview.value = true
}

function toggleStagedSelect(id: string) {
  const idx = selectedStagedIds.value.indexOf(id)
  if (idx > -1) {
    selectedStagedIds.value.splice(idx, 1)
  } else {
    selectedStagedIds.value.push(id)
  }
}

function startEditStaged(q: any) {
  editingStagedId.value = q.id
  // Clone question details
  editingStagedQuestion.value = JSON.parse(JSON.stringify(q))
}

async function saveStagedEdit() {
  if (!editingStagedQuestion.value) return
  try {
    const res = await api.patch(`/assessments/staged-questions/${editingStagedId.value}/`, editingStagedQuestion.value)
    
    // Update local stagedQuestions item
    const idx = stagedQuestions.value.findIndex(q => q.id === editingStagedId.value)
    if (idx > -1) {
      stagedQuestions.value[idx] = res.data
    }
    
    editingStagedId.value = null
    editingStagedQuestion.value = null
    notificationStore.success('Staged question changes saved.')
  } catch (err) {
    console.error(err)
    notificationStore.error('Failed to save question edits.')
  }
}

async function deleteStaged(id: string) {
  if (!confirm('Are you sure you want to reject/delete this staged question?')) return
  try {
    await api.delete(`/assessments/staged-questions/${id}/`)
    stagedQuestions.value = stagedQuestions.value.filter(q => q.id !== id)
    selectedStagedIds.value = selectedStagedIds.value.filter(item => item !== id)
    notificationStore.success('Staged question deleted.')
  } catch (err) {
    console.error(err)
    notificationStore.error('Failed to delete staged question.')
  }
}

async function handleApproveStaged() {
  if (selectedStagedIds.value.length === 0) {
    notificationStore.warning('Please select at least one question to approve.')
    return
  }
  
  stagedApproving.value = true
  try {
    const res = await api.post('/assessments/staged-questions/confirm_staged/', {
      staged_ids: selectedStagedIds.value
    })
    
    const approvedQuestions = res.data.questions || []
    handleDocumentExtracted(approvedQuestions)
    
    // Reset staging state
    stagedQuestions.value = []
    selectedStagedIds.value = []
    showStagedReview.value = false
    notificationStore.success(`Successfully approved and added ${approvedQuestions.length} questions.`)
  } catch (err) {
    console.error(err)
    notificationStore.error('Failed to confirm and approve questions.')
  } finally {
    stagedApproving.value = false
  }
}


// Remove question from local list
function removeQuestion(index: number) {
  addedQuestions.value.splice(index, 1)
  form.value.questions_data.splice(index, 1)
}

// Final Save Assessment
async function handleSaveAssessment() {
  if (form.value.questions_data.length === 0) {
    notificationStore.warning('Please add at least one question to the assessment.')
    return
  }

  loading.value = true
  try {
    // 1. Create or Update Assessment (use draft ID if already created to prevent duplicate assessments)
    let newAssessment;
    if (draftId.value) {
      const res = await api.put(`/assessments/assessments/${draftId.value}/`, {
        ...form.value,
        status: 'published' // publish it directly
      })
      newAssessment = res.data
    } else {
      newAssessment = await assessmentStore.createAssessment(form.value)
    }
    
    // 2. Save Proctoring configuration if enabled
    if (form.value.is_proctored) {
      await proctoringService.updateConfig(newAssessment.id, proctorForm.value)
    }

    // 3. Clear auto-save draft
    localStorage.removeItem('homepackage_assessment_draft')

    notificationStore.success('Assessment created successfully.')
    router.push('/teacher/assessments')
  } catch (err: any) {
    const errorData = err.response?.data
    let errorMsg = 'Failed to create assessment.'
    if (errorData && typeof errorData === 'object') {
      const details = Object.entries(errorData)
        .map(([key, val]) => `${key}: ${Array.isArray(val) ? val.join(', ') : val}`)
        .join(' | ')
      if (details) errorMsg += ` (${details})`
    }
    notificationStore.error(errorMsg)
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await loadInitialData()
  await loadQuestionBanks()

  // 1. Check for unsaved draft in local storage backup
  const savedDraft = localStorage.getItem('homepackage_assessment_draft')
  if (savedDraft) {
    try {
      const draftData = JSON.parse(savedDraft)
      if (confirm('An unsaved assessment draft was found. Do you want to restore it?')) {
        form.value = draftData.form
        addedQuestions.value = draftData.addedQuestions
        currentStep.value = draftData.currentStep
        proctorForm.value = draftData.proctorForm
        notificationStore.success('Draft restored successfully.')
      } else {
        localStorage.removeItem('homepackage_assessment_draft')
      }
    } catch (err) {
      console.error('Failed to parse draft:', err)
    }
  }

  // 2. Start Draft Auto-save every 15 seconds
  startDraftAutoSave()
})

onUnmounted(() => {
  if (draftTimer) {
    clearInterval(draftTimer)
  }
})
</script>

<template>
  <div class="space-y-6 max-w-4xl mx-auto">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Create Assessment</h1>
      <p class="text-sm text-gray-500 mt-1">Design an interactive exam or homework package for your students.</p>
    </div>

    <!-- Step Progress Indicator -->
    <div class="flex items-center justify-between p-4 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl">
      <div v-for="step in [1, 2, 3, 4]" :key="step" class="flex items-center gap-2">
        <span
          :class="[
            currentStep === step
              ? 'bg-blue-600 border-blue-600 text-white'
              : currentStep > step
              ? 'bg-emerald-600 border-emerald-600 text-white'
              : 'border-gray-300 text-gray-400',
            'w-8 h-8 rounded-full border flex items-center justify-center text-xs font-bold'
          ]"
        >
          {{ currentStep > step ? '✓' : step }}
        </span>
        <span v-if="step === 1" class="text-xs font-bold hidden sm:inline" :class="currentStep >= 1 ? 'text-gray-900 dark:text-white' : 'text-gray-400'">Details</span>
        <span v-if="step === 2" class="text-xs font-bold hidden sm:inline" :class="currentStep >= 2 ? 'text-gray-900 dark:text-white' : 'text-gray-400'">Questions</span>
        <span v-if="step === 3" class="text-xs font-bold hidden sm:inline" :class="currentStep >= 3 ? 'text-gray-900 dark:text-white' : 'text-gray-400'">Proctoring</span>
        <span v-if="step === 4" class="text-xs font-bold hidden sm:inline" :class="currentStep >= 4 ? 'text-gray-900 dark:text-white' : 'text-gray-400'">Review</span>
        <span v-if="step < 4" class="w-10 sm:w-16 h-0.5 bg-gray-200 dark:bg-gray-800"></span>
      </div>
    </div>

    <!-- Step 1: Details -->
    <div v-show="currentStep === 1" class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 space-y-4">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div class="flex flex-col gap-1.5">
          <label class="text-xs font-bold text-gray-700 dark:text-gray-300">Assessment Title</label>
          <input type="text" v-model="form.title" placeholder="e.g. Biology Midterm Exam" class="px-3 py-2 text-xs border border-gray-300 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none" />
        </div>
        <div class="flex flex-col gap-1.5">
          <label class="text-xs font-bold text-gray-700 dark:text-gray-300">Subject</label>
          <select v-model="form.subject" class="px-3 py-2 text-xs border border-gray-300 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none">
            <option v-for="sub in subjectsList" :key="sub.id" :value="sub.id">{{ sub.name }}</option>
          </select>
        </div>
        <div class="flex flex-col gap-1.5">
          <label class="text-xs font-bold text-gray-700 dark:text-gray-300">Target Classroom</label>
          <select v-model="form.classroom" class="px-3 py-2 text-xs border border-gray-300 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none">
            <option value="">General (All Classrooms)</option>
            <option v-for="cls in classroomsList" :key="cls.id" :value="cls.id">{{ cls.name }} (Stream {{ cls.stream }})</option>
          </select>
        </div>
        <div class="flex flex-col gap-1.5">
          <label class="text-xs font-bold text-gray-700 dark:text-gray-300">Delivery Type</label>
          <select v-model="form.assessment_type" class="px-3 py-2 text-xs border border-gray-300 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none">
            <option value="quiz">Quiz</option>
            <option value="test">Test</option>
            <option value="assignment">Assignment</option>
            <option value="exam">Exam</option>
            <option value="home_package">Home Package</option>
          </select>
        </div>
        <div class="flex flex-col gap-1.5">
          <label class="text-xs font-bold text-gray-700 dark:text-gray-300">Time Limit (Minutes)</label>
          <input type="number" v-model="form.time_limit_minutes" class="px-3 py-2 text-xs border border-gray-300 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none" />
        </div>
        <div class="flex flex-col gap-1.5">
          <label class="text-xs font-bold text-gray-700 dark:text-gray-300">Max Allowed Attempts</label>
          <input type="number" v-model="form.max_attempts" class="px-3 py-2 text-xs border border-gray-300 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none" />
        </div>
        <div class="flex flex-col gap-1.5">
          <label class="text-xs font-bold text-gray-700 dark:text-gray-300">Start Date & Time (Optional)</label>
          <input type="datetime-local" v-model="form.start_datetime" class="px-3 py-2 text-xs border border-gray-300 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none" />
        </div>
        <div class="flex flex-col gap-1.5">
          <label class="text-xs font-bold text-gray-700 dark:text-gray-300">End Date & Time (Optional)</label>
          <input type="datetime-local" v-model="form.end_datetime" class="px-3 py-2 text-xs border border-gray-300 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none" />
        </div>
      </div>
      
      <div class="flex flex-col gap-1.5">
        <label class="text-xs font-bold text-gray-700 dark:text-gray-300">Instructions to Candidates</label>
        <textarea rows="3" v-model="form.instructions" placeholder="e.g. Ensure your camera remains active. Read each question carefully." class="px-3 py-2 text-xs border border-gray-300 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none"></textarea>
      </div>

      <div class="flex items-center gap-6 pt-3">
        <label class="flex items-center gap-2 cursor-pointer text-xs text-gray-700 dark:text-gray-300">
          <input type="checkbox" v-model="form.is_proctored" class="rounded border-gray-300 text-blue-600 focus:ring-blue-500" />
          Require Online Proctoring (🛡️ webcam + VAD monitoring)
        </label>
        <label class="flex items-center gap-2 cursor-pointer text-xs text-gray-700 dark:text-gray-300">
          <input type="checkbox" v-model="form.shuffle_questions" class="rounded border-gray-300 text-blue-600 focus:ring-blue-500" />
          Shuffle Questions Sequence
        </label>
      </div>
    </div>

    <!-- Step 2: Questions Selection / AI / PDF upload -->
    <div v-show="currentStep === 2" class="space-y-6">
      <div :class="[pdfUrl ? 'grid grid-cols-1 lg:grid-cols-12 gap-6' : 'space-y-6']">
        
        <!-- Left Column: Uploaded Document Resemblance Preview -->
        <div v-if="pdfUrl" class="lg:col-span-5 space-y-3">
          <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-4 shadow-sm flex flex-col h-full">
            <div class="flex items-center justify-between pb-3 border-b border-gray-150 dark:border-gray-800 mb-3">
              <span class="text-xs font-bold text-gray-700 dark:text-gray-300">📄 Original Document Resemblance</span>
              <button @click="pdfUrl = ''" class="text-red-500 hover:text-red-700 text-xs flex items-center gap-1 font-semibold">❌ Clear Preview</button>
            </div>
            <iframe :src="pdfUrl" class="w-full h-[580px] rounded-xl bg-gray-50 border border-gray-200 dark:border-gray-800 shadow-inner"></iframe>
          </div>
        </div>

        <!-- Right/Main Column: Settings & Extracted preview -->
        <div :class="[pdfUrl ? 'lg:col-span-7' : '']" class="space-y-6">
          <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6">
            <!-- Tabs -->
            <div class="flex gap-4 border-b border-gray-150 dark:border-gray-800 pb-3 mb-6">
              <button @click="questionTab = 'ai'" :class="[questionTab === 'ai' ? 'text-blue-600 border-blue-600 border-b-2 font-bold' : 'text-gray-500', 'text-xs pb-1']">🤖 AI Assisted Generator</button>
              <button @click="questionTab = 'upload'" :class="[questionTab === 'upload' ? 'text-blue-600 border-blue-600 border-b-2 font-bold' : 'text-gray-500', 'text-xs pb-1']">📄 Upload PDF Worksheet</button>
              <button @click="questionTab = 'manual'" :class="[questionTab === 'manual' ? 'text-blue-600 border-blue-600 border-b-2 font-bold' : 'text-gray-500', 'text-xs pb-1']">✍️ Create Question Manually</button>
              <button @click="questionTab = 'bank'" :class="[questionTab === 'bank' ? 'text-blue-600 border-blue-600 border-b-2 font-bold' : 'text-gray-500', 'text-xs pb-1']">🗂️ Import from Question Bank</button>
            </div>

            <!-- AI Tab -->
            <div v-show="questionTab === 'ai'" class="space-y-4">
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div class="flex flex-col gap-1.5">
                  <label class="text-xs font-bold text-gray-700 dark:text-gray-300">Focus Topic / Concept</label>
                  <input type="text" v-model="aiTopic" placeholder="e.g. Osmosis or Quadratic equations" class="px-3 py-2 text-xs border border-gray-300 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none" />
                </div>
                <div class="flex flex-col gap-1.5">
                  <label class="text-xs font-bold text-gray-700 dark:text-gray-300">Question Type</label>
                  <select v-model="aiTypes[0]" class="px-3 py-2 text-xs border border-gray-300 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none">
                    <option value="mcq">Multiple Choice</option>
                    <option value="true_false">True / False</option>
                    <option value="short_answer">Short Answer</option>
                    <option value="essay">Essay / Freeform</option>
                  </select>
                </div>
                <div class="flex flex-col gap-1.5">
                  <label class="text-xs font-bold text-gray-700 dark:text-gray-300">Questions Count</label>
                  <input type="number" v-model="aiCount" class="px-3 py-2 text-xs border border-gray-300 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none" />
                </div>
              </div>

              <div class="flex flex-col gap-1.5">
                <label class="text-xs font-bold text-gray-700 dark:text-gray-300">Custom Prompts / Constraints</label>
                <input type="text" v-model="aiPrompt" placeholder="e.g. Ensure all calculations match secondary school levels" class="px-3 py-2 text-xs border border-gray-300 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none" />
              </div>

              <button
                @click="handleAIGenerate"
                :disabled="aiGenerating"
                class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-xl flex items-center justify-center gap-2 disabled:opacity-50"
              >
                <span v-if="aiGenerating" class="animate-spin inline-block w-3 h-3 border-2 border-white border-t-transparent rounded-full"></span>
                {{ aiGenerating ? 'Generating Questions...' : '🤖 Generate Questions' }}
              </button>
            </div>

            <!-- Document Upload Tab -->
            <div v-show="questionTab === 'upload'" class="space-y-6">
              <div v-if="!showStagedReview">
                <DocumentUploader :subjectId="form.subject" @staged-ready="handleStagedQuestionsReady" @file-selected="pdfUrl = $event" @error="notificationStore.error($event)" />
              </div>

              <!-- Staged Review Interface -->
              <div v-else class="space-y-6">
                <div class="flex items-center justify-between pb-3 border-b border-gray-150 dark:border-gray-800">
                  <div>
                    <h3 class="text-xs font-bold text-gray-850 dark:text-white">Review Extracted Staging Questions</h3>
                    <p class="text-[10px] text-gray-500 mt-0.5">Edit, select, or delete questions before approving and adding them.</p>
                  </div>
                  <button @click="showStagedReview = false" class="text-xs text-gray-500 hover:text-gray-700">← Re-upload</button>
                </div>

                <div class="space-y-4 max-h-[500px] overflow-y-auto pr-2">
                  <div
                    v-for="q in stagedQuestions"
                    :key="q.id"
                    class="p-4 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl space-y-4 relative"
                  >
                    <!-- Header -->
                    <div class="flex items-start justify-between gap-3 pb-2 border-b border-gray-200 dark:border-gray-800">
                      <label class="flex items-center gap-2 cursor-pointer font-bold text-[10px] text-gray-700 dark:text-gray-300">
                        <input type="checkbox" :checked="selectedStagedIds.includes(q.id)" @change="toggleStagedSelect(q.id)" class="rounded border-gray-300 text-blue-600 focus:ring-blue-500" />
                        Include in Selection
                      </label>
                      <div class="flex gap-2">
                        <button v-if="editingStagedId !== q.id" @click="startEditStaged(q)" class="text-[10px] font-bold text-blue-600 hover:underline">Edit</button>
                        <button @click="deleteStaged(q.id)" class="text-[10px] font-bold text-red-500 hover:underline">Delete</button>
                      </div>
                    </div>

                    <!-- Question edit mode -->
                    <div v-if="editingStagedId === q.id && editingStagedQuestion" class="space-y-3 pt-2">
                      <div class="flex flex-col gap-1">
                        <label class="text-[10px] font-bold text-gray-500 uppercase">Question Text</label>
                        <textarea v-model="editingStagedQuestion.text" rows="3" class="px-3 py-2 text-xs border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none"></textarea>
                      </div>

                      <div class="grid grid-cols-2 gap-4">
                        <div class="flex flex-col gap-1">
                          <label class="text-[10px] font-bold text-gray-500 uppercase">Question Type</label>
                          <select v-model="editingStagedQuestion.question_type" class="px-2 py-1.5 text-xs border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 focus:outline-none">
                            <option value="mcq">Multiple Choice</option>
                            <option value="true_false">True / False</option>
                            <option value="fill_blank">Fill in the Blank</option>
                            <option value="short_answer">Short Answer</option>
                            <option value="essay">Essay / Freeform</option>
                            <option value="matching">Matching</option>
                            <option value="ordering">Ordering</option>
                          </select>
                        </div>
                        <div class="flex flex-col gap-1">
                          <label class="text-[10px] font-bold text-gray-500 uppercase">Points</label>
                          <input type="number" step="0.5" v-model="editingStagedQuestion.points" class="px-2 py-1.5 text-xs border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 focus:outline-none" />
                        </div>
                      </div>

                      <!-- Options editor (if MCQ / True-False / Multi-select) -->
                      <div v-if="['mcq', 'true_false', 'multi_select'].includes(editingStagedQuestion.question_type)" class="space-y-2">
                        <label class="text-[10px] font-bold text-gray-500 uppercase block">Options</label>
                        <div v-for="(opt, oIdx) in editingStagedQuestion.options" :key="oIdx" class="flex items-center gap-2">
                          <input type="checkbox" v-model="opt.is_correct" class="rounded text-blue-600" />
                          <input type="text" v-model="opt.text" class="flex-1 px-2 py-1 text-xs border border-gray-300 dark:border-gray-700 rounded bg-white dark:bg-gray-850" />
                        </div>
                      </div>

                      <div class="flex justify-end gap-2 pt-2">
                        <button @click="editingStagedId = null" class="px-3 py-1.5 bg-gray-200 dark:bg-gray-800 text-gray-700 dark:text-gray-300 text-[10px] font-bold rounded-lg hover:bg-gray-300">Cancel</button>
                        <button @click="saveStagedEdit" class="px-3 py-1.5 bg-blue-600 text-white text-[10px] font-bold rounded-lg hover:bg-blue-700">Save changes</button>
                      </div>
                    </div>

                    <!-- Read mode -->
                    <div v-else class="space-y-2">
                      <div class="text-xs text-gray-800 dark:text-gray-200 font-semibold" v-html="q.text"></div>
                      <div class="flex flex-wrap gap-2 text-[9px] font-bold">
                        <span class="px-1.5 py-0.5 bg-blue-50 dark:bg-blue-900/30 text-blue-600 rounded uppercase">{{ q.question_type }}</span>
                        <span class="px-1.5 py-0.5 bg-purple-50 dark:bg-purple-900/30 text-purple-600 rounded uppercase">Points: {{ q.points }}</span>
                        <span v-if="q.metadata?.page_num" class="px-1.5 py-0.5 bg-amber-50 dark:bg-amber-900/30 text-amber-600 rounded uppercase">Page: {{ q.metadata.page_num }}</span>
                      </div>

                      <!-- Options Preview -->
                      <div v-if="q.options && q.options.length > 0" class="pl-3 border-l-2 border-gray-200 dark:border-gray-800 space-y-1 mt-2">
                        <div v-for="(opt, oIdx) in q.options" :key="oIdx" class="text-[11px] flex items-center gap-1.5">
                          <span :class="[opt.is_correct ? 'text-emerald-500 font-bold' : 'text-gray-400']">{{ opt.is_correct ? '✓' : '•' }}</span>
                          <span :class="[opt.is_correct ? 'text-gray-900 dark:text-white font-semibold' : 'text-gray-650 dark:text-gray-450']">{{ opt.text }}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div class="flex items-center justify-between pt-3 border-t border-gray-150 dark:border-gray-800">
                  <span class="text-xs font-bold text-gray-500">{{ selectedStagedIds.length }} of {{ stagedQuestions.length }} selected</span>
                  <button
                    @click="handleApproveStaged"
                    :disabled="stagedApproving || selectedStagedIds.length === 0"
                    class="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-xl flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    <span v-if="stagedApproving" class="animate-spin inline-block w-3 h-3 border-2 border-white border-t-transparent rounded-full"></span>
                    {{ stagedApproving ? 'Approving...' : 'Confirm & Add to Assessment' }}
                  </button>
                </div>
              </div>
            </div>

            <!-- Manual Question Tab -->
            <div v-show="questionTab === 'manual'" class="space-y-4">
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div class="flex flex-col gap-1.5 sm:col-span-2">
                  <div class="flex items-center justify-between">
                    <label class="text-xs font-bold text-gray-700 dark:text-gray-300">Question Text</label>
                    <!-- WYSIWYG Formatter Toolbar -->
                    <div class="flex flex-wrap items-center gap-1 bg-gray-50 dark:bg-gray-800 p-1 rounded-xl border border-gray-250 dark:border-gray-700">
                      <button @click="insertManualText('<strong>', '</strong>')" type="button" title="Bold" class="px-1.5 py-0.5 text-[10px] font-bold hover:bg-gray-200 dark:hover:bg-gray-700 rounded text-gray-700 dark:text-gray-300">B</button>
                      <button @click="insertManualText('<em>', '</em>')" type="button" title="Italic" class="px-1.5 py-0.5 text-[10px] font-serif italic hover:bg-gray-200 dark:hover:bg-gray-700 rounded text-gray-700 dark:text-gray-300">I</button>
                      <button @click="insertManualText('<ul>\n  <li>', '</li>\n</ul>')" type="button" title="List" class="px-1.5 py-0.5 text-[10px] hover:bg-gray-200 dark:hover:bg-gray-700 rounded text-gray-700 dark:text-gray-300">FormatList</button>
                      <span class="w-px h-3 bg-gray-300 dark:bg-gray-650 mx-1"></span>
                      <button @click="insertManualText('√(', ')')" type="button" title="Square Root" class="px-1.5 py-0.5 text-[10px] hover:bg-gray-200 dark:hover:bg-gray-700 rounded font-mono text-gray-700 dark:text-gray-300">√</button>
                      <button @click="insertManualText('<sup>a</sup>&frasl;<sub>b</sub>')" type="button" title="Fraction" class="px-1.5 py-0.5 text-[10px] hover:bg-gray-200 dark:hover:bg-gray-700 rounded font-mono text-gray-700 dark:text-gray-300">½</button>
                      <button @click="insertManualText('π')" type="button" title="Pi" class="px-1.5 py-0.5 text-[10px] hover:bg-gray-200 dark:hover:bg-gray-700 rounded font-mono text-gray-700 dark:text-gray-300">π</button>
                      <button @click="insertManualText('∑')" type="button" title="Sum" class="px-1.5 py-0.5 text-[10px] hover:bg-gray-200 dark:hover:bg-gray-700 rounded font-mono text-gray-700 dark:text-gray-300">∑</button>
                      <span class="w-px h-3 bg-gray-300 dark:bg-gray-650 mx-1"></span>
                      <button @click="insertManualText('<img src=\'https://example.com/image.png\' class=\'my-4 max-w-full rounded-xl shadow-sm block\' />')" type="button" title="Insert Image" class="px-1.5 py-0.5 text-[10px] hover:bg-gray-200 dark:hover:bg-gray-700 rounded text-gray-700 dark:text-gray-300">InsertPhoto</button>
                    </div>
                  </div>
                  <textarea id="manual-q-textarea" v-model="manualQuestion.text" rows="3" placeholder="Enter the question here..." class="px-3 py-2 text-xs border border-gray-300 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none"></textarea>
                </div>
                <div class="flex flex-col gap-1.5">
                  <label class="text-xs font-bold text-gray-700 dark:text-gray-300">Question Type</label>
                  <select v-model="manualQuestion.question_type" class="px-3 py-2 text-xs border border-gray-300 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none">
                    <option value="mcq">Multiple Choice</option>
                    <option value="true_false">True / False</option>
                    <option value="short_answer">Short Answer</option>
                    <option value="essay">Essay / Freeform</option>
                  </select>
                </div>
                <div class="flex flex-col gap-1.5">
                  <label class="text-xs font-bold text-gray-700 dark:text-gray-300">Points</label>
                  <input type="number" step="0.5" v-model="manualQuestion.points" class="px-3 py-2 text-xs border border-gray-300 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none" />
                </div>
              </div>

              <!-- Options (for MCQ / True-False) -->
              <div v-if="['mcq', 'true_false'].includes(manualQuestion.question_type)" class="space-y-2">
                <div class="flex items-center justify-between">
                  <label class="text-xs font-bold text-gray-700 dark:text-gray-300">Options (Select the correct choice)</label>
                  <button v-if="manualQuestion.question_type === 'mcq'" @click="addManualOption" class="text-[10px] font-bold text-blue-600 hover:underline">+ Add Option</button>
                </div>
                <div v-for="(opt, oIdx) in manualQuestion.options" :key="oIdx" class="flex items-center gap-2">
                  <input type="radio" :checked="opt.is_correct" @change="setManualOptionCorrect(oIdx)" name="manual-correct-option" class="text-blue-600 focus:ring-blue-500" />
                  <input type="text" v-model="opt.text" placeholder="Option text" class="flex-1 px-3 py-1.5 text-xs border border-gray-300 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-850 text-gray-900 dark:text-white focus:outline-none" />
                  <button v-if="manualQuestion.question_type === 'mcq' && manualQuestion.options.length > 2" @click="removeManualOption(oIdx)" class="text-red-500 hover:text-red-700 text-xs">🗑️</button>
                </div>
              </div>

              <!-- Save to Bank Checkbox -->
              <div class="flex items-center gap-2 pt-2 pb-1">
                <input type="checkbox" id="save-to-bank" v-model="saveToBank" class="rounded border-gray-300 text-blue-600 focus:ring-blue-500" />
                <label for="save-to-bank" class="text-xs font-semibold text-gray-700 dark:text-gray-300 cursor-pointer">💾 Save this question to my Personal Question Bank</label>
              </div>

              <!-- Live Preview of manual question -->
              <div v-show="manualQuestion.text.trim()" class="p-4 bg-gray-50 dark:bg-gray-900 border border-dashed border-gray-300 dark:border-gray-700 rounded-xl space-y-2">
                <span class="text-[10px] font-bold text-gray-500 uppercase block">👁️ Question Live Preview</span>
                <div class="text-xs text-gray-800 dark:text-gray-200" v-html="manualQuestion.text"></div>
              </div>

              <button
                @click="handleAddManualQuestion"
                :disabled="manualSaving"
                class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-xl flex items-center justify-center gap-2 disabled:opacity-50"
              >
                <span v-if="manualSaving" class="animate-spin inline-block w-3 h-3 border-2 border-white border-t-transparent rounded-full"></span>
                💾 {{ manualSaving ? 'Saving...' : 'Save & Add Question' }}
              </button>
            </div>

            <!-- Question Bank Tab -->
            <div v-show="questionTab === 'bank'" class="space-y-4">
              <div class="flex flex-col gap-1.5">
                <label class="text-xs font-bold text-gray-700 dark:text-gray-300">Select Question Bank</label>
                <select v-model="selectedBankId" @change="loadBankQuestions" class="px-3 py-2 text-xs border border-gray-300 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none">
                  <option value="">-- Choose a Bank --</option>
                  <option v-for="bank in questionBanksList" :key="bank.id" :value="bank.id">{{ bank.name }} ({{ bank.question_count }} questions)</option>
                </select>
              </div>

              <!-- Questions in Selected Bank -->
              <div v-if="selectedBankQuestions.length > 0" class="space-y-3">
                <div class="flex items-center justify-between">
                  <label class="text-xs font-bold text-gray-700 dark:text-gray-300">Questions (Select to import)</label>
                  <button @click="selectAllBankQuestions" class="text-[10px] font-bold text-blue-600 hover:underline">
                    {{ selectedBankQuestionIds.length === selectedBankQuestions.length ? 'Clear Selection' : 'Select All' }}
                  </button>
                </div>
                <div class="max-h-[300px] overflow-y-auto pr-2 space-y-2">
                  <div v-for="q in selectedBankQuestions" :key="q.id" class="p-3 bg-gray-50 dark:bg-gray-900 border border-gray-250 dark:border-gray-800 rounded-xl flex items-start gap-3">
                    <input type="checkbox" :checked="selectedBankQuestionIds.includes(q.id)" @change="toggleBankQuestionSelect(q.id)" class="rounded text-blue-600 mt-0.5 cursor-pointer" />
                    <div class="flex-1 space-y-1">
                      <p class="text-xs text-gray-800 dark:text-gray-250" v-html="q.text"></p>
                      <div class="flex gap-2 text-[9px] font-bold text-gray-500 dark:text-gray-400 uppercase">
                        <span class="px-1.5 py-0.5 bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded">{{ q.question_type }}</span>
                        <span class="px-1.5 py-0.5 bg-purple-50 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 rounded">Points: {{ q.points }}</span>
                      </div>
                    </div>
                  </div>
                </div>
                <button
                  @click="handleImportFromBank"
                  class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-xl flex items-center justify-center gap-2"
                >
                  📥 Import {{ selectedBankQuestionIds.length }} Selected Questions
                </button>
              </div>
              <div v-else-if="selectedBankId && !loadingBankQuestions" class="text-center py-6 text-xs text-gray-500">
                No questions found in this bank.
              </div>
            </div>

          </div>

          <!-- Preview of added questions -->
          <div v-if="addedQuestions.length > 0" class="space-y-3">
            <h3 class="text-xs font-bold text-gray-500 uppercase">Assessment Questions Preview ({{ addedQuestions.length }})</h3>
            <div
              v-for="(q, idx) in addedQuestions"
              :key="idx"
              class="p-4 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl shadow-sm flex items-start justify-between gap-4"
            >
              <div class="space-y-1">
                <div class="flex items-center gap-2">
                  <span class="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 text-[9px] font-bold rounded uppercase">Question {{ idx + 1 }}</span>
                  <span class="px-1.5 py-0.5 bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 text-[9px] font-bold rounded uppercase">{{ q.question_type }}</span>
                </div>
                <p class="text-xs text-gray-800 dark:text-gray-200 mt-1 line-clamp-2">{{ q.text.replace(/<[^>]*>/g, '') }}</p>
              </div>
              <div class="flex items-center gap-3">
                <div class="flex flex-col gap-0.5">
                  <button
                    @click="moveQuestionUp(idx)"
                    :disabled="idx === 0"
                    class="p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded disabled:opacity-30 text-[9px] font-bold text-gray-500 dark:text-gray-400"
                    title="Move Up"
                  >
                    ▲
                  </button>
                  <button
                    @click="moveQuestionDown(idx)"
                    :disabled="idx === addedQuestions.length - 1"
                    class="p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded disabled:opacity-30 text-[9px] font-bold text-gray-500 dark:text-gray-400"
                    title="Move Down"
                  >
                    ▼
                  </button>
                </div>
                <button @click="removeQuestion(idx)" class="text-red-500 hover:text-red-755 text-[10px] font-bold">🗑️ Remove</button>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>

    <!-- Step 3: Proctoring Settings -->
    <div v-show="currentStep === 3" class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 space-y-4">
      <div v-if="!form.is_proctored" class="text-center py-6">
        <span class="text-2xl">🔓</span>
        <p class="text-xs font-bold text-gray-550 mt-2">Online Proctoring is disabled for this assessment.</p>
        <p class="text-[10px] text-gray-500 mt-0.5">Click "Back" to enable it in Details if needed, or proceed to "Review".</p>
      </div>

      <div v-else class="space-y-4">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <label class="flex items-center gap-2 cursor-pointer text-xs text-gray-700 dark:text-gray-300">
            <input type="checkbox" v-model="proctorForm.require_webcam" class="rounded border-gray-300 text-blue-600 focus:ring-blue-500" />
            Require Webcam Stream Recording
          </label>
          <label class="flex items-center gap-2 cursor-pointer text-xs text-gray-700 dark:text-gray-300">
            <input type="checkbox" v-model="proctorForm.require_microphone" class="rounded border-gray-300 text-blue-600 focus:ring-blue-500" />
            Require Microphone Stream Capture
          </label>
          <label class="flex items-center gap-2 cursor-pointer text-xs text-gray-700 dark:text-gray-300">
            <input type="checkbox" v-model="proctorForm.require_fullscreen" class="rounded border-gray-300 text-blue-600 focus:ring-blue-500" />
            Enforce Fullscreen Lockdown
          </label>
          <label class="flex items-center gap-2 cursor-pointer text-xs text-gray-700 dark:text-gray-300">
            <input type="checkbox" v-model="proctorForm.block_copy_paste" class="rounded border-gray-300 text-blue-600 focus:ring-blue-500" />
            Block Copy & Paste Operations
          </label>
          <label class="flex items-center gap-2 cursor-pointer text-xs text-gray-700 dark:text-gray-300">
            <input type="checkbox" v-model="proctorForm.block_right_click" class="rounded border-gray-300 text-blue-600 focus:ring-blue-500" />
            Block Right Click Context Menu
          </label>
          <label class="flex items-center gap-2 cursor-pointer text-xs text-gray-700 dark:text-gray-300">
            <input type="checkbox" v-model="proctorForm.block_devtools" class="rounded border-gray-300 text-blue-600 focus:ring-blue-500" />
            Block DevTools & Inspector Keys
          </label>
          <label class="flex items-center gap-2 cursor-pointer text-xs text-gray-700 dark:text-gray-300">
            <input type="checkbox" v-model="proctorForm.require_identity_verification" class="rounded border-gray-300 text-blue-600 focus:ring-blue-500" />
            Require Front Face Identity Photo
          </label>
          <label class="flex items-center gap-2 cursor-pointer text-xs text-gray-700 dark:text-gray-300">
            <input type="checkbox" v-model="proctorForm.ai_monitoring_enabled" class="rounded border-gray-300 text-blue-600 focus:ring-blue-500" />
            Enable Realtime Face & Audio AI Monitoring
          </label>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-3 border-t border-gray-150 dark:border-gray-800">
          <div class="flex flex-col gap-1">
            <label class="text-xs font-bold text-gray-700 dark:text-gray-300">Max Allowed Tab Switches</label>
            <input type="number" v-model="proctorForm.max_tab_switches" class="px-3 py-1.5 text-xs border border-gray-300 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-gray-900" />
          </div>
          <div class="flex flex-col gap-1">
            <label class="text-xs font-bold text-gray-700 dark:text-gray-300">Auto-submit Violation Threshold</label>
            <input type="number" v-model="proctorForm.auto_submit_on_violation_count" class="px-3 py-1.5 text-xs border border-gray-300 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-gray-900" />
          </div>
        </div>
      </div>
    </div>

    <!-- Step 4: Review and Publish -->
    <div v-show="currentStep === 4" class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 space-y-4">
      <div class="border-b border-gray-150 dark:border-gray-800 pb-3">
        <h3 class="text-sm font-bold text-gray-900 dark:text-white">Assessment Review Summary</h3>
        <p class="text-xs text-gray-500 mt-0.5">Please review your setup details before finalizing submission.</p>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-medium text-gray-700 dark:text-gray-300">
        <div>Title: <span class="text-gray-900 dark:text-white font-bold">{{ form.title }}</span></div>
        <div>Type: <span class="text-gray-900 dark:text-white font-bold uppercase">{{ form.assessment_type }}</span></div>
        <div>Total Questions: <span class="text-gray-900 dark:text-white font-bold">{{ form.questions_data.length }}</span></div>
        <div>Estimated Points: <span class="text-gray-900 dark:text-white font-bold">{{ form.questions_data.length * 5 }} pts</span></div>
        <div>Proctoring Status: <span class="text-gray-900 dark:text-white font-bold">{{ form.is_proctored ? '🛡️ Enabled' : 'Disabled' }}</span></div>
      </div>
    </div>

    <!-- Navigation Buttons -->
    <div class="flex justify-between items-center gap-4">
      <button
        v-if="currentStep > 1"
        @click="currentStep--"
        class="px-4 py-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 text-xs font-bold rounded-xl transition-all"
      >
        ◀ Back
      </button>
      <div class="flex-1"></div>
      
      <button
        v-if="currentStep < 4"
        @click="currentStep++"
        class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-xl transition-all"
      >
        Next Step ▶
      </button>
      
      <button
        v-else
        @click="handleSaveAssessment"
        :disabled="loading"
        class="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-xl shadow-md disabled:opacity-50 transition-all"
      >
        🚀 Create & Save Assessment
      </button>
    </div>
  </div>
</template>
