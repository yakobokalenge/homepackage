<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { assessmentService } from '../../services/assessment.service'
import { useNotificationStore } from '../../stores/notification'

const route = useRoute()
const router = useRouter()
const notificationStore = useNotificationStore()

const attemptId = route.params.id as string
const attempt = ref<any>(null)
const loading = ref(true)
const saving = ref(false)

// Grading maps (only used in editable mode)
const gradedResponses = ref<Record<string, { points_awarded: number; teacher_feedback: string }>>({})
const overallFeedback = ref('')

const isEditable = computed(() => attempt.value?.status === 'submitted')
const isGraded = computed(() => attempt.value?.status === 'graded')

async function loadAttempt() {
  loading.value = true
  try {
    const data = await assessmentService.getAttempt(attemptId)
    attempt.value = data
    overallFeedback.value = data.feedback || ''
    
    // Initialize local grading responses
    if (data.responses) {
      data.responses.forEach((resp: any) => {
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

function isOptionSelected(resp: any, optionId: string): boolean {
  if (resp.selected_options && resp.selected_options.length > 0) {
    return resp.selected_options.includes(optionId)
  }
  if (resp.selected_options_details) {
    return resp.selected_options_details.some((d: any) => d.id === optionId)
  }
  return false
}

function getQuestionTypeBadgeColor(type: string): string {
  const colors: Record<string, string> = {
    mcq: 'bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    multi_select: 'bg-indigo-50 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400',
    true_false: 'bg-purple-50 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
    fill_blank: 'bg-cyan-50 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-400',
    short_answer: 'bg-teal-50 text-teal-700 dark:bg-teal-900/30 dark:text-teal-400',
    essay: 'bg-amber-50 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
    matching: 'bg-pink-50 text-pink-700 dark:bg-pink-900/30 dark:text-pink-400',
    ordering: 'bg-orange-50 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
  }
  return colors[type] || 'bg-gray-50 text-gray-700'
}

function formatQuestionType(type: string): string {
  const labels: Record<string, string> = {
    mcq: 'Multiple Choice',
    multi_select: 'Multi Select',
    true_false: 'True / False',
    fill_blank: 'Fill in the Blank',
    short_answer: 'Short Answer',
    essay: 'Essay',
    matching: 'Matching',
    ordering: 'Ordering',
  }
  return labels[type] || type
}

onMounted(loadAttempt)
</script>

<template>
  <div class="space-y-6 max-w-4xl mx-auto">
    <!-- Back -->
    <button @click="router.back()" class="text-xs font-bold text-blue-600 hover:text-blue-800 flex items-center gap-1">
      ◀ Back
    </button>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-20 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl">
      <span class="animate-spin inline-block w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mb-4"></span>
      <p class="text-gray-500">Loading Student Submission...</p>
    </div>

    <template v-else-if="attempt">
      <!-- Header Card -->
      <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm space-y-3">
        <div class="flex items-center gap-2">
          <span v-if="isEditable" class="px-2 py-0.5 bg-amber-50 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 text-[10px] font-bold rounded-lg uppercase">⏳ Needs Grading</span>
          <span v-else-if="isGraded" class="px-2 py-0.5 bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 text-[10px] font-bold rounded-lg uppercase">✓ Graded</span>
          <span v-else class="px-2 py-0.5 bg-gray-100 text-gray-600 text-[10px] font-bold rounded-lg uppercase">{{ attempt.status }}</span>
        </div>
        <h1 class="text-xl font-bold text-gray-900 dark:text-white">
          {{ isEditable ? 'Grading Workspace' : 'Submission Review' }}
        </h1>
        <p class="text-xs text-gray-500">
          Student: <span class="font-bold text-gray-900 dark:text-white">{{ attempt.student_name }}</span>
          · Assessment: {{ attempt.assessment_title }}
          · Attempt #{{ attempt.attempt_number }}
        </p>
      </div>

      <!-- Score Summary Banner (for graded attempts) -->
      <div v-if="isGraded" class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-4 text-center">
          <p class="text-xl font-bold text-blue-600">{{ attempt.score || '0.00' }}</p>
          <p class="text-[10px] font-bold text-gray-500 uppercase mt-0.5">Score (pts)</p>
        </div>
        <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-4 text-center">
          <p class="text-xl font-bold" :class="parseFloat(attempt.percentage) >= 50 ? 'text-emerald-600' : 'text-red-500'">{{ attempt.percentage || '0.00' }}%</p>
          <p class="text-[10px] font-bold text-gray-500 uppercase mt-0.5">Percentage</p>
        </div>
        <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-4 text-center">
          <p class="text-xl font-bold text-gray-900 dark:text-white">{{ attempt.responses?.length || 0 }}</p>
          <p class="text-[10px] font-bold text-gray-500 uppercase mt-0.5">Questions</p>
        </div>
        <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-4 text-center">
          <p class="text-xl font-bold text-gray-900 dark:text-white">{{ attempt.graded_at ? new Date(attempt.graded_at).toLocaleDateString() : '—' }}</p>
          <p class="text-[10px] font-bold text-gray-500 uppercase mt-0.5">Graded Date</p>
        </div>
      </div>

      <!-- Responses List -->
      <div class="space-y-6">
        <div
          v-for="(resp, idx) in attempt.responses"
          :key="resp.id"
          class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm space-y-4"
        >
          <!-- Question Header -->
          <div class="flex items-center justify-between border-b border-gray-150 dark:border-gray-800 pb-3">
            <div class="flex items-center gap-2">
              <span class="text-xs font-bold text-gray-700 dark:text-gray-300">Q{{ idx + 1 }}</span>
              <span :class="[getQuestionTypeBadgeColor(resp.question_type), 'px-2 py-0.5 text-[10px] font-bold rounded-lg uppercase']">
                {{ formatQuestionType(resp.question_type) }}
              </span>
            </div>
            <span class="text-xs text-gray-500 font-bold">Max: {{ resp.question_points || 5 }} pts</span>
          </div>

          <!-- Question Text -->
          <div class="prose max-w-none text-sm text-gray-800 dark:text-gray-200">
            <p v-html="resp.question_text || 'Question text unavailable'"></p>
          </div>

          <!-- Student Answer Display -->
          <div class="p-4 bg-gray-50 dark:bg-gray-950 border border-gray-200 dark:border-gray-850 rounded-2xl space-y-3">
            <span class="text-[10px] font-bold text-gray-500 uppercase tracking-wider">Student's Answer</span>

            <!-- MCQ / Multi-Select / True-False: Show options list -->
            <div v-if="['mcq', 'multi_select', 'true_false'].includes(resp.question_type) && resp.question_options && resp.question_options.length > 0" class="space-y-2">
              <div
                v-for="opt in resp.question_options"
                :key="opt.id"
                class="flex items-center gap-3 p-2.5 rounded-xl border text-xs"
                :class="[
                  isOptionSelected(resp, opt.id) && opt.is_correct
                    ? 'bg-emerald-50 dark:bg-emerald-900/20 border-emerald-300 dark:border-emerald-700'
                    : isOptionSelected(resp, opt.id) && !opt.is_correct
                    ? 'bg-red-50 dark:bg-red-900/20 border-red-300 dark:border-red-700'
                    : opt.is_correct
                    ? 'bg-emerald-50/50 dark:bg-emerald-950/20 border-emerald-200 dark:border-emerald-800'
                    : 'bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-800'
                ]"
              >
                <span class="flex-shrink-0 w-5 h-5 flex items-center justify-center rounded-full text-[10px] font-bold"
                  :class="[
                    isOptionSelected(resp, opt.id) && opt.is_correct ? 'bg-emerald-500 text-white' :
                    isOptionSelected(resp, opt.id) && !opt.is_correct ? 'bg-red-500 text-white' :
                    opt.is_correct ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-800 dark:text-emerald-300' :
                    'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400'
                  ]"
                >
                  <template v-if="isOptionSelected(resp, opt.id) && opt.is_correct">✓</template>
                  <template v-else-if="isOptionSelected(resp, opt.id) && !opt.is_correct">✗</template>
                  <template v-else-if="opt.is_correct">✓</template>
                  <template v-else>{{ opt.order }}</template>
                </span>
                <span class="flex-1" :class="isOptionSelected(resp, opt.id) ? 'font-semibold text-gray-900 dark:text-white' : 'text-gray-600 dark:text-gray-400'">{{ opt.text }}</span>
                <span v-if="isOptionSelected(resp, opt.id)" class="text-[10px] font-bold uppercase" :class="opt.is_correct ? 'text-emerald-600' : 'text-red-500'">
                  {{ opt.is_correct ? 'Correct' : 'Incorrect' }}
                </span>
                <span v-else-if="opt.is_correct" class="text-[10px] font-bold uppercase text-emerald-500">Correct Answer</span>
              </div>
            </div>

            <!-- Fill Blank -->
            <div v-else-if="resp.question_type === 'fill_blank'" class="space-y-2">
              <div class="flex items-center gap-2">
                <span class="text-[10px] font-bold text-gray-500 uppercase">Student wrote:</span>
                <span class="px-3 py-1.5 bg-white dark:bg-gray-800 border rounded-lg text-xs font-medium text-gray-900 dark:text-white">{{ resp.text_answer || '(no answer)' }}</span>
              </div>
              <div v-if="resp.correct_answer_text" class="flex items-center gap-2">
                <span class="text-[10px] font-bold text-emerald-600 uppercase">Correct answer:</span>
                <span class="px-3 py-1.5 bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 rounded-lg text-xs font-medium text-emerald-700">{{ resp.correct_answer_text }}</span>
              </div>
            </div>

            <!-- Essay / Short Answer -->
            <div v-else-if="['essay', 'short_answer'].includes(resp.question_type)" class="space-y-2">
              <p class="text-xs text-gray-900 dark:text-white whitespace-pre-line leading-relaxed bg-white dark:bg-gray-800 p-3 rounded-xl border border-gray-200 dark:border-gray-700">{{ resp.text_answer || '(no answer provided)' }}</p>
            </div>

            <!-- Matching -->
            <div v-else-if="resp.question_type === 'matching' && resp.matching_pairs" class="space-y-1">
              <div v-for="(value, key) in resp.matching_pairs" :key="key" class="flex items-center gap-2 text-xs">
                <span class="px-2 py-1 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 rounded-lg font-medium">{{ key }}</span>
                <span class="text-gray-400">→</span>
                <span class="px-2 py-1 bg-purple-50 dark:bg-purple-900/20 border border-purple-200 rounded-lg font-medium">{{ value }}</span>
              </div>
            </div>

            <!-- Ordering -->
            <div v-else-if="resp.question_type === 'ordering' && resp.ordering_sequence" class="space-y-1">
              <div v-for="(item, i) in resp.ordering_sequence" :key="i" class="flex items-center gap-2 text-xs">
                <span class="w-5 h-5 flex items-center justify-center bg-gray-100 dark:bg-gray-800 rounded-full text-[10px] font-bold">{{ i + 1 }}</span>
                <span class="text-gray-900 dark:text-white">{{ item }}</span>
              </div>
            </div>

            <!-- Fallback text answer -->
            <div v-else>
              <p v-if="resp.text_answer" class="text-xs text-gray-900 dark:text-white whitespace-pre-line leading-relaxed">{{ resp.text_answer }}</p>
              <p v-else class="text-xs text-gray-400 italic">(No answer provided)</p>
            </div>

            <!-- File attachment -->
            <div v-if="resp.file_attachment" class="flex items-center justify-between p-3 bg-white dark:bg-gray-900 border rounded-xl mt-2">
              <span class="text-xs font-bold text-gray-700 dark:text-gray-300">📎 Submission Attachment</span>
              <a :href="resp.file_attachment" target="_blank" class="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white font-bold text-[10px] rounded-lg">
                View / Download
              </a>
            </div>

            <!-- Auto grading indicator -->
            <div v-if="resp.auto_graded" class="flex items-center gap-1.5 text-[10px] font-bold" :class="resp.is_correct ? 'text-emerald-600' : 'text-red-500'">
              {{ resp.is_correct ? '✓ Auto-Graded Correct' : '✗ Auto-Graded Incorrect' }}
            </div>
          </div>

          <!-- Grading Section -->
          <div class="pt-3 border-t border-gray-150 dark:border-gray-850">
            <!-- Editable mode (needs grading) -->
            <div v-if="isEditable" class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div class="flex flex-col gap-1">
                <label class="text-[10px] font-bold text-gray-550 uppercase">Award Points</label>
                <input
                  type="number"
                  step="0.5"
                  :max="resp.question_points || 100"
                  min="0"
                  v-model="gradedResponses[resp.id].points_awarded"
                  class="px-3 py-2 border rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 text-xs"
                />
              </div>
              <div class="md:col-span-2 flex flex-col gap-1">
                <label class="text-[10px] font-bold text-gray-550 uppercase">Question Feedback</label>
                <input
                  type="text"
                  v-model="gradedResponses[resp.id].teacher_feedback"
                  placeholder="Great work! / Needs improvement on..."
                  class="px-3 py-2 border rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 text-xs"
                />
              </div>
            </div>

            <!-- Read-only mode (already graded) -->
            <div v-else class="flex flex-wrap items-center gap-4">
              <div class="flex items-center gap-1.5">
                <span class="text-[10px] font-bold text-gray-500 uppercase">Awarded:</span>
                <span class="px-2 py-0.5 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 font-bold text-xs rounded-lg">{{ resp.points_awarded }} / {{ resp.question_points || 5 }} pts</span>
              </div>
              <div v-if="resp.teacher_feedback" class="flex items-center gap-1.5">
                <span class="text-[10px] font-bold text-gray-500 uppercase">Feedback:</span>
                <span class="text-xs text-gray-700 dark:text-gray-300 italic">"{{ resp.teacher_feedback }}"</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Overall Feedback & Submit -->
      <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm space-y-4">
        <div class="flex flex-col gap-1.5">
          <label class="text-xs font-bold text-gray-700 dark:text-gray-300">Overall Attempt Feedback</label>
          <textarea
            v-if="isEditable"
            rows="3"
            v-model="overallFeedback"
            placeholder="Write overall comments here..."
            class="px-3 py-2 text-xs border border-gray-300 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          ></textarea>
          <p v-else class="text-xs text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-950 p-3 rounded-xl border">
            {{ overallFeedback || '(No overall feedback provided)' }}
          </p>
        </div>

        <button
          v-if="isEditable"
          @click="handleSaveGrades"
          :disabled="saving"
          class="w-full py-3 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white font-bold text-xs rounded-xl shadow-md flex items-center justify-center gap-2 transition-colors"
        >
          <span v-if="saving" class="animate-spin inline-block w-3 h-3 border-2 border-white border-t-transparent rounded-full"></span>
          Submit Gradebook & Feedback
        </button>
      </div>
    </template>
  </div>
</template>
