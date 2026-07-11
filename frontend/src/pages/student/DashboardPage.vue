<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useI18n } from 'vue-i18n'
import { assessmentService } from '@/services/assessment.service'
import api from '@/services/api'
import type { Assessment, AssessmentAttempt } from '@/types/assessment'

const { t } = useI18n()
const auth = useAuthStore()

// State
const loading = ref(true)
const stats = ref([
  { icon: '📝', label: 'Total Completed', value: '0', trend: 'Assessments taken', color: 'from-blue-500 to-blue-600' },
  { icon: '📊', label: 'Average Score', value: '0%', trend: 'Overall average', color: 'from-emerald-500 to-emerald-600' },
  { icon: '⭐', label: 'Best Subject', value: 'N/A', trend: 'Highest average', color: 'from-amber-500 to-amber-600' },
  { icon: '🔥', label: 'Revision Streak', value: '3 days', trend: 'Daily revision streak', color: 'from-red-500 to-rose-600' },
])

const upcoming = ref<Assessment[]>([])
const weakTopics = ref<any[]>([])
const subjectProgress = ref<any[]>([])
const attemptsHistory = ref<AssessmentAttempt[]>([])

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
    // 1. Fetch Student Overview Stats
    const { data: overview } = await api.get('/analytics/student/')
    stats.value[0].value = String(overview.total_assessments)
    stats.value[1].value = `${Math.round(overview.average_score)}%`
    subjectProgress.value = overview.by_subject || []
    
    if (overview.by_subject && overview.by_subject.length > 0) {
      stats.value[2].value = overview.by_subject[0].assessment__subject__name
      stats.value[2].trend = `${Math.round(overview.by_subject[0].avg_score)}% average`
    }

    // 2. Fetch Weak Topics
    const { data: topics } = await api.get('/analytics/weak-topics/')
    weakTopics.value = topics.map((t: any, index: number) => ({
      topic: t.question__topic__name || 'General',
      subject: t.question__subject__name || 'Subject',
      wrongCount: t.wrong_count,
      color: index === 0 ? 'bg-red-500' : index < 3 ? 'bg-amber-500' : 'bg-yellow-500'
    }))

    // 3. Fetch Upcoming Assessments
    const rawList = await assessmentService.list({ status: 'published' })
    upcoming.value = rawList.slice(0, 3)

    // 4. Fetch Student Attempts History
    const attemptsRes = await api.get('/attempts/')
    const rawAttempts = Array.isArray(attemptsRes.data) ? attemptsRes.data : attemptsRes.data?.results || []
    attemptsHistory.value = rawAttempts.map((a: any) => ({
      id: a.id,
      assessment: a.assessment,
      assessment_title: a.assessment_title || 'Revision Quiz',
      score: a.score,
      percentage: a.percentage,
      status: a.status,
      started_at: new Date(a.started_at).toLocaleDateString(),
      responses: a.responses || []
    }))

  } catch (err) {
    console.error('Failed to load student dashboard details:', err)
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
      <p class="text-blue-100">
        {{ upcoming.length > 0 ? `You have ${upcoming.length} revision assessments ready to take.` : 'You are all caught up on Revision assessments!' }}
      </p>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-20 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl">
      <span class="animate-spin inline-block w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mb-4"></span>
      <p class="text-gray-500">Loading Student Dashboard...</p>
    </div>

    <template v-else>
      <!-- Stats Grid -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div v-for="stat in stats" :key="stat.label" class="bg-white dark:bg-gray-900 rounded-2xl p-5 border border-gray-200 dark:border-gray-800 hover:shadow-md transition-shadow">
          <div :class="['w-10 h-10 rounded-xl bg-gradient-to-br flex items-center justify-center text-lg mb-3 text-white', stat.color]">
            {{ stat.icon }}
          </div>
          <p class="text-2xl font-bold text-gray-900 dark:text-white">{{ stat.value }}</p>
          <p class="text-xs text-gray-500 mt-1">{{ stat.label }}</p>
          <p class="text-xs text-blue-600 dark:text-blue-400 mt-1 font-semibold">{{ stat.trend }}</p>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Upcoming Assessments -->
        <div class="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-6 shadow-sm">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Available Quizzes & Exams</h2>
          
          <div v-if="upcoming.length === 0" class="text-center py-12 text-gray-500">
            <span class="text-3xl block mb-2">🎉</span>
            No practice exams found at this time.
          </div>
          
          <div v-else class="space-y-3">
            <div v-for="item in upcoming" :key="item.id" @click="$router.push(`/student/exam/${item.id}`)"
              class="flex items-center gap-4 p-3 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-all cursor-pointer border border-gray-100 dark:border-gray-850">
              <div class="w-10 h-10 rounded-xl flex items-center justify-center text-white bg-blue-500 text-sm font-bold shadow-sm">
                📝
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-gray-900 dark:text-white truncate">{{ item.title }}</p>
                <p class="text-xs text-gray-500">{{ item.subject_name }} · {{ item.assessment_type.replace('_', ' ') }}</p>
              </div>
              <div class="text-right">
                <p class="text-xs text-gray-500">{{ item.duration_minutes ? `${item.duration_minutes} min` : 'No limit' }}</p>
                <span class="inline-block mt-1 px-2 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 text-[10px] font-bold rounded-full">Interactive</span>
              </div>
            </div>
          </div>
        </div>

        <!-- AI Homework Assistant card -->
        <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm space-y-4">
          <h3 class="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
            🤖 AI Homework Assistant
          </h3>
          <p class="text-xs text-gray-500">Stuck on a homework question? Ask our tutor to explain standard syllabus concepts instantly.</p>
          
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
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
        <!-- AI Recommendations & Weak Topics -->
        <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm space-y-4">
          <h3 class="text-lg font-bold text-gray-900 dark:text-white">✨ AI Recommendations & Weak Topics</h3>
          <div v-if="weakTopics.length === 0" class="text-sm text-gray-500 italic py-4 text-center">
            ⭐ Excellent! No weak topics identified yet. Keep it up!
          </div>
          <div v-else class="space-y-3">
            <p class="text-xs text-gray-500">Based on your recent attempts, our AI model recommends focusing on these areas:</p>
            <div v-for="topic in weakTopics" :key="topic.topic" class="p-3 bg-red-500/10 border border-red-500/20 rounded-xl flex items-center justify-between">
              <div class="min-w-0">
                <span class="text-sm font-semibold text-red-700 dark:text-red-400 block truncate">{{ topic.topic }}</span>
                <span class="text-[10px] text-gray-500 block">Subject: {{ topic.subject }}</span>
              </div>
              <span class="text-xs font-semibold text-red-650 bg-red-100 dark:bg-red-950/40 px-2 py-1 rounded-lg">
                {{ topic.wrongCount }} errors
              </span>
            </div>
          </div>
        </div>

        <!-- Subject Progress Bar cards -->
        <div class="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-6 shadow-sm">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Progress per Subject</h2>
          
          <div v-if="subjectProgress.length === 0" class="text-center py-12 text-gray-500">
            <span class="text-3xl block mb-2">📚</span>
            No subject progress records found.
          </div>
          
          <div v-else class="space-y-4">
            <div v-for="sub in subjectProgress" :key="sub.assessment__subject__name" class="space-y-2">
              <div class="flex justify-between text-sm">
                <span class="font-medium text-gray-700 dark:text-gray-300">{{ sub.assessment__subject__name }}</span>
                <span class="font-bold text-blue-600 dark:text-blue-400">{{ Math.round(sub.avg_score) }}%</span>
              </div>
              <div class="w-full h-2 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                <div class="h-full bg-gradient-to-r from-blue-500 to-emerald-500 rounded-full" :style="{ width: `${sub.avg_score}%` }"></div>
              </div>
              <p class="text-xs text-gray-500">{{ sub.count }} completed assessments</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Past attempts table -->
      <div class="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 overflow-hidden mt-6 shadow-sm">
        <div class="p-6 border-b border-gray-200 dark:border-gray-800">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Grade History & Past Attempts</h2>
        </div>
        
        <div v-if="attemptsHistory.length === 0" class="text-center py-12 text-gray-500">
          <span class="text-3xl block mb-2">📜</span>
          No completed attempts found.
        </div>
        
        <div v-else class="overflow-x-auto">
          <table class="w-full text-left text-sm">
            <thead class="bg-gray-50 dark:bg-gray-800/50 text-gray-500 font-semibold">
              <tr>
                <th class="px-6 py-3">Assessment</th>
                <th class="px-6 py-3">Completed Date</th>
                <th class="px-6 py-3">Score %</th>
                <th class="px-6 py-3">Status</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200 dark:divide-gray-800 text-gray-950 dark:text-gray-100">
              <tr v-for="att in attemptsHistory" :key="att.id" class="hover:bg-gray-50 dark:hover:bg-gray-800/20">
                <td class="px-6 py-4 font-medium">{{ att.assessment_title }}</td>
                <td class="px-6 py-4">{{ att.started_at }}</td>
                <td class="px-6 py-4 font-bold text-blue-600 dark:text-blue-400">
                  {{ (att.percentage !== null && att.percentage !== undefined) ? `${Math.round(att.percentage)}%` : '—' }}
                </td>
                <td class="px-6 py-4">
                  <span :class="['px-2.5 py-1 text-xs font-semibold rounded-full uppercase', att.status === 'graded' ? 'bg-emerald-100 text-emerald-700' : 'bg-blue-100 text-blue-700']">
                    {{ att.status }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>
