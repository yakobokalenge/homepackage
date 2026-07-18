<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { useAssessmentStore } from '../../stores/assessment'
import { useNotificationStore } from '../../stores/notification'

const assessmentStore = useAssessmentStore()
const notificationStore = useNotificationStore()

const loading = ref(true)

async function loadData() {
  loading.value = true
  try {
    await assessmentStore.fetchAssessments()
    await assessmentStore.fetchStudentAttempts()
  } catch {
    notificationStore.error('Failed to load assessments.')
  } finally {
    loading.value = false
  }
}

function getAttemptForAssessment(assessmentId: string) {
  return assessmentStore.studentAttempts.filter(att => att.assessment === assessmentId)
}

onMounted(loadData)
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Assessments Dashboard</h1>
      <p class="text-sm text-gray-500 mt-1">Review available homework packages, take quizzes, or start exam sessions.</p>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-20 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl">
      <span class="animate-spin inline-block w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mb-4"></span>
      <p class="text-gray-500">Loading Assessments...</p>
    </div>

    <!-- Main Workspace -->
    <template v-else>
      <!-- Empty State -->
      <div v-if="assessmentStore.assessments.length === 0" class="text-center py-16 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl">
        <span class="text-4xl block mb-1">📖</span>
        <p class="text-gray-600 dark:text-gray-400 font-medium">No assessments available for your classroom.</p>
        <p class="text-xs text-gray-450 mt-1">Check back later or contact your stream teacher.</p>
      </div>

      <!-- Assessments list cards grid -->
      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div
          v-for="item in assessmentStore.assessments"
          :key="item.id"
          class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-5 hover:shadow-lg transition-all flex flex-col justify-between"
        >
          <div class="space-y-3">
            <!-- Badges -->
            <div class="flex items-center justify-between">
              <span class="px-2 py-0.5 bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 text-[10px] font-bold rounded-lg uppercase">
                {{ item.assessment_type.replace('_', ' ') }}
              </span>
              <span v-if="item.is_proctored" class="px-2 py-0.5 bg-red-50 dark:bg-red-950/20 text-red-600 dark:text-red-400 text-[9px] font-bold rounded-lg uppercase">
                🛡️ Proctored
              </span>
            </div>

            <!-- Title -->
            <div>
              <h3 class="text-sm md:text-base font-bold text-gray-900 dark:text-white truncate">{{ item.title }}</h3>
              <p class="text-[11px] text-gray-500 mt-1">Subject: {{ item.subject_name }} · Created by: {{ item.created_by_name }}</p>
            </div>

            <!-- Stats -->
            <div class="grid grid-cols-2 gap-2 p-2.5 bg-gray-50 dark:bg-gray-900/50 rounded-xl text-[10px] font-medium text-gray-500">
              <div>Time Limit: <span class="text-gray-900 dark:text-white font-bold">{{ item.time_limit_minutes ? `${item.time_limit_minutes}m` : 'None' }}</span></div>
              <div>Total Points: <span class="text-gray-900 dark:text-white font-bold">{{ item.total_points }} pts</span></div>
            </div>

            <!-- Attempt Histories status -->
            <div class="pt-2">
              <span class="text-[9px] font-bold text-gray-500 uppercase tracking-wider block mb-1">Your Attempt History</span>
              <div v-if="getAttemptForAssessment(item.id).length === 0" class="text-[10px] text-gray-400 font-semibold italic">No attempts yet</div>
              <div v-else class="space-y-1">
                <div v-for="att in getAttemptForAssessment(item.id)" :key="att.id" class="flex items-center justify-between text-[10px] p-1.5 bg-gray-50 dark:bg-gray-900 border rounded-lg">
                  <span class="font-medium text-gray-500">Attempt #{{ att.attempt_number }}</span>
                  <div class="flex items-center gap-2">
                    <span :class="[
                      att.status === 'graded' ? 'text-emerald-600' : 'text-amber-500',
                      'font-bold'
                    ]">
                      {{ att.status === 'graded' ? `${att.percentage}%` : att.status }}
                    </span>
                    <RouterLink :to="`/student/attempts/${att.id}/result`" class="text-blue-500 font-bold hover:underline">
                      View
                    </RouterLink>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Bottom Button Action -->
          <div class="mt-5 pt-3 border-t border-gray-150 dark:border-gray-800">
            <RouterLink
              v-if="getAttemptForAssessment(item.id).length < item.max_attempts"
              :to="`/student/assessments/${item.id}/take`"
              class="w-full py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl shadow-md flex items-center justify-center gap-1.5 hover:scale-[1.02] active:scale-[0.98] transition-all"
            >
              ✍️ Start Assessment
            </RouterLink>
            <button
              v-else
              disabled
              class="w-full py-2 bg-gray-100 dark:bg-gray-800 text-gray-400 text-xs font-bold rounded-xl cursor-not-allowed border"
            >
              Attempts Completed
            </button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
