<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { assessmentService } from '../../services/assessment.service'
import { AssessmentAttempt } from '../../types/assessment'
import { useNotificationStore } from '../../stores/notification'

const route = useRoute()
const notificationStore = useNotificationStore()

const attemptId = route.params.id as string
const attempt = ref<AssessmentAttempt | null>(null)
const loading = ref(true)

async function loadResults() {
  loading.value = true
  try {
    attempt.value = await assessmentService.getAttempt(attemptId)
  } catch {
    notificationStore.error('Failed to load assessment results.')
  } finally {
    loading.value = false
  }
}

onMounted(loadResults)
</script>

<template>
  <div class="space-y-6 max-w-3xl mx-auto">
    <!-- Back to Assessments -->
    <RouterLink to="/student/assessments" class="text-xs font-bold text-blue-600 hover:text-blue-800">
      ◀ Back to Assessments List
    </RouterLink>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-20 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl">
      <span class="animate-spin inline-block w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mb-4"></span>
      <p class="text-gray-500">Retrieving assessment results...</p>
    </div>

    <!-- Results Display -->
    <template v-else-if="attempt">
      <!-- Grade Card -->
      <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm text-center space-y-4">
        <div>
          <span class="px-2 py-0.5 bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 text-[10px] font-bold rounded-lg uppercase">
            Attempt Results Summary
          </span>
          <h1 class="text-xl font-bold text-gray-900 dark:text-white mt-2">{{ attempt.assessment_title }}</h1>
          <p class="text-xs text-gray-500 mt-1">Submitted on: {{ new Date(attempt.submitted_at || '').toLocaleString() }}</p>
        </div>

        <!-- Grade Display based on status -->
        <div v-if="attempt.status === 'graded'" class="space-y-2">
          <div class="inline-block p-6 rounded-3xl bg-gray-50 dark:bg-gray-950 border border-gray-150 shadow-inner">
            <p class="text-3xl sm:text-4xl font-extrabold font-mono" :class="parseFloat(attempt.percentage || '0') >= 50 ? 'text-emerald-600' : 'text-red-500'">
              {{ attempt.percentage }}%
            </p>
            <p class="text-[10px] font-bold text-gray-500 uppercase mt-1">Passing Mark: 50.00%</p>
          </div>
          <p class="text-xs font-bold text-gray-700 dark:text-gray-300">
            Score: {{ attempt.score }} / {{ attempt.responses?.reduce((acc, r) => acc + (r.question_points || 5), 0) || 100 }} pts
          </p>
          <span :class="[
            parseFloat(attempt.percentage || '0') >= 50 ? 'bg-emerald-50 text-emerald-700 border-emerald-250' : 'bg-red-50 text-red-700 border-red-250',
            'inline-block px-3 py-1 text-xs font-bold border rounded-full uppercase'
          ]">
            {{ parseFloat(attempt.percentage || '0') >= 50 ? 'Passed ✓' : 'Failed ✗' }}
          </span>
        </div>

        <div v-else class="p-6 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-2xl">
          <span class="text-2xl">✍️</span>
          <p class="text-xs font-bold text-amber-800 dark:text-amber-400 mt-2">Attempt Submitted & Awaiting Teacher Review</p>
          <p class="text-[10px] text-gray-500 mt-0.5">Some questions (like essays) require manual grading. Your results will display here once graded.</p>
        </div>
      </div>

      <!-- Attempt statistics details -->
      <div class="grid grid-cols-2 gap-4">
        <div class="bg-white dark:bg-gray-900 p-4 border border-gray-250 dark:border-gray-800 rounded-2xl shadow-sm text-center">
          <p class="text-lg font-bold text-gray-900 dark:text-white">{{ Math.floor(attempt.time_spent_seconds / 60) }}m {{ attempt.time_spent_seconds % 60 }}s</p>
          <p class="text-[9px] font-bold text-gray-500 uppercase mt-0.5">Time Spent</p>
        </div>
        <div class="bg-white dark:bg-gray-900 p-4 border border-gray-250 dark:border-gray-800 rounded-2xl shadow-sm text-center">
          <p class="text-lg font-bold text-gray-900 dark:text-white">Attempt #{{ attempt.attempt_number }}</p>
          <p class="text-[9px] font-bold text-gray-500 uppercase mt-0.5">Attempt Number</p>
        </div>
      </div>

      <!-- Teacher overall feedback comments -->
      <div v-if="attempt.feedback" class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-5 shadow-sm space-y-2">
        <h3 class="text-xs font-bold text-gray-500 uppercase">Teacher Overall Comments</h3>
        <p class="text-xs text-gray-800 dark:text-gray-200 italic leading-relaxed">"{{ attempt.feedback }}"</p>
      </div>
    </template>
  </div>
</template>
