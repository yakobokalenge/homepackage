<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'
import api from '@/services/api'

const { t } = useI18n()
const auth = useAuthStore()

// State
const loading = ref(true)
const stats = ref([
  { icon: '👨‍🎓', label: 'Total Students', value: '0', trend: 'Unique stream members', color: 'from-blue-500 to-blue-600' },
  { icon: '🏫', label: 'Classrooms Target', value: '0', trend: 'Registered school streams', color: 'from-purple-500 to-purple-600' },
  { icon: '📝', label: 'Assessments Created', value: '0', trend: 'Active homework/exams', color: 'from-indigo-500 to-indigo-600' },
  { icon: '📈', label: 'Average Score', value: '0.0%', trend: 'Class success rate', color: 'from-emerald-500 to-emerald-600' }
])

const classroomsList = ref<any[]>([])

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
    stats.value[0].value = String(performance.total_students || 0)
    stats.value[2].value = String(performance.assessments_created || 0)
    stats.value[3].value = `${performance.average_score || 0.0}%`

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
    
    stats.value[1].value = String(classroomsList.value.length)

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
        <p class="text-gray-500 text-sm mt-1">Here's your class overview and roster hub for today.</p>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-20 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl">
      <span class="animate-spin inline-block w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mb-4"></span>
      <p class="text-gray-500">Loading Dashboard Metrics...</p>
    </div>

    <template v-else>
      <!-- Stats Grid -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div v-for="stat in stats" :key="stat.label" class="bg-white dark:bg-gray-900 rounded-2xl p-5 border border-gray-200 dark:border-gray-800 hover:shadow-lg transition-shadow">
          <div :class="['w-10 h-10 rounded-xl bg-gradient-to-br flex items-center justify-center text-lg mb-3 text-white', stat.color]">{{ stat.icon }}</div>
          <p class="text-2xl font-bold text-gray-900 dark:text-white">{{ stat.value }}</p>
          <p class="text-xs text-gray-500 mt-1">{{ stat.label }}</p>
          <p class="text-xs text-blue-600 dark:text-blue-400 mt-1 font-semibold">{{ stat.trend }}</p>
        </div>
      </div>

      <div class="grid grid-cols-1 gap-6">
        <!-- Classrooms Data Export Panel -->
        <div class="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-6 space-y-4 shadow-sm">
          <div>
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Class Roster & Results</h2>
            <p class="text-xs text-gray-500 mt-1">Download Excel-compatible CSV student gradebooks for school databases.</p>
          </div>
          <div v-if="classroomsList.length === 0" class="text-center py-6 text-gray-550 font-medium">
            <span class="text-2xl block mb-1">🏫</span>
            No classrooms found.
          </div>
          <div v-else class="space-y-3 max-h-[350px] overflow-y-auto pr-1">
            <div v-for="cls in classroomsList" :key="cls.id" class="p-3 bg-gray-50 dark:bg-gray-850 border border-gray-150 rounded-xl flex items-center justify-between gap-2 hover:border-blue-400 transition-colors">
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
    </template>
  </div>
</template>
