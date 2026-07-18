<script setup lang="ts">
import { computed } from 'vue'
import { useExamStore } from '../../stores/exam'

const examStore = useExamStore()

// Determine if a question is answered
function isAnswered(questionId: string) {
  const ans = examStore.localAnswers[questionId]
  if (!ans) return false
  
  // MCQ / TrueFalse / MultiSelect
  if (ans.selected_options && ans.selected_options.length > 0) return true
  
  // Fillblank / ShortAnswer / Essay
  if (ans.text_answer && ans.text_answer.trim() !== '') return true
  
  // Matching
  if (ans.matching_pairs && Object.keys(ans.matching_pairs).length > 0) return true
  
  // Ordering
  if (ans.ordering_sequence && ans.ordering_sequence.length > 0) return true
  
  return false
}
</script>

<template>
  <div class="space-y-4">
    <h3 class="text-xs font-bold text-gray-500 uppercase tracking-wider">Question Navigator</h3>
    <div class="grid grid-cols-5 gap-2 max-h-[250px] overflow-y-auto pr-1">
      <button
        v-for="(aq, idx) in examStore.questions"
        :key="aq.id"
        @click="examStore.setQuestionIndex(idx)"
        :class="[
          examStore.activeQuestionIndex === idx
            ? 'bg-blue-600 border-blue-600 text-white font-bold ring-2 ring-blue-300'
            : isAnswered(aq.question.id)
            ? 'bg-emerald-50 dark:bg-emerald-950/20 border-emerald-300 dark:border-emerald-800 text-emerald-700 dark:text-emerald-400 font-bold'
            : 'bg-white dark:bg-gray-900 border-gray-250 dark:border-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800',
          'w-8 h-8 rounded-xl border flex items-center justify-center text-xs transition-all duration-200 shadow-sm'
        ]"
      >
        {{ idx + 1 }}
      </button>
    </div>

    <!-- Status Legend -->
    <div class="pt-3 border-t border-gray-150 dark:border-gray-800 flex items-center justify-between text-[10px] text-gray-500 font-medium">
      <span class="flex items-center gap-1.5">
        <span class="w-2.5 h-2.5 rounded bg-emerald-500 border border-emerald-600 block"></span>
        Answered
      </span>
      <span class="flex items-center gap-1.5">
        <span class="w-2.5 h-2.5 rounded bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-700 block"></span>
        Unanswered
      </span>
    </div>
  </div>
</template>
