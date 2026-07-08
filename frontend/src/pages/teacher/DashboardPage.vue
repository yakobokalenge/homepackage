<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'
import api from '@/services/api'

const { t } = useI18n()
const auth = useAuthStore()

// State
const loading = ref(true)
const stats = ref([
  { icon: '👨‍🎓', label: 'Total Students', value: '0', trend: 'Unique students', color: 'from-blue-500 to-blue-600' },
  { icon: '📝', label: 'Assessments Created', value: '0', trend: 'Active exams', color: 'from-emerald-500 to-emerald-600' },
  { icon: '📊', label: 'Avg Class Score', value: '0%', trend: 'Class average', color: 'from-amber-500 to-amber-600' },
  { icon: '🔒', label: 'Proctored Exams', value: '0', trend: 'Security enabled', color: 'from-purple-500 to-purple-600' },
])

const recentSubmissions = ref<any[]>([])
const classPerformance = ref<any[]>([])
const commonMistakes = ref<any[]>([])
const classroomsList = ref<any[]>([])
const assessmentsList = ref<any[]>([])

const groupedAssessments = computed(() => {
  const groups: Record<string, any[]> = {
    'home_package': [],
    'assignment': [],
    'quiz': [],
    'test': [],
    'exam': []
  }
  
  assessmentsList.value.forEach(ass => {
    const type = ass.type || 'home_package'
    if (!groups[type]) {
      groups[type] = []
    }
    groups[type].push(ass)
  })
  
  return groups
})

const previewingAssessment = ref<any | null>(null)
const previewingQuestions = ref<any[]>([])
const showPreviewModal = ref(false)
const loadingPreview = ref(false)

async function previewAssessmentQuestions(ass: any) {
  previewingAssessment.value = ass
  showPreviewModal.value = true
  loadingPreview.value = true
  previewingQuestions.value = []
  
  try {
    const res = await api.get(`/assessments/${ass.id}/questions/`)
    previewingQuestions.value = Array.isArray(res.data) ? res.data : res.data?.results || []
  } catch (err) {
    console.error('Failed to load preview questions:', err)
  } finally {
    loadingPreview.value = false
  }
}

function deleteAssessment(id: string) {
  if (!confirm('Are you sure you want to delete this assessment? This will remove all attempts and student responses associated with it.')) return
  api.delete(`/assessments/${id}/`)
    .then(() => {
      alert('Assessment deleted successfully.')
      assessmentsList.value = assessmentsList.value.filter(a => a.id !== id)
      stats.value[1].value = String(Math.max(0, Number(stats.value[1].value) - 1))
    })
    .catch((err) => {
      alert('Failed to delete assessment.')
      console.error(err)
    })
}

function downloadClassroomCSV(classId: string, className: string) {
  api.get(`/schools/classrooms/${classId}/download_results/`, { responseType: 'blob' })
    .then((response) => {
      const blob = new Blob([response.data], { type: 'text/csv' })
      const link = document.createElement('a')
      link.href = window.URL.createObjectURL(blob)
      link.download = `results_class_${className.replace(/\s+/g, '_')}.csv`
      link.click()
    })
    .catch((err) => {
      console.error('Failed to download results:', err)
    })
}

function formatTimeAgo(dateString: string) {
  if (!dateString) return '—'
  const date = new Date(dateString)
  const seconds = Math.floor((new Date().getTime() - date.getTime()) / 1000)
  
  let interval = Math.floor(seconds / 31536000)
  if (interval >= 1) return `${interval}y ago`
  interval = Math.floor(seconds / 2592000)
  if (interval >= 1) return `${interval}mo ago`
  interval = Math.floor(seconds / 86400)
  if (interval >= 1) return `${interval}d ago`
  interval = Math.floor(seconds / 3600)
  if (interval >= 1) return `${interval}h ago`
  interval = Math.floor(seconds / 60)
  if (interval >= 1) return `${interval}m ago`
  return 'just now'
}

onMounted(async () => {
  try {
    // Fetch Teacher Analytics Stats
    const { data: performance } = await api.get('/analytics/teacher/')
    stats.value[0].value = String(performance.total_students)
    stats.value[1].value = String(performance.assessments_created)
    stats.value[2].value = `${performance.average_score}%`
    stats.value[3].value = String(performance.proctored_exams)
    classPerformance.value = performance.by_assessment || []
    commonMistakes.value = performance.common_mistakes || []

    // Fetch Classrooms List
    const classroomsRes = await api.get('/schools/classrooms/')
    const rawClassrooms = Array.isArray(classroomsRes.data) ? classroomsRes.data : classroomsRes.data?.results || []
    const seenCls = new Set()
    classroomsList.value = rawClassrooms.filter((item: any) => {
      const key = `${item.name}-${item.stream}`
      if (seenCls.has(key)) return false
      seenCls.add(key)
      return true
    })

    // Fetch Assessments List
    const assessmentsRes = await api.get('/assessments/')
    assessmentsList.value = Array.isArray(assessmentsRes.data) ? assessmentsRes.data : assessmentsRes.data?.results || []

    // 2. Fetch Recent Submissions
    const { data: attempts } = await api.get('/attempts/')
    let rawAttempts = Array.isArray(attempts) ? attempts : attempts.results || []
    recentSubmissions.value = rawAttempts.slice(0, 5).map((a: any) => ({
      id: a.id,
      student: a.student_name || 'Student',
      assessment: a.assessment_title || 'Exam',
      score: a.percentage !== null && a.percentage !== undefined ? `${Math.round(a.percentage)}%` : '—',
      status: a.status,
      time: formatTimeAgo(a.submitted_at || a.started_at)
    }))

  } catch (err) {
    console.error('Failed to load teacher dashboard details:', err)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="space-y-6">
    <!-- Welcome + Quick Actions -->
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">{{ t('dashboard.welcome') }} {{ auth.user?.first_name }}! 👋</h1>
        <p class="text-gray-500 text-sm mt-1">Here's your class overview for today.</p>
      </div>
      <RouterLink to="/teacher/assessments/create" class="px-5 py-2.5 bg-gradient-to-r from-blue-600 to-emerald-600 text-white font-semibold rounded-xl hover:shadow-lg transition-all text-sm">
        + {{ t('common.create') }} Assessment
      </RouterLink>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-20 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl">
      <span class="animate-spin inline-block w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mb-4"></span>
      <p class="text-gray-500">Loading Dashboard Metrics...</p>
    </div>

    <template v-else>
      <!-- Stats -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div v-for="stat in stats" :key="stat.label" class="bg-white dark:bg-gray-900 rounded-2xl p-5 border border-gray-200 dark:border-gray-800 hover:shadow-lg transition-shadow">
          <div :class="['w-10 h-10 rounded-xl bg-gradient-to-br flex items-center justify-center text-lg mb-3 text-white', stat.color]">{{ stat.icon }}</div>
          <p class="text-2xl font-bold text-gray-900 dark:text-white">{{ stat.value }}</p>
          <p class="text-xs text-gray-500 mt-1">{{ stat.label }}</p>
          <p class="text-xs text-blue-600 dark:text-blue-400 mt-1">{{ stat.trend }}</p>
        </div>
      </div>

      <!-- Submissions and Classroom Roster Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
        <!-- Recent Submissions Table (col-span-2) -->
        <div class="lg:col-span-2 bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 overflow-hidden">
          <div class="p-6 border-b border-gray-200 dark:border-gray-800 flex justify-between items-center">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Recent Submissions</h2>
          </div>
          
          <div v-if="recentSubmissions.length === 0" class="text-center py-12 text-gray-500">
            <span class="text-3xl block mb-2">📁</span>
            No student submissions recorded yet.
          </div>
          
          <div v-else class="overflow-x-auto">
            <table class="w-full">
              <thead class="bg-gray-50 dark:bg-gray-800/50">
                <tr>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Student</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Assessment</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Score</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Time</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-200 dark:divide-gray-800">
                <tr v-for="sub in recentSubmissions" :key="sub.id" class="hover:bg-gray-50 dark:hover:bg-gray-800/30 transition-colors">
                  <td class="px-6 py-4 text-sm font-medium text-gray-900 dark:text-white">{{ sub.student }}</td>
                  <td class="px-6 py-4 text-sm text-gray-500">{{ sub.assessment }}</td>
                  <td class="px-6 py-4 text-sm font-semibold" :class="sub.score !== '—' ? 'text-gray-900 dark:text-white' : 'text-gray-400'">{{ sub.score }}</td>
                  <td class="px-6 py-4">
                    <span :class="['px-2.5 py-1 text-xs font-medium rounded-full uppercase', sub.status === 'graded' || sub.status === 'GRADED' ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400' : 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400']">
                      {{ sub.status }}
                    </span>
                  </td>
                  <td class="px-6 py-4 text-sm text-gray-500">{{ sub.time }}</td>
                  <td class="px-6 py-4 text-sm">
                    <RouterLink :to="`/teacher/attempts/${sub.id}/grade`" class="text-blue-600 dark:text-blue-400 hover:underline font-medium">
                      Grade
                    </RouterLink>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Classrooms Data Export Panel (col-span-1) -->
        <div class="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-6 space-y-4">
          <div>
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Class Roster & Results</h2>
            <p class="text-xs text-gray-500 mt-1">Download Excel-compatible CSV student gradebooks for school information systems.</p>
          </div>
          <div v-if="classroomsList.length === 0" class="text-center py-6 text-gray-500">
            <span class="text-2xl block mb-1">🏫</span>
            No classrooms found.
          </div>
          <div v-else class="space-y-3 max-h-[350px] overflow-y-auto pr-1">
            <div v-for="cls in classroomsList" :key="cls.id" class="p-3 bg-gray-50 dark:bg-gray-800/40 border border-gray-100 dark:border-gray-800 rounded-xl flex items-center justify-between gap-2 hover:border-blue-400 transition-colors">
              <div class="min-w-0">
                <p class="text-sm font-semibold text-gray-900 dark:text-white truncate">{{ cls.name }}</p>
                <p class="text-xs text-gray-500">Stream: {{ cls.stream }} · Year: {{ cls.academic_year }}</p>
              </div>
              <button @click="downloadClassroomCSV(cls.id, cls.name)" class="flex-shrink-0 px-3 py-1.5 bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 hover:bg-blue-100 dark:hover:bg-blue-900/50 rounded-xl text-xs font-bold transition-all">
                📥 CSV
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Assessments Created Workspace Grouped by Type -->
      <div class="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 overflow-hidden mt-6 shadow-sm">
        <div class="p-6 border-b border-gray-200 dark:border-gray-800 flex justify-between items-center">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Active Assessments & Homework</h2>
        </div>
        
        <div v-if="assessmentsList.length === 0" class="text-center py-12 text-gray-500">
          <span class="text-3xl block mb-2">📝</span>
          No assessments created yet. Click "+ Create Assessment" above to make your first one.
        </div>
        
        <div v-else class="p-6 space-y-6">
          <div v-for="(list, type) in groupedAssessments" :key="type" class="space-y-3">
            <div v-if="list.length > 0">
              <h3 class="text-xs font-bold text-gray-800 dark:text-gray-200 uppercase tracking-wider flex items-center gap-2">
                <span class="text-lg">{{ type === 'home_package' ? '🏠' : type === 'quiz' ? '📝' : type === 'assignment' ? '✍️' : type === 'test' ? '🧪' : '🎓' }}</span>
                {{ type === 'home_package' ? 'Home Packages' : type === 'quiz' ? 'Quizzes' : type === 'assignment' ? 'Assignments' : type === 'test' ? 'Tests' : 'Exams' }}
                <span class="px-2 py-0.5 bg-gray-150 dark:bg-gray-800 rounded-full text-xs font-bold text-gray-500 dark:text-gray-400">{{ list.length }}</span>
              </h3>
              
              <div class="overflow-x-auto border border-gray-100 dark:border-gray-800 rounded-xl mt-2">
                <table class="w-full text-left text-sm">
                  <thead class="bg-gray-50 dark:bg-gray-850 text-gray-500 font-semibold border-b border-gray-200 dark:border-gray-800">
                    <tr>
                      <th class="px-6 py-3">Assessment Title</th>
                      <th class="px-6 py-3">Subject Name</th>
                      <th class="px-6 py-3">Class Target</th>
                      <th class="px-6 py-3">Question Limit</th>
                      <th class="px-6 py-3">Status</th>
                      <th class="px-6 py-3">Actions</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-gray-200 dark:divide-gray-800 text-gray-900 dark:text-gray-150">
                    <tr v-for="ass in list" :key="ass.id" class="hover:bg-gray-50 dark:hover:bg-gray-850">
                      <td class="px-6 py-4 font-semibold">{{ ass.title }}</td>
                      <td class="px-6 py-4 font-medium text-indigo-650 dark:text-indigo-400">{{ ass.subject_name || 'N/A' }}</td>
                      <td class="px-6 py-4">{{ ass.classroom_name || 'All Streams' }}</td>
                      <td class="px-6 py-4">{{ ass.questions_limit || 'Unlimited' }} questions</td>
                      <td class="px-6 py-4">
                        <span :class="['px-2.5 py-0.5 text-xs font-bold rounded-full uppercase', ass.status === 'published' || ass.status === 'active' ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-400' : 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400']">
                          {{ ass.status }}
                        </span>
                      </td>
                      <td class="px-6 py-4 space-x-3">
                        <button @click="previewAssessmentQuestions(ass)" class="text-xs font-bold text-indigo-600 hover:underline">
                          Review Questions
                        </button>
                        <button @click="deleteAssessment(ass.id)" class="text-xs font-bold text-red-650 hover:underline">
                          Delete
                        </button>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Class Performance Analytics -->
      <div class="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 overflow-hidden mt-6">
        <div class="p-6 border-b border-gray-200 dark:border-gray-800">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Class Performance by Assessment</h2>
        </div>
        <div v-if="classPerformance.length === 0" class="text-center py-12 text-gray-500">
          <span class="text-3xl block mb-2">📊</span>
          No class performance metrics available yet.
        </div>
        <div v-else class="p-6 space-y-4">
          <div v-for="item in classPerformance" :key="item.assessment__title" class="flex flex-col sm:flex-row justify-between sm:items-center gap-2 p-4 rounded-xl bg-gray-50 dark:bg-gray-800/40 border border-gray-100 dark:border-gray-800">
            <div>
              <p class="font-semibold text-gray-900 dark:text-white">{{ item.assessment__title }}</p>
              <p class="text-xs text-gray-500">Total Submissions: {{ item.total }}</p>
            </div>
            <div class="flex items-center gap-3">
              <span class="text-xs text-gray-500">Class Average:</span>
              <span class="px-3 py-1 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 font-bold rounded-lg text-sm border border-blue-100 dark:border-blue-900/20">
                {{ Math.round(item.avg_score) }}%
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Common Classroom Mistakes -->
      <div class="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 overflow-hidden mt-6">
        <div class="p-6 border-b border-gray-200 dark:border-gray-800">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Common Classroom Mistakes</h2>
          <p class="text-xs text-gray-500 mt-1">Questions most frequently answered incorrectly by students.</p>
        </div>
        <div v-if="commonMistakes.length === 0" class="text-center py-12 text-gray-500">
          <span class="text-3xl block mb-2">💡</span>
          No common mistakes identified yet. Great job class!
        </div>
        <div v-else class="p-6 space-y-4">
          <div v-for="(mistake, idx) in commonMistakes" :key="idx" class="p-4 rounded-xl bg-red-50/30 dark:bg-red-950/10 border border-red-100/30 dark:border-red-900/20 flex justify-between items-start gap-4">
            <div class="space-y-1">
              <span class="px-2 py-0.5 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 text-xs font-bold rounded-full">
                {{ mistake.question__subject__name }}
              </span>
              <p class="text-sm font-medium text-gray-900 dark:text-white" v-html="mistake.question__text"></p>
            </div>
            <div class="text-right">
              <span class="px-3 py-1 bg-red-100 text-red-700 font-bold rounded-lg text-xs whitespace-nowrap">
                {{ mistake.wrong_count }} Wrong Answers
              </span>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- Review Assessment Questions Modal -->
    <Teleport to="body">
      <div v-if="showPreviewModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4" @click.self="showPreviewModal = false">
        <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-3xl max-w-2xl w-full max-h-[85vh] overflow-y-auto p-6 shadow-2xl space-y-6 flex flex-col justify-between">
          <div class="space-y-4">
            <div class="flex justify-between items-center border-b border-gray-150 dark:border-gray-800 pb-4">
              <div>
                <h3 class="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
                  <span>🔍</span> Review Assessment Questions
                </h3>
                <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">Reviewing: <span class="font-semibold text-indigo-650">{{ previewingAssessment?.title }}</span></p>
              </div>
              <button @click="showPreviewModal = false" class="text-gray-450 hover:text-gray-600 dark:text-gray-400 dark:hover:text-gray-200 text-lg">✕</button>
            </div>

            <div v-if="loadingPreview" class="flex flex-col items-center justify-center py-12 space-y-3">
              <div class="animate-spin rounded-full h-8 w-8 border-2 border-indigo-600 border-t-transparent"></div>
              <p class="text-xs text-gray-500">Loading questions...</p>
            </div>

            <div v-else-if="previewingQuestions.length === 0" class="text-center py-12 text-gray-500 space-y-1">
              <p class="text-xl">⚠️</p>
              <p class="text-sm font-semibold">No questions found</p>
              <p class="text-xs text-gray-450">This assessment currently has no questions generated or linked.</p>
            </div>

            <div v-else class="space-y-4 overflow-y-auto max-h-[50vh] pr-2">
              <div v-for="(q, idx) in previewingQuestions" :key="q.id" class="p-4 bg-gray-50 dark:bg-gray-850 border border-gray-100 dark:border-gray-800 rounded-2xl space-y-3">
                <div class="flex justify-between items-center">
                  <span class="px-2 py-0.5 bg-indigo-50 dark:bg-indigo-950/40 text-indigo-650 dark:text-indigo-400 text-[10px] font-bold rounded-md uppercase">
                    Q{{ idx + 1 }} · {{ q.question_type.replace('_', ' ') }}
                  </span>
                  <span class="text-[10px] text-gray-500 font-mono">{{ q.difficulty }}</span>
                </div>
                
                <p class="text-sm font-semibold text-gray-900 dark:text-white">{{ q.text }}</p>

                <!-- Options list for MCQs / True-False -->
                <div v-if="q.options && q.options.length > 0" class="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-2">
                  <div v-for="opt in q.options" :key="opt.id" :class="['p-2 rounded-xl text-xs flex items-center gap-2 border', opt.is_correct ? 'bg-emerald-50/50 border-emerald-200 text-emerald-700 dark:bg-emerald-950/20 dark:border-emerald-900/50 dark:text-emerald-400 font-bold' : 'border-gray-100 dark:border-gray-800 text-gray-600 dark:text-gray-400']">
                    <span>{{ opt.is_correct ? '✅' : '⚪' }}</span>
                    <span>{{ opt.text }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="border-t border-gray-150 dark:border-gray-800 pt-4 flex justify-end">
            <button @click="showPreviewModal = false" class="px-6 py-2 bg-indigo-600 text-white text-xs font-bold rounded-xl hover:bg-indigo-700 transition-colors">
              Close Preview
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
