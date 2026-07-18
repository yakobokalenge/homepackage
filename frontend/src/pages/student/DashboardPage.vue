<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useI18n } from 'vue-i18n'
import api from '@/services/api'

const { t } = useI18n()
const auth = useAuthStore()

// State
const loading = ref(true)
const stats = ref({
  total_assessments: 0,
  average_score: 0.0,
  by_subject: [] as any[]
})

const aiQuestion = ref('')
const aiResponse = ref('')
const aiLoading = ref(false)

async function askAITutor() {
  if (aiQuestion.value.trim() === '') return
  aiLoading.value = true
  aiResponse.value = ''
  try {
    const res = await api.post('/analytics/ai-tutor/', { message: aiQuestion.value })
    aiResponse.value = res.data?.reply || 'Tutor responded successfully.'
  } catch (err) {
    aiResponse.value = 'Failed to connect to AI Homework Assistant. Please try again.'
  } finally {
    aiLoading.value = false
  }
}

onMounted(async () => {
  try {
    const res = await api.get('/analytics/student/')
    stats.value = {
      total_assessments: res.data?.total_assessments || 0,
      average_score: res.data?.average_score || 0.0,
      by_subject: res.data?.by_subject || []
    }
  } catch (err) {
    console.error('Failed to load student dashboard metrics:', err)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="space-y-6">
    <!-- Welcome -->
    <div class="bg-gradient-to-r from-blue-600 to-emerald-600 rounded-2xl p-6 text-white shadow-md">
      <h1 class="text-2xl font-bold mb-1">{{ t('dashboard.welcome') }} {{ auth.user?.first_name }}! 👋</h1>
      <p class="text-blue-100">Welcome to your HomePackage revision companion dashboard.</p>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-20 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl">
      <span class="animate-spin inline-block w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mb-4"></span>
      <p class="text-gray-500">Loading Student Dashboard...</p>
    </div>

    <template v-else>
      <!-- Stats Grid -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-5 shadow-sm">
          <div class="w-10 h-10 rounded-xl bg-blue-550/10 text-blue-600 flex items-center justify-center text-lg mb-3">📋</div>
          <p class="text-2xl font-bold text-gray-900 dark:text-white">{{ stats.total_assessments }}</p>
          <p class="text-xs text-gray-500 mt-1">Assessments Completed</p>
        </div>
        <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-5 shadow-sm">
          <div class="w-10 h-10 rounded-xl bg-emerald-550/10 text-emerald-600 flex items-center justify-center text-lg mb-3">📈</div>
          <p class="text-2xl font-bold text-gray-900 dark:text-white">{{ stats.average_score }}%</p>
          <p class="text-xs text-gray-500 mt-1">Average Performance</p>
        </div>
        <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-5 shadow-sm flex flex-col justify-between">
          <div class="w-10 h-10 rounded-xl bg-purple-550/10 text-purple-600 flex items-center justify-center text-lg">🛡️</div>
          <RouterLink to="/student/assessments" class="text-xs font-bold text-blue-600 hover:text-blue-800 flex items-center gap-1 mt-3">
            Go to Assessments List →
          </RouterLink>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- AI Homework Assistant card -->
        <div class="lg:col-span-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm space-y-4">
          <h3 class="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
            🤖 AI Homework Assistant
          </h3>
          <p class="text-xs text-gray-550 font-medium">Stuck on a homework question? Ask our tutor to explain standard syllabus concepts instantly.</p>
          
          <div class="space-y-2">
            <input v-model="aiQuestion" @keyup.enter="askAITutor" placeholder="Ask a homework question..." class="w-full px-3 py-2 text-xs border border-gray-300 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none" />
            <button @click="askAITutor" :disabled="aiLoading || aiQuestion.trim() === ''" class="w-full py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-bold text-xs rounded-xl flex items-center justify-center gap-2">
              <span v-if="aiLoading" class="animate-spin inline-block w-3 h-3 border-2 border-white border-t-transparent rounded-full"></span>
              {{ aiLoading ? 'Querying AI...' : 'Ask Tutor' }}
            </button>
          </div>

          <div v-if="aiResponse" class="p-3 bg-indigo-50/50 dark:bg-indigo-950/20 border border-indigo-100/30 rounded-xl space-y-1">
            <span class="text-[10px] font-bold text-indigo-700 dark:text-indigo-400 uppercase">AI response</span>
            <p class="text-xs text-gray-700 dark:text-gray-300 whitespace-pre-line leading-relaxed">{{ aiResponse }}</p>
          </div>
        </div>

        <!-- Subjects performance list -->
        <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-5 shadow-sm space-y-4">
          <h3 class="text-sm font-bold text-gray-900 dark:text-white">Subject Breakdown</h3>
          <div v-if="stats.by_subject.length === 0" class="text-center py-6 text-gray-550 text-xs italic">
            No subject breakdowns available.
          </div>
          <div v-else class="space-y-3">
            <div v-for="sub in stats.by_subject" :key="sub.subject_id" class="flex justify-between items-center text-xs">
              <span class="font-medium text-gray-750 dark:text-gray-300">{{ sub.subject_name }}</span>
              <span class="font-bold text-gray-900 dark:text-white">{{ sub.average_score }}% ({{ sub.attempts_count }} attempts)</span>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
