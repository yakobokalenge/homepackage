<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { assessmentService } from '@/services/assessment.service'
import api from '@/services/api'
import type { Assessment, ExtractedQuestionDraft } from '@/types/assessment'

const router = useRouter()

// Form states
const currentStep = ref(1)
const subjectsList = ref<any[]>([])
const classroomsList = ref<any[]>([])

const assessmentData = ref<Partial<Assessment>>({
  title: '',
  description: '',
  assessment_type: 'home_package',
  subject: '',
  classroom: '',
  duration_minutes: 60,
  pass_percentage: 50,
  status: 'draft'
})

// File state
const selectedFile = ref<File | null>(null)
const uploadProgress = ref(0)
const isExtracting = ref(false)
const extractionError = ref('')

// Draft questions state
const draftQuestions = ref<ExtractedQuestionDraft[]>([])
const activeDraftIndex = ref<number | null>(null)

// Step transitions & checks
function validateStep1() {
  return assessmentData.value.title && assessmentData.value.subject
}

async function startDocumentExtraction() {
  if (!selectedFile.value || !assessmentData.value.subject) return
  isExtracting.value = true
  extractionError.value = ''
  uploadProgress.value = 10
  
  try {
    const timer = setInterval(() => {
      if (uploadProgress.value < 90) uploadProgress.value += 10
    }, 400)

    const res = await assessmentService.extractDocument(
      selectedFile.value,
      assessmentData.value.subject
    )
    clearInterval(timer)
    uploadProgress.value = 100
    
    draftQuestions.value = res.questions || []
    currentStep.value = 3
    if (draftQuestions.value.length > 0) {
      activeDraftIndex.value = 0
    }
  } catch (err: any) {
    extractionError.value = err.response?.data?.error || 'Failed to parse the document. Please verify format and try again.'
  } finally {
    isExtracting.value = false
  }
}

// Review panel mutations
function editQuestionField(index: number, field: keyof ExtractedQuestionDraft, val: any) {
  if (draftQuestions.value[index]) {
    (draftQuestions.value[index] as any)[field] = val
  }
}

function editOptionField(qIndex: number, oIndex: number, field: string, val: any) {
  const question = draftQuestions.value[qIndex]
  if (question && question.options && question.options[oIndex]) {
    (question.options[oIndex] as any)[field] = val
  }
}

function removeQuestion(index: number) {
  draftQuestions.value.splice(index, 1)
  if (activeDraftIndex.value === index) {
    activeDraftIndex.value = draftQuestions.value.length > 0 ? 0 : null
  } else if (activeDraftIndex.value !== null && activeDraftIndex.value > index) {
    activeDraftIndex.value--
  }
}

function addNewQuestion() {
  draftQuestions.value.push({
    text: 'New Question text here...',
    question_type: 'mcq',
    difficulty: 'medium',
    points: 5.0,
    options: [
      { text: 'Option A', is_correct: true, order: 1 },
      { text: 'Option B', is_correct: false, order: 2 }
    ]
  })
  activeDraftIndex.value = draftQuestions.value.length - 1
}

function toggleMCQCorrect(qIdx: number, oIdx: number) {
  const question = draftQuestions.value[qIdx]
  if (!question || !question.options) return
  
  if (question.question_type === 'mcq' || question.question_type === 'true_false') {
    // Single correct selection logic
    question.options.forEach((opt, idx) => {
      opt.is_correct = idx === oIdx
    })
  } else {
    // Multi-select logic
    question.options[oIdx].is_correct = !question.options[oIdx].is_correct
  }
}

// Final save
const isSaving = ref(false)
async function finalizeAssessment() {
  isSaving.value = true
  try {
    // 1. Create Assessment Draft
    const createdAss = await assessmentService.create(assessmentData.value)
    
    // 2. Link validated questions
    await assessmentService.saveExtracted(createdAss.id, draftQuestions.value)
    
    // 3. Publish if chosen
    if (assessmentData.value.status === 'published') {
      await assessmentService.update(createdAss.id, { status: 'published' })
    }
    
    alert('Assessment successfully saved and linked to Question Bank!')
    router.push('/teacher/dashboard')
  } catch (err) {
    alert('Failed to finalize assessment. Please review question formatting.')
  } finally {
    isSaving.value = false
  }
}

onMounted(async () => {
  try {
    const subjectsRes = await api.get('/content/subjects/')
    subjectsList.value = Array.isArray(subjectsRes.data) ? subjectsRes.data : subjectsRes.data?.results || []

    const classroomsRes = await api.get('/schools/classrooms/')
    classroomsList.value = Array.isArray(classroomsRes.data) ? classroomsRes.data : classroomsRes.data?.results || []
  } catch (err) {
    console.error('Failed to load classes or subjects:', err)
  }
})
</script>

<template>
  <div class="max-w-6xl mx-auto space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between border-b border-gray-200 dark:border-gray-800 pb-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Document-to-Assessment Generator</h1>
        <p class="text-sm text-gray-500 mt-1">Convert raw question sheets into interactive online assessments instantly.</p>
      </div>
      <div class="flex items-center gap-2">
        <span v-for="step in 4" :key="step" :class="['w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs transition-all', currentStep === step ? 'bg-blue-600 text-white shadow-lg' : currentStep > step ? 'bg-emerald-100 text-emerald-700' : 'bg-gray-100 text-gray-400']">
          {{ step }}
        </span>
      </div>
    </div>

    <!-- Step 1: Metadata Setup -->
    <div v-if="currentStep === 1" class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 space-y-6">
      <h2 class="text-lg font-bold text-gray-900 dark:text-white border-b border-gray-100 dark:border-gray-850 pb-2">Step 1: Setup Assessment Metadata</h2>
      
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div class="space-y-1">
          <label class="text-sm font-semibold text-gray-700 dark:text-gray-300">Assessment Title *</label>
          <input v-model="assessmentData.title" placeholder="e.g. Form 2 Mathematics Midterm" class="w-full px-4 py-2 border border-gray-350 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-850 text-sm focus:outline-none" />
        </div>

        <div class="space-y-1">
          <label class="text-sm font-semibold text-gray-700 dark:text-gray-300">Assessment Type</label>
          <select v-model="assessmentData.assessment_type" class="w-full px-4 py-2 border border-gray-350 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-850 text-sm focus:outline-none">
            <option value="home_package">Home Package</option>
            <option value="assignment">Assignment</option>
            <option value="quiz">Quiz</option>
            <option value="test">Test</option>
            <option value="exam">Examination</option>
          </select>
        </div>

        <div class="space-y-1">
          <label class="text-sm font-semibold text-gray-700 dark:text-gray-300">Subject Link *</label>
          <select v-model="assessmentData.subject" class="w-full px-4 py-2 border border-gray-350 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-850 text-sm focus:outline-none">
            <option value="">Select Subject</option>
            <option v-for="sub in subjectsList" :key="sub.id" :value="sub.id">{{ sub.name }}</option>
          </select>
        </div>

        <div class="space-y-1">
          <label class="text-sm font-semibold text-gray-700 dark:text-gray-300">Target Classroom Stream</label>
          <select v-model="assessmentData.classroom" class="w-full px-4 py-2 border border-gray-350 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-850 text-sm focus:outline-none">
            <option value="">All Streams (Public)</option>
            <option v-for="cls in classroomsList" :key="cls.id" :value="cls.id">{{ cls.name }} - {{ cls.stream }}</option>
          </select>
        </div>

        <div class="space-y-1">
          <label class="text-sm font-semibold text-gray-700 dark:text-gray-300">Time Limit (Minutes)</label>
          <input type="number" v-model="assessmentData.duration_minutes" class="w-full px-4 py-2 border border-gray-350 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-850 text-sm focus:outline-none" />
        </div>

        <div class="space-y-1">
          <label class="text-sm font-semibold text-gray-700 dark:text-gray-300">Pass Percentage (%)</label>
          <input type="number" v-model="assessmentData.pass_percentage" class="w-full px-4 py-2 border border-gray-350 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-850 text-sm focus:outline-none" />
        </div>
      </div>

      <div class="flex justify-end pt-4">
        <button @click="currentStep = 2" :disabled="!validateStep1()" class="px-6 py-2.5 bg-blue-600 disabled:opacity-50 text-white font-semibold rounded-xl text-sm transition-all hover:bg-blue-700 shadow-md">
          Next: Upload Document
        </button>
      </div>
    </div>

    <!-- Step 2: Upload File Panel -->
    <div v-if="currentStep === 2" class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 space-y-6">
      <div class="flex justify-between items-center border-b border-gray-100 dark:border-gray-850 pb-2">
        <h2 class="text-lg font-bold text-gray-900 dark:text-white">Step 2: Upload Exam Document Sheet</h2>
        <button @click="currentStep = 1" class="text-xs font-semibold text-gray-500 hover:underline">Back</button>
      </div>

      <div class="border-2 border-dashed border-gray-300 dark:border-gray-700 rounded-2xl p-12 text-center flex flex-col items-center justify-center space-y-4 hover:border-blue-500 transition-colors relative">
        <span class="text-5xl">📄</span>
        <div>
          <p class="font-bold text-gray-800 dark:text-white text-base">Select Question Sheet PDF, DOCX, or TXT</p>
          <p class="text-xs text-gray-500 mt-1">Upload the file you want the Extraction Engine to convert.</p>
        </div>
        <input type="file" @change="(e: any) => selectedFile = e.target.files[0]" accept=".pdf,.docx,.doc,.txt" class="absolute inset-0 opacity-0 cursor-pointer" />
        
        <div v-if="selectedFile" class="p-3 bg-blue-50 dark:bg-blue-950/20 border border-blue-150 rounded-xl text-xs font-bold text-blue-700 dark:text-blue-400">
          Selected: {{ selectedFile.name }} ({{ Math.round(selectedFile.size / 1024) }} KB)
        </div>
      </div>

      <!-- Loading / Extraction Progress Loader -->
      <div v-if="isExtracting" class="p-6 bg-gray-50 dark:bg-gray-850 rounded-2xl flex flex-col items-center justify-center space-y-3">
        <span class="animate-spin inline-block w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full"></span>
        <p class="text-sm font-semibold text-gray-900 dark:text-white">Extraction Engine Active...</p>
        <div class="w-full max-w-md bg-gray-200 dark:bg-gray-700 h-2 rounded-full overflow-hidden">
          <div class="h-full bg-blue-600 transition-all duration-300" :style="{ width: `${uploadProgress}%` }"></div>
        </div>
        <p class="text-xs text-gray-500">Converting text layout and validating questions via AI...</p>
      </div>

      <div v-if="extractionError" class="p-4 bg-red-100 border border-red-200 rounded-xl text-xs font-semibold text-red-700">
        ⚠️ {{ extractionError }}
      </div>

      <div class="flex justify-end pt-4">
        <button @click="startDocumentExtraction" :disabled="!selectedFile || isExtracting" class="px-6 py-2.5 bg-blue-600 disabled:opacity-50 text-white font-semibold rounded-xl text-sm transition-all hover:bg-blue-700 shadow-md">
          Start Question Extraction
        </button>
      </div>
    </div>

    <!-- Step 3: Teacher Review & Edit Screen -->
    <div v-if="currentStep === 3" class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Left sidebar question selector list -->
      <div class="lg:col-span-1 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-4 flex flex-col justify-between max-h-[80vh] overflow-hidden">
        <div class="space-y-4 flex-1 overflow-y-auto pr-1">
          <div class="flex justify-between items-center pb-2 border-b border-gray-100 dark:border-gray-800">
            <h3 class="font-bold text-gray-900 dark:text-white text-sm">Extracted Drafts</h3>
            <span class="px-2 py-0.5 bg-gray-100 dark:bg-gray-800 rounded text-xs font-bold text-gray-600">{{ draftQuestions.length }} questions</span>
          </div>

          <div class="space-y-2">
            <div v-for="(q, idx) in draftQuestions" :key="idx" @click="activeDraftIndex = idx" :class="['p-3 rounded-xl cursor-pointer border text-left transition-all', activeDraftIndex === idx ? 'bg-blue-50 border-blue-200 dark:bg-blue-950/20 dark:border-blue-900' : 'bg-gray-50 border-gray-100 hover:bg-gray-100 dark:bg-gray-850 dark:border-gray-800']">
              <div class="flex justify-between items-center text-xs mb-1.5">
                <span class="font-bold text-gray-600 dark:text-gray-400">Q{{ idx + 1 }}</span>
                <span class="px-1.5 py-0.5 bg-indigo-50 dark:bg-indigo-950/30 text-indigo-600 text-[10px] rounded uppercase font-semibold">{{ q.question_type }}</span>
              </div>
              <p class="text-xs text-gray-900 dark:text-white font-medium line-clamp-2" v-html="q.text"></p>
            </div>
          </div>
        </div>

        <div class="pt-4 border-t border-gray-200 dark:border-gray-800 flex gap-2">
          <button @click="addNewQuestion" class="flex-1 py-2 border border-gray-300 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-850 text-gray-700 dark:text-gray-300 font-semibold rounded-xl text-xs transition-all">
            + Add Question
          </button>
          <button @click="currentStep = 4" class="flex-1 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl text-xs transition-all">
            Save & Next
          </button>
        </div>
      </div>

      <!-- Right main question editor workspace -->
      <div class="lg:col-span-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 overflow-y-auto max-h-[80vh]">
        <div v-if="activeDraftIndex === null || draftQuestions.length === 0" class="text-center py-24 text-gray-500">
          <span class="text-4xl block mb-2">📋</span>
          Select or add a question to start editing.
        </div>
        
        <div v-else class="space-y-6">
          <div class="flex justify-between items-center border-b border-gray-150 dark:border-gray-800 pb-3">
            <h3 class="font-bold text-gray-900 dark:text-white text-base">Edit Question {{ activeDraftIndex + 1 }}</h3>
            <button @click="removeQuestion(activeDraftIndex)" class="px-3 py-1.5 bg-red-50 text-red-650 hover:bg-red-100 rounded-lg text-xs font-bold transition-all">
              ✕ Delete Question
            </button>
          </div>
          <div class="space-y-4">
            <div class="space-y-1">
              <label class="text-xs font-semibold text-gray-600">Question Content (HTML/LaTeX supported) *</label>
              <textarea v-model="draftQuestions[activeDraftIndex].text" rows="4" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-750 rounded-xl bg-white dark:bg-gray-850 text-xs focus:outline-none focus:border-blue-500 font-mono"></textarea>
            </div>

            <!-- Live Render Preview Card -->
            <div class="p-4 bg-gray-50 dark:bg-gray-850 border border-gray-150 dark:border-gray-800 rounded-2xl space-y-2">
              <span class="text-[10px] font-bold text-gray-400 dark:text-gray-500 uppercase tracking-wider block">Live Preview</span>
              <div class="text-sm text-gray-900 dark:text-white leading-relaxed whitespace-pre-line" v-html="draftQuestions[activeDraftIndex].text"></div>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div class="space-y-1">
                <label class="text-xs font-semibold text-gray-600">Question Type</label>
                <select v-model="draftQuestions[activeDraftIndex].question_type" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-750 rounded-xl bg-white dark:bg-gray-850 text-xs focus:outline-none">
                  <option value="mcq">Multiple Choice (MCQ)</option>
                  <option value="true_false">True / False</option>
                  <option value="fill_blank">Fill in the Blank</option>
                  <option value="short_answer">Short Answer</option>
                  <option value="essay">Essay Question</option>
                </select>
              </div>

              <div class="space-y-1">
                <label class="text-xs font-semibold text-gray-600">Marks / Points</label>
                <input type="number" v-model="draftQuestions[activeDraftIndex].points" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-750 rounded-xl bg-white dark:bg-gray-850 text-xs focus:outline-none" />
              </div>
            </div>

            <!-- Options Block for MCQ and True/False -->
            <div v-if="['mcq', 'true_false'].includes(draftQuestions[activeDraftIndex].question_type)" class="space-y-3 pt-3 border-t border-gray-100 dark:border-gray-850">
              <h4 class="text-xs font-bold text-gray-800 dark:text-gray-200">Answer Options</h4>
              
              <div class="space-y-2">
                <div v-for="(opt, oIdx) in draftQuestions[activeDraftIndex].options" :key="oIdx" class="flex items-center gap-3">
                  <button @click="toggleMCQCorrect(activeDraftIndex!, oIdx)" :class="['w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold text-white border transition-all', opt.is_correct ? 'bg-emerald-500 border-emerald-500' : 'border-gray-300 dark:border-gray-700 hover:bg-gray-50']">
                    {{ opt.is_correct ? '✓' : '' }}
                  </button>
                  <input v-model="opt.text" placeholder="Option text" class="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-750 rounded-xl bg-white dark:bg-gray-850 text-xs focus:outline-none" />
                </div>
              </div>
            </div>

            <!-- Explanation / Correction notes -->
            <div class="space-y-1">
              <label class="text-xs font-semibold text-gray-600">Model Answer Explanation (Visible to students during correction review)</label>
              <textarea v-model="draftQuestions[activeDraftIndex].explanation" rows="2" placeholder="e.g. Mars has rich iron oxide content giving it a reddish appearance." class="w-full px-3 py-2 border border-gray-300 dark:border-gray-750 rounded-xl bg-white dark:bg-gray-850 text-xs focus:outline-none"></textarea>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Step 4: Finalize and Publish -->
    <div v-if="currentStep === 4" class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 space-y-6">
      <div class="flex justify-between items-center border-b border-gray-100 dark:border-gray-850 pb-2">
        <h2 class="text-lg font-bold text-gray-900 dark:text-white">Step 4: Finalize & Save to Question Bank</h2>
        <button @click="currentStep = 3" class="text-xs font-semibold text-gray-500 hover:underline">Back to Review</button>
      </div>

      <div class="p-6 bg-gray-50 dark:bg-gray-850 rounded-2xl max-w-lg mx-auto border border-gray-150 dark:border-gray-800 space-y-4">
        <h3 class="font-bold text-center text-gray-800 dark:text-white text-base">Assessment Setup Review</h3>
        
        <div class="divide-y divide-gray-200 dark:divide-gray-800 text-xs space-y-3">
          <div class="flex justify-between pt-2">
            <span class="text-gray-500 font-medium">Title:</span>
            <span class="font-bold text-gray-900 dark:text-white">{{ assessmentData.title }}</span>
          </div>
          <div class="flex justify-between pt-2">
            <span class="text-gray-500 font-medium">Class Stream Target:</span>
            <span class="font-bold text-gray-900 dark:text-white">
              {{ classroomsList.find(c => c.id === assessmentData.classroom)?.name || 'All Streams (Public)' }}
            </span>
          </div>
          <div class="flex justify-between pt-2">
            <span class="text-gray-500 font-medium">Time Limit:</span>
            <span class="font-bold text-gray-900 dark:text-white">{{ assessmentData.duration_minutes }} Minutes</span>
          </div>
          <div class="flex justify-between pt-2">
            <span class="text-gray-500 font-medium">Validated Questions:</span>
            <span class="font-bold text-blue-600">{{ draftQuestions.length }} Items</span>
          </div>
        </div>

        <div class="pt-4 space-y-2">
          <label class="text-xs font-bold text-gray-700">Set Initial Status</label>
          <div class="flex gap-4">
            <label class="flex items-center gap-2 text-xs font-semibold text-gray-600 dark:text-gray-400 cursor-pointer">
              <input type="radio" v-model="assessmentData.status" value="draft" />
              Save as Draft
            </label>
            <label class="flex items-center gap-2 text-xs font-semibold text-gray-600 dark:text-gray-400 cursor-pointer">
              <input type="radio" v-model="assessmentData.status" value="published" />
              Publish Immediately (Visible to students)
            </label>
          </div>
        </div>
      </div>

      <div class="flex justify-end pt-4 gap-3">
        <button @click="currentStep = 3" class="px-5 py-2 border border-gray-300 dark:border-gray-700 hover:bg-gray-50 text-gray-700 dark:text-gray-300 font-semibold rounded-xl text-sm transition-all">
          Back
        </button>
        <button @click="finalizeAssessment" :disabled="isSaving" class="px-6 py-2.5 bg-gradient-to-r from-blue-600 to-emerald-600 disabled:opacity-50 text-white font-semibold rounded-xl text-sm transition-all shadow-md flex items-center gap-2">
          <span v-if="isSaving" class="animate-spin inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full"></span>
          Confirm & Save Assessment
        </button>
      </div>
    </div>
  </div>
</template>
