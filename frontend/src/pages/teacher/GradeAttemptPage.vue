<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { assessmentService } from '../../services/assessment.service'
import { AssessmentAttempt } from '../../types/assessment'
import { useNotificationStore } from '../../stores/notification'

const route = useRoute()
const router = useRouter()
const notificationStore = useNotificationStore()

const attemptId = route.params.id as string
const attempt = ref<AssessmentAttempt | null>(null)
const loading = ref(true)
const saving = ref(false)

// local grading maps
const gradedResponses = ref<Record<string, { points_awarded: number; teacher_feedback: string }>>({})
const overallFeedback = ref('')

async function loadAttempt() {
  loading.value = true
  try {
    const data = await assessmentService.getAttempt(attemptId)
    attempt.value = data
    overallFeedback.value = data.feedback || ''
    
    // Initialize local responses
    if (data.responses) {
      data.responses.forEach(resp => {
        gradedResponses.value[resp.id] = {
          points_awarded: parseFloat(resp.points_awarded) || 0,
          teacher_feedback: resp.teacher_feedback || ''
        }
      })
    }
  } catch {
    notificationStore.error('Failed to load attempt details.')
  } finally {
    loading.value = false
  }
}

async function handleSaveGrades() {
  saving.value = true
  try {
    await assessmentService.gradeAttempt(attemptId, {
      grades: gradedResponses.value,
      feedback: overallFeedback.value
    })
    notificationStore.success('Attempt graded successfully.')
    router.push(`/teacher/assessments/${attempt.value?.assessment}`)
  } catch {
    notificationStore.error('Failed to save grades.')
  } finally {
    saving.value = false
  }
}

onMounted(loadAttempt)
</script>

<template>
  <div class="space-y-6 max-w-4xl mx-auto">
    <!-- Back -->
    <button @click="router.back()" class="text-xs font-bold text-blue-600 hover:text-blue-800">
      ◀ Back
    </button>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-20 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl">
      <span class="animate-spin inline-block w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mb-4"></span>
      <p class="text-gray-500">Loading Student Submission...</p>
    </div>

    <template v-else-if="attempt">
      <!-- Roster Header -->
      <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm">
        <h1 class="text-xl font-bold text-gray-900 dark:text-white">Grading Workspace</h1>
        <p class="text-xs text-gray-500 mt-1">Student: <span class="font-bold text-gray-900 dark:text-white">{{ attempt.student_name }}</span> · Assessment: {{ attempt.assessment_title }} (Attempt #{{ attempt.attempt_number }})</p>
      </div>

      <!-- Responses list -->
      <div class="space-y-6">
        <div
          v-for="(resp, idx) in attempt.responses"
          :key="resp.id"
          class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm space-y-4"
        >
          <!-- Question Header info -->
          <div class="flex items-center justify-between border-b border-gray-150 dark:border-gray-800 pb-2">
            <span class="text-xs font-bold text-gray-550 uppercase">Question {{ idx + 1 }} ({{ resp.question_type || 'Essay' }})</span>
            <span class="text-xs text-gray-500 font-bold">Max points: {{ resp.question_points || 5 }}</span>
          </div>

          <!-- Question Text -->
          <div class="prose max-w-none text-xs md:text-sm text-gray-700 dark:text-gray-300">
            <p v-html="resp.question_text || 'Loading Question Text...'"></p>
          </div>

          <!-- Student's Answer -->
          <div class="p-4 bg-gray-50 dark:bg-gray-950 border border-gray-200 dark:border-gray-850 rounded-2xl space-y-3">
            <span class="text-[10px] font-bold text-gray-550 uppercase">Student Answer Response</span>
            
            <!-- Standard text display -->
            <p v-if="resp.text_answer" class="text-xs text-gray-900 dark:text-white whitespace-pre-line leading-relaxed">{{ resp.text_answer }}</p>
            
            <!-- File attachment download -->
            <div v-if="resp.file_attachment" class="flex items-center justify-between p-3 bg-white dark:bg-gray-900 border rounded-xl">
              <span class="text-xs font-bold text-gray-700 dark:text-gray-300">📎 Submission Attachment</span>
              <a :href="resp.file_attachment" target="_blank" class="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white font-bold text-[10px] rounded-lg">
                View/Download File
              </a>
            </div>

            <!-- Auto grading status -->
            <div v-if="resp.auto_graded" class="flex items-center gap-1.5 text-[10px] font-bold" :class="resp.is_correct ? 'text-emerald-600' : 'text-red-500'">
              <span>{{ resp.is_correct ? '✓ Auto-Graded Correct' : '✗ Auto-Graded Incorrect' }}</span>
            </div>
          </div>

          <!-- Grading Input -->
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4 pt-3 border-t border-gray-150 dark:border-gray-850">
            <div class="flex flex-col gap-1">
              <label class="text-[10px] font-bold text-gray-550 uppercase">Awarded Points</label>
              <input
                type="number"
                step="0.5"
                v-model="gradedResponses[resp.id].points_awarded"
                class="px-3 py-2 border rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none text-xs"
              />
            </div>
            <div class="md:col-span-2 flex flex-col gap-1">
              <label class="text-[10px] font-bold text-gray-550 uppercase">Question Feedback</label>
              <input
                type="text"
                v-model="gradedResponses[resp.id].teacher_feedback"
                placeholder="Good effort. Double check your formulas next time."
                class="px-3 py-2 border rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none text-xs"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Overall Feedback & Action -->
      <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm space-y-4">
        <div class="flex flex-col gap-1.5">
          <label class="text-xs font-bold text-gray-700 dark:text-gray-300">Overall Attempt Feedback</label>
          <textarea rows="3" v-model="overallFeedback" placeholder="Write overall comments here..." class="px-3 py-2 text-xs border border-gray-300 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none"></textarea>
        </div>

        <button
          @click="handleSaveGrades"
          :disabled="saving"
          class="w-full py-3 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white font-bold text-xs rounded-xl shadow-md flex items-center justify-center gap-2"
        >
          <span v-if="saving" class="animate-spin inline-block w-3 h-3 border-2 border-white border-t-transparent rounded-full"></span>
          Submit Gradebook & Feedback
        </button>
      </div>
    </template>
  </div>
</template>
