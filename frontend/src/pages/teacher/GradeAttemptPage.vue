<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import api from '@/services/api'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()

const attemptId = route.params.id as string
const loading = ref(true)
const attempt = ref<any>(null)
const error = ref('')
const saving = ref(false)

// Locally holds editable response grades
// Array of: { response_id: string, is_correct: boolean, points_awarded: number, teacher_feedback: string }
const grades = ref<any[]>([])

function getQuestionMaxPoints(qDetail: any) {
  return qDetail ? Number(qDetail.points || 0) : 0
}

onMounted(async () => {
  try {
    const { data } = await api.get(`/attempts/${attemptId}/`)
    attempt.value = data
    
    // Initialize editable grades for responses
    if (Array.isArray(data.responses)) {
      grades.value = data.responses.map((r: any) => ({
        response_id: r.id,
        is_correct: r.is_correct ?? false,
        points_awarded: Number(r.points_awarded || 0),
        teacher_feedback: r.teacher_feedback || '',
        // Read-only helpers
        question_type: r.question_detail?.question_type || 'essay',
        max_points: getQuestionMaxPoints(r.question_detail)
      }))
    }
  } catch (err: any) {
    error.value = 'Failed to load student attempt details.'
  } finally {
    loading.value = false
  }
})

async function saveGrades() {
  saving.value = true
  error.value = ''
  try {
    await api.post(`/attempts/${attemptId}/grade/`, {
      responses: grades.value.map(g => ({
        response_id: g.response_id,
        is_correct: g.is_correct,
        points_awarded: g.points_awarded,
        teacher_feedback: g.teacher_feedback
      }))
    })
    router.push('/teacher/dashboard')
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Failed to submit grading.'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="space-y-6 max-w-4xl mx-auto pb-12">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <button @click="router.push('/teacher/dashboard')" class="text-sm font-medium text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200">
          ← Back to Dashboard
        </button>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white mt-2">Grade Submission</h1>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-20 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl">
      <span class="animate-spin inline-block w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mb-4"></span>
      <p class="text-gray-500">Loading Student Submission...</p>
    </div>

    <div v-else-if="error && !attempt" class="p-6 bg-red-50 dark:bg-red-950/20 border border-red-200 text-red-700 rounded-2xl">
      {{ error }}
    </div>

    <template v-else-if="attempt">
      <!-- Submission Metadata -->
      <div class="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-6 shadow-sm space-y-4">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white border-b border-gray-200 dark:border-gray-800 pb-3">Submission Details</h2>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span class="text-gray-500 dark:text-gray-400 block">Student</span>
            <span class="font-medium text-gray-900 dark:text-white">{{ attempt.student_name }}</span>
          </div>
          <div>
            <span class="text-gray-500 dark:text-gray-400 block">Assessment</span>
            <span class="font-medium text-gray-900 dark:text-white">{{ attempt.assessment_title }}</span>
          </div>
          <div>
            <span class="text-gray-500 dark:text-gray-400 block">Current Score</span>
            <span class="font-medium text-gray-900 dark:text-white">
              {{ attempt.score !== null ? `${attempt.score} pts (${Math.round(attempt.percentage)}%)` : 'Not Graded' }}
            </span>
          </div>
          <div>
            <span class="text-gray-500 dark:text-gray-400 block">Status</span>
            <span class="inline-block mt-0.5 px-2 py-0.5 text-xs font-semibold uppercase rounded-full bg-blue-100 text-blue-700">
              {{ attempt.status }}
            </span>
          </div>
        </div>
      </div>

      <!-- Question Reponses List -->
      <div class="space-y-6">
        <h3 class="text-xl font-bold text-gray-900 dark:text-white">Question Grading</h3>
        
        <div v-for="(r, index) in attempt.responses" :key="r.id"
          class="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-6 shadow-sm space-y-4">
          <div class="flex justify-between items-start">
            <span class="px-2.5 py-1 text-xs font-semibold rounded-full uppercase bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300">
              Question {{ index + 1 }} · {{ r.question_detail?.question_type.replace('_', ' ') }}
            </span>
            <span class="text-sm font-semibold text-gray-500">
              Max Points: {{ getQuestionMaxPoints(r.question_detail) }}
            </span>
          </div>

          <!-- Question Text -->
          <div class="p-4 bg-gray-50 dark:bg-gray-800/40 rounded-xl">
            <p class="text-sm text-gray-900 dark:text-white" v-html="r.question_detail?.text"></p>
          </div>

          <!-- Student's Answer -->
          <div>
            <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Student's Answer:</label>
            <div class="p-4 border border-gray-200 dark:border-gray-800 rounded-xl bg-white dark:bg-gray-950">
              <p class="text-sm text-gray-900 dark:text-white whitespace-pre-line" v-if="r.answer_text">
                {{ r.answer_text }}
              </p>
              <div v-else-if="r.selected_options && r.selected_options.length > 0" class="space-y-1">
                <span class="text-xs text-gray-500 block mb-2">Selected Option:</span>
                <span v-for="optId in r.selected_options" :key="optId" class="inline-block px-3 py-1 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400 text-sm rounded-lg border border-blue-100 dark:border-blue-900/30">
                  Option ID: {{ optId }}
                </span>
              </div>
              <p class="text-sm text-gray-400 italic" v-else>
                No answer submitted.
              </p>
            </div>
          </div>

          <!-- Teacher Grading Controls -->
          <div class="border-t border-gray-100 dark:border-gray-800/60 pt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="space-y-3">
              <span class="block text-xs font-medium text-gray-500">Grading</span>
              <div class="flex items-center gap-4">
                <!-- Correct Toggle -->
                <button type="button" @click="grades[index].is_correct = true; grades[index].points_awarded = grades[index].max_points"
                  :class="['px-4 py-2 text-sm font-medium rounded-xl border transition-all flex items-center gap-1.5', grades[index].is_correct ? 'bg-emerald-50 border-emerald-300 text-emerald-700 dark:bg-emerald-950/20' : 'border-gray-200 dark:border-gray-800 text-gray-500']">
                  ✓ Correct
                </button>
                <button type="button" @click="grades[index].is_correct = false; grades[index].points_awarded = 0"
                  :class="['px-4 py-2 text-sm font-medium rounded-xl border transition-all flex items-center gap-1.5', !grades[index].is_correct ? 'bg-red-50 border-red-300 text-red-700 dark:bg-red-950/20' : 'border-gray-200 dark:border-gray-800 text-gray-500']">
                  ✕ Incorrect
                </button>
              </div>

              <!-- Points Awarded Input -->
              <div>
                <label class="block text-xs font-medium text-gray-500 mb-1">Awarded Points:</label>
                <input type="number" step="0.1" v-model.number="grades[index].points_awarded" :max="grades[index].max_points" min="0"
                  class="w-32 px-3 py-2 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none text-sm" />
              </div>
            </div>

            <!-- Feedback -->
            <div>
              <label class="block text-xs font-medium text-gray-500 mb-1">Teacher Feedback:</label>
              <textarea v-model="grades[index].teacher_feedback" rows="3" placeholder="Provide feedback to the student..."
                class="w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none text-sm"></textarea>
            </div>
          </div>
        </div>
      </div>

      <!-- Action Button -->
      <div v-if="error" class="p-3 bg-red-50 dark:bg-red-950/20 border border-red-200 text-red-700 text-sm rounded-xl">{{ error }}</div>

      <button @click="saveGrades" :disabled="saving"
        class="w-full py-4 bg-gradient-to-r from-blue-600 to-emerald-600 text-white font-bold rounded-xl hover:shadow-xl hover:shadow-blue-500/20 disabled:opacity-60 transition-all duration-300 text-lg">
        {{ saving ? 'Saving Grades...' : 'Submit Grades' }}
      </button>
    </template>
  </div>
</template>
