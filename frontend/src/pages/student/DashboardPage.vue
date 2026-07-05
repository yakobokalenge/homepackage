<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useI18n } from 'vue-i18n'
import { assessmentService } from '@/services/assessment.service'
import api from '@/services/api'
import type { Assessment } from '@/types'

const { t } = useI18n()
const auth = useAuthStore()

// State
const loading = ref(true)
const stats = ref([
  { icon: '📝', label: t('dashboard.total_taken'), value: '0', trend: 'Total completed', color: 'from-blue-500 to-blue-600' },
  { icon: '📊', label: t('dashboard.avg_score'), value: '0%', trend: 'Overall average', color: 'from-emerald-500 to-emerald-600' },
  { icon: '⭐', label: t('dashboard.best_subject'), value: 'N/A', trend: 'Highest score', color: 'from-amber-500 to-amber-600' },
  { icon: '🔥', label: t('dashboard.streak'), value: '0 days', trend: 'Daily streak', color: 'from-red-500 to-rose-600' },
])

const upcoming = ref<any[]>([])
const weakTopics = ref<any[]>([])
const subjectProgress = ref<any[]>([])
const attemptsHistory = ref<any[]>([])
const selectedAttempt = ref<any | null>(null)
const showFeedbackModal = ref(false)

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
    stats.value[1].value = `${overview.average_score}%`
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
    const res = await assessmentService.list({ status: 'published' })
    let rawList: Assessment[] = []
    if (res && Array.isArray(res.assessments)) {
      rawList = res.assessments
    } else if (res && Array.isArray((res as any).results)) {
      rawList = (res as any).results
    } else if (Array.isArray(res)) {
      rawList = res
    }
    
    upcoming.value = rawList.slice(0, 3).map((a: Assessment) => ({
      id: a.id,
      title: a.title,
      subject: a.subject_name || 'Subject',
      type: a.assessment_type.replace('_', ' '),
      date: a.duration_minutes ? `Duration: ${a.duration_minutes} min` : 'No limit',
      proctored: a.requires_proctoring
    }))

    // 4. Fetch Student Attempts History
    const { data: attemptsRes } = await api.get('/attempts/')
    attemptsHistory.value = (Array.isArray(attemptsRes) ? attemptsRes : attemptsRes.results || []).map((a: any) => ({
      id: a.id,
      assessment: a.assessment_title || 'Exam',
      score: a.percentage !== null && a.percentage !== undefined ? `${Math.round(a.percentage)}%` : '—',
      points: a.score !== null ? `${a.score} pts` : '—',
      status: a.status,
      date: new Date(a.submitted_at || a.started_at).toLocaleDateString(),
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
    <div class="bg-gradient-to-r from-blue-600 to-emerald-600 rounded-2xl p-6 text-white">
      <h1 class="text-2xl font-bold mb-1">{{ t('dashboard.welcome') }} {{ auth.user?.first_name }}! 👋</h1>
      <p class="text-blue-100">
        {{ upcoming.length > 0 ? `You have ${upcoming.length} upcoming assessments available.` : 'You are all caught up on assessments!' }}
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
        <div v-for="stat in stats" :key="stat.label" class="bg-white dark:bg-gray-900 rounded-2xl p-5 border border-gray-200 dark:border-gray-800 hover:shadow-lg transition-shadow">
          <div :class="['w-10 h-10 rounded-xl bg-gradient-to-br flex items-center justify-center text-lg mb-3 text-white', stat.color]">
            {{ stat.icon }}
          </div>
          <p class="text-2xl font-bold text-gray-900 dark:text-white">{{ stat.value }}</p>
          <p class="text-xs text-gray-500 mt-1">{{ stat.label }}</p>
          <p class="text-xs text-blue-600 dark:text-blue-400 mt-1">{{ stat.trend }}</p>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Upcoming Assessments -->
        <div class="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-6">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">{{ t('dashboard.upcoming') }}</h2>
          
          <div v-if="upcoming.length === 0" class="text-center py-12 text-gray-500">
            <span class="text-3xl block mb-2">🎉</span>
            No upcoming assessments found.
          </div>
          
          <div v-else class="space-y-3">
            <div v-for="item in upcoming" :key="item.id" @click="$router.push(item.proctored ? `/student/exam/${item.id}/proctored` : `/student/exam/${item.id}`)"
              class="flex items-center gap-4 p-3 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors cursor-pointer border border-gray-50 dark:border-gray-800">
              <div :class="['w-10 h-10 rounded-xl flex items-center justify-center text-white text-sm font-bold', item.proctored ? 'bg-red-500' : 'bg-blue-500']">
                {{ item.proctored ? '🔒' : '📝' }}
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-gray-900 dark:text-white truncate">{{ item.title }}</p>
                <p class="text-xs text-gray-500">{{ item.subject }} · {{ item.type }}</p>
              </div>
              <div class="text-right">
                <p class="text-xs text-gray-500">{{ item.date }}</p>
                <span v-if="item.proctored" class="inline-block mt-1 px-2 py-0.5 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 text-xs rounded-full">Proctored</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Analytics & Progress Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
        <!-- AI Study recommendations & Chatbot -->
        <div class="space-y-6">
          <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm space-y-4">
            <h3 class="text-lg font-bold text-gray-900 dark:text-white">✨ AI Study Recommendations & Weak Topics</h3>
            <div v-if="weakTopics.length === 0" class="text-sm text-gray-500 italic py-4 text-center">
              ⭐ Excellent! No weak topics identified yet. Keep it up!
            </div>
            <div v-else class="space-y-3">
              <p class="text-xs text-gray-500">Based on your recent attempts, our AI model recommends focusing on these areas:</p>
              <div v-for="topic in weakTopics" :key="topic.topic" class="p-3 bg-red-500/10 border border-red-500/20 rounded-xl flex items-center justify-between">
                <div class="min-w-0">
                  <span class="text-sm font-semibold text-red-700 dark:text-red-400 block truncate">{{ topic.topic }}</span>
                  <span class="text-[10px] text-gray-500 block">Learning Path: Solve 5 practice quizzes on this area.</span>
                </div>
                <span class="text-xs font-semibold text-red-650 bg-red-100 dark:bg-red-950/40 px-2 py-1 rounded-lg">
                  {{ topic.wrongCount }} errors
                </span>
              </div>
            </div>
          </div>

          <!-- AI Homework Assistant chatbot card -->
          <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm space-y-4">
            <h3 class="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
              🤖 AI Homework Assistant
            </h3>
            <p class="text-xs text-gray-500">Stuck on a homepackage question? Ask our tutor to explain standard syllabus concepts instantly.</p>
            
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

        <!-- Progress per Subject -->
        <div class="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-6">
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

      <!-- Grade History & Past Attempts -->
      <div class="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 overflow-hidden mt-6">
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
                <th class="px-6 py-3">Teacher Feedback</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200 dark:divide-gray-800 text-gray-950 dark:text-gray-100">
              <tr v-for="att in attemptsHistory" :key="att.id" class="hover:bg-gray-50 dark:hover:bg-gray-800/20">
                <td class="px-6 py-4 font-medium">{{ att.assessment }}</td>
                <td class="px-6 py-4">{{ att.date }}</td>
                <td class="px-6 py-4 font-bold text-blue-600 dark:text-blue-400">{{ att.score }} ({{ att.points }})</td>
                <td class="px-6 py-4">
                  <span :class="['px-2 py-0.5 text-xs font-semibold rounded-full uppercase', att.status === 'graded' ? 'bg-emerald-100 text-emerald-700' : 'bg-blue-100 text-blue-700']">
                    {{ att.status }}
                  </span>
                </td>
                <td class="px-6 py-4">
                  <button @click="selectedAttempt = att; showFeedbackModal = true" class="text-xs font-bold text-indigo-600 hover:underline">
                    View Feedback
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Feedback Details Modal Dialog -->
      <div v-if="showFeedbackModal && selectedAttempt" class="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
        <div class="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 w-full max-w-2xl max-h-[80vh] overflow-y-auto p-6 space-y-6 shadow-2xl relative">
          <button @click="showFeedbackModal = false; selectedAttempt = null" class="absolute top-4 right-4 text-2xl text-gray-400 hover:text-gray-600">
            ✕
          </button>
          
          <div>
            <h3 class="text-xl font-bold text-gray-900 dark:text-white">{{ selectedAttempt.assessment }}</h3>
            <p class="text-sm text-gray-500">Graded Attempt Feedback Review</p>
          </div>

          <div class="p-4 bg-gray-50 dark:bg-gray-800/40 rounded-xl flex justify-between items-center">
            <span class="text-sm font-semibold text-gray-600 dark:text-gray-400">Total Score:</span>
            <span class="text-lg font-bold text-emerald-600 dark:text-emerald-400">{{ selectedAttempt.score }} ({{ selectedAttempt.points }})</span>
          </div>

          <div class="space-y-4">
            <h4 class="font-bold text-gray-900 dark:text-white border-b border-gray-200 dark:border-gray-800 pb-2">Questions Review</h4>
            <div v-if="selectedAttempt.responses.length === 0" class="text-center py-6 text-gray-500 italic">
              No questions responses found for this attempt.
            </div>
            <div v-for="(resp, i) in selectedAttempt.responses" :key="resp.id" class="p-4 rounded-xl border border-gray-100 dark:border-gray-800 space-y-3">
              <div class="flex justify-between items-start">
                <span class="text-xs font-bold text-gray-500 uppercase">Question {{ i + 1 }}</span>
                <span :class="['px-2 py-0.5 text-xs font-bold rounded-full', resp.is_correct ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700']">
                  {{ resp.is_correct ? 'Correct' : 'Incorrect' }} · {{ resp.points_awarded || 0 }} pts
                </span>
              </div>
              <p class="text-sm text-gray-900 dark:text-white" v-html="resp.question_detail?.text"></p>
              
              <!-- Question Options for MCQ/Multi-select type -->
              <div v-if="resp.question_detail?.options && resp.question_detail.options.length > 0" class="mt-2 space-y-1.5 pl-3">
                <div v-for="opt in resp.question_detail.options" :key="opt.id" class="flex items-center gap-2 text-xs">
                  <span :class="['w-4 h-4 rounded-full flex items-center justify-center font-bold text-[9px] border', opt.is_correct ? 'bg-emerald-500 border-emerald-500 text-white' : 'border-gray-300 dark:border-gray-700']">
                    {{ opt.is_correct ? '✓' : '' }}
                  </span>
                  <span :class="[opt.is_correct ? 'text-emerald-600 dark:text-emerald-400 font-semibold' : 'text-gray-600 dark:text-gray-400']">
                    {{ opt.text }}
                  </span>
                </div>
              </div>
              
              <div class="pt-2 border-t border-gray-100 dark:border-gray-800/60">
                <p class="text-xs font-semibold text-gray-500">Your Answer:</p>
                <p class="text-sm text-gray-800 dark:text-gray-200 mt-0.5 whitespace-pre-line">{{ resp.answer_text || 'Option Selected' }}</p>
              </div>

              <div v-if="resp.teacher_feedback" class="p-3 bg-indigo-50/50 dark:bg-indigo-950/20 border border-indigo-100/30 rounded-lg">
                <p class="text-xs font-bold text-indigo-700 dark:text-indigo-400">Teacher Feedback:</p>
                <p class="text-sm text-indigo-900 dark:text-indigo-200 mt-0.5">{{ resp.teacher_feedback }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
