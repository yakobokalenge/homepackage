<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { assessmentService } from '../../services/assessment.service'
import { Assessment } from '../../types/assessment'
import { useNotificationStore } from '../../stores/notification'

const route = useRoute()
const notificationStore = useNotificationStore()

const assessmentId = route.params.id as string
const assessment = ref<Assessment | null>(null)
const summary = ref<any>(null)
const studentResults = ref<any[]>([])
const loading = ref(true)

async function loadDetails() {
  loading.value = true
  try {
    assessment.value = await assessmentService.getAssessment(assessmentId)
    const res = await assessmentService.getAssessmentResults(assessmentId)
    summary.value = res.summary
    studentResults.value = res.results
  } catch {
    notificationStore.error('Failed to load assessment results.')
  } finally {
    loading.value = false
  }
}

onMounted(loadDetails)
</script>

<template>
  <div class="space-y-6">
    <!-- Back Navigation -->
    <RouterLink to="/teacher/assessments" class="text-xs font-bold text-blue-600 hover:text-blue-800 flex items-center gap-1">
      ◀ Back to Assessments
    </RouterLink>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-20 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl">
      <span class="animate-spin inline-block w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mb-4"></span>
      <p class="text-gray-500">Loading Assessment Results...</p>
    </div>

    <template v-else-if="assessment">
      <!-- Title & Info -->
      <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm space-y-3">
        <div class="flex items-center gap-2">
          <span class="px-2 py-0.5 bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 text-[10px] font-bold rounded-lg uppercase">
            {{ assessment.assessment_type.replace('_', ' ') }}
          </span>
          <span class="text-xs text-gray-500">· Subject: {{ assessment.subject_details?.name }}</span>
        </div>
        <h1 class="text-xl md:text-2xl font-bold text-gray-900 dark:text-white">{{ assessment.title }}</h1>
        <p class="text-xs text-gray-500 leading-relaxed">{{ assessment.description || 'No description provided.' }}</p>
      </div>

      <!-- Summary metrics grid -->
      <div v-if="summary" class="grid grid-cols-2 md:grid-cols-4 gap-6">
        <div class="bg-white dark:bg-gray-900 p-5 border border-gray-200 dark:border-gray-800 rounded-2xl shadow-sm text-center">
          <p class="text-2xl font-bold text-gray-900 dark:text-white">{{ summary.total_submissions }}</p>
          <p class="text-[10px] font-bold text-gray-500 uppercase mt-1">Submissions</p>
        </div>
        <div class="bg-white dark:bg-gray-900 p-5 border border-gray-200 dark:border-gray-800 rounded-2xl shadow-sm text-center">
          <p class="text-2xl font-bold text-blue-600 dark:text-blue-450">{{ summary.avg_percentage.toFixed(1) }}%</p>
          <p class="text-[10px] font-bold text-gray-500 uppercase mt-1">Avg Score</p>
        </div>
        <div class="bg-white dark:bg-gray-900 p-5 border border-gray-200 dark:border-gray-800 rounded-2xl shadow-sm text-center">
          <p class="text-2xl font-bold text-emerald-600">{{ summary.passed }}</p>
          <p class="text-[10px] font-bold text-gray-500 uppercase mt-1">Passed Students</p>
        </div>
        <div class="bg-white dark:bg-gray-900 p-5 border border-gray-200 dark:border-gray-800 rounded-2xl shadow-sm text-center">
          <p class="text-2xl font-bold text-red-600">{{ summary.failed }}</p>
          <p class="text-[10px] font-bold text-gray-500 uppercase mt-1">Failed Students</p>
        </div>
      </div>

      <!-- Student Attempts Roster list table -->
      <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl shadow-sm overflow-hidden">
        <div class="p-5 border-b border-gray-150 dark:border-gray-800 flex justify-between items-center">
          <h2 class="text-base font-bold text-gray-900 dark:text-white">Student Submission Roster</h2>
          <span class="text-xs text-gray-500">{{ studentResults.length }} attempts</span>
        </div>

        <div v-if="studentResults.length === 0" class="text-center py-12 text-gray-550 font-medium">
          <span class="text-3xl block mb-1">📝</span>
          No students have submitted this assessment yet.
        </div>

        <div v-else class="overflow-x-auto">
          <table class="w-full text-left border-collapse">
            <thead>
              <tr class="bg-gray-50 dark:bg-gray-800/50 text-[10px] font-bold uppercase text-gray-500 border-b border-gray-150 dark:border-gray-850">
                <th class="p-4">Student Name</th>
                <th class="p-4">Submission Date</th>
                <th class="p-4">Score</th>
                <th class="p-4">Percentage</th>
                <th class="p-4">Status</th>
                <th class="p-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-150 dark:divide-gray-850 text-xs">
              <tr v-for="res in studentResults" :key="res.attempt_id" class="hover:bg-gray-50/50 dark:hover:bg-gray-900/50 text-gray-700 dark:text-gray-300">
                <td class="p-4 font-semibold text-gray-900 dark:text-white">{{ res.student_name }}</td>
                <td class="p-4">{{ new Date(res.submitted_at).toLocaleString() }}</td>
                <td class="p-4 font-mono">{{ res.score || '0.00' }} pts</td>
                <td class="p-4 font-mono">{{ res.percentage ? `${res.percentage}%` : '0.00%' }}</td>
                <td class="p-4">
                  <span :class="[
                    res.status === 'graded' ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700',
                    'px-2 py-0.5 rounded-lg text-[10px] font-bold uppercase'
                  ]">
                    {{ res.status }}
                  </span>
                </td>
                <td class="p-4 text-right flex gap-2 justify-end">
                  <RouterLink
                    v-if="res.status === 'submitted'"
                    :to="`/teacher/attempts/${res.attempt_id}/grade`"
                    class="px-2.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white font-bold text-[10px] rounded-lg shadow-sm"
                  >
                    ✍️ Grade
                  </RouterLink>
                  <RouterLink
                    v-else
                    :to="`/teacher/attempts/${res.attempt_id}/grade`"
                    class="px-2.5 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 text-[10px] font-bold rounded-lg border"
                  >
                    👁️ View
                  </RouterLink>
                  <RouterLink
                    v-if="assessment.is_proctored"
                    :to="`/teacher/proctoring/${res.attempt_id}`"
                    class="px-2.5 py-1.5 bg-amber-50 dark:bg-amber-950/20 text-amber-700 hover:bg-amber-100 text-[10px] font-bold rounded-lg border border-amber-300"
                  >
                    🛡️ Proctor Report
                  </RouterLink>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>
