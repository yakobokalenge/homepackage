<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'
import { assessmentService } from '@/services/assessment.service'
import api from '@/services/api'
import type { Assessment } from '@/types/assessment'

const { t } = useI18n()
const auth = useAuthStore()

// State
const loading = ref(true)
const stats = ref([
  { icon: '👨‍🎓', label: 'Total Students', value: '0', trend: 'Unique stream members', color: 'from-blue-500 to-blue-600' },
  { icon: '📝', label: 'Assessments Created', value: '0', trend: 'Online question sheets', color: 'from-emerald-500 to-emerald-600' },
  { icon: '📊', label: 'Avg Class Score', value: '0%', trend: 'Stream class average', color: 'from-amber-500 to-amber-600' },
  { icon: '📁', label: 'Total Submissions', value: '0', trend: 'Submitted attempts', color: 'from-purple-500 to-purple-600' },
])

const classPerformance = ref<any[]>([])
const commonMistakes = ref<any[]>([])
const classroomsList = ref<any[]>([])
const assessmentsList = ref<Assessment[]>([])

const groupedAssessments = computed(() => {
  const groups: Record<string, Assessment[]> = {
    'home_package': [],
    'assignment': [],
    'quiz': [],
    'test': [],
    'exam': []
  }
  
  assessmentsList.value.forEach(ass => {
    const type = ass.assessment_type || 'home_package'
    if (!groups[type]) {
      groups[type] = []
    }
    groups[type].push(ass)
  })
  
  return groups
})

function deleteAssessment(id: string) {
  if (!confirm('Are you sure you want to delete this assessment? This will remove all attempts and student responses associated with it.')) return
  assessmentService.delete(id)
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

onMounted(async () => {
  try {
    // 1. Fetch Teacher Analytics Stats
    const { data: performance } = await api.get('/analytics/teacher/')
    stats.value[0].value = String(performance.total_students)
    stats.value[1].value = String(performance.assessments_created)
    stats.value[2].value = `${Math.round(performance.average_score)}%`
    stats.value[3].value = String(performance.total_submissions)
    classPerformance.value = performance.by_assessment || []
    commonMistakes.value = performance.common_mistakes || []

    // 2. Fetch Classrooms List
    const classroomsRes = await api.get('/schools/classrooms/')
    const rawClassrooms = Array.isArray(classroomsRes.data) ? classroomsRes.data : classroomsRes.data?.results || []
    const seenCls = new Set()
    classroomsList.value = rawClassrooms.filter((item: any) => {
      const key = `${item.name}-${item.stream}`
      if (seenCls.has(key)) return false
      seenCls.add(key)
      return true
    })

    // 3. Fetch Assessments List
    assessmentsList.value = await assessmentService.list()

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
        <p class="text-gray-500 text-sm mt-1">Here's your class overview and assessments hub for today.</p>
      </div>
      <RouterLink to="/teacher/assessments/create" class="px-5 py-2.5 bg-gradient-to-r from-blue-600 to-emerald-600 text-white font-semibold rounded-xl hover:shadow-lg transition-all text-sm shadow-md">
        + Create Online Assessment
      </RouterLink>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-20 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl">
      <span class="animate-spin inline-block w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mb-4"></span>
      <p class="text-gray-500">Loading Dashboard Metrics...</p>
    </div>

    <template v-else>
      <!-- Stats Grid -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div v-for="stat in stats" :key="stat.label" class="bg-white dark:bg-gray-900 rounded-2xl p-5 border border-gray-200 dark:border-gray-800 hover:shadow-lg transition-shadow">
          <div :class="['w-10 h-10 rounded-xl bg-gradient-to-br flex items-center justify-center text-lg mb-3 text-white', stat.color]">{{ stat.icon }}</div>
          <p class="text-2xl font-bold text-gray-900 dark:text-white">{{ stat.value }}</p>
          <p class="text-xs text-gray-500 mt-1">{{ stat.label }}</p>
          <p class="text-xs text-blue-600 dark:text-blue-400 mt-1 font-semibold">{{ stat.trend }}</p>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Class Performance List (col-span-2) -->
        <div class="lg:col-span-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm space-y-4">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Revision Performance Breakdown</h2>
          
          <div v-if="classPerformance.length === 0" class="text-center py-12 text-gray-500">
            <span class="text-3xl block mb-2">📊</span>
            No student submissions recorded for assessments yet.
          </div>
          
          <div v-else class="space-y-4 max-h-[350px] overflow-y-auto pr-1">
            <div v-for="perf in classPerformance" :key="perf.assessment__title" class="p-3 bg-gray-50 dark:bg-gray-850 rounded-xl flex justify-between items-center">
              <div>
                <p class="text-sm font-semibold text-gray-900 dark:text-white">{{ perf.assessment__title }}</p>
                <p class="text-xs text-gray-500">{{ perf.total }} student attempts completed</p>
              </div>
              <span class="text-sm font-bold text-emerald-600 bg-emerald-50 dark:bg-emerald-950/20 px-2 py-1 rounded-lg">
                {{ Math.round(perf.avg_score) }}% Average
              </span>
            </div>
          </div>
        </div>

        <!-- Classrooms Data Export Panel (col-span-1) -->
        <div class="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-6 space-y-4 shadow-sm">
          <div>
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Class Roster & Results</h2>
            <p class="text-xs text-gray-500 mt-1">Download Excel-compatible CSV student gradebooks for school databases.</p>
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
          No assessments created yet. Click "+ Create Online Assessment" above to make your first one.
        </div>
        
        <div v-else class="p-6 space-y-6">
          <div v-for="(list, type) in groupedAssessments" :key="type" class="space-y-3">
            <div v-if="list.length > 0">
              <h3 class="text-xs font-bold text-gray-800 dark:text-gray-200 uppercase tracking-wider flex items-center gap-2">
                <span class="text-lg">{{ type === 'home_package' ? '🏠' : type === 'quiz' ? '📝' : type === 'assignment' ? '✍️' : type === 'test' ? '🧪' : '🎓' }}</span>
                {{ type === 'home_package' ? 'Home Packages' : type === 'quiz' ? 'Quizzes' : type === 'assignment' ? 'Assignments' : type === 'test' ? 'Tests' : 'Exams' }}
                <span class="px-2 py-0.5 bg-gray-100 dark:bg-gray-850 rounded-full text-xs font-bold text-gray-500 dark:text-gray-400">{{ list.length }}</span>
              </h3>
              
              <div class="overflow-x-auto border border-gray-100 dark:border-gray-800 rounded-xl mt-2">
                <table class="w-full text-left text-sm">
                  <thead class="bg-gray-50 dark:bg-gray-850 text-gray-500 font-semibold border-b border-gray-200 dark:border-gray-850">
                    <tr>
                      <th class="px-6 py-3">Assessment Title</th>
                      <th class="px-6 py-3">Subject Name</th>
                      <th class="px-6 py-3">Class Target</th>
                      <th class="px-6 py-3">Questions Limit</th>
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
                        <span :class="['px-2.5 py-0.5 text-xs font-bold rounded-full uppercase', ass.status === 'published' ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-400' : 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400']">
                          {{ ass.status }}
                        </span>
                      </td>
                      <td class="px-6 py-4">
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
    </template>
  </div>
</template>
