<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'
import { assessmentService } from '@/services/assessment.service'
import type { Assessment } from '@/types'

const { t } = useI18n()
const tab = ref<'all' | 'quiz' | 'test' | 'assignment' | 'exam' | 'home_package'>('all')
const loading = ref(true)
const errorMessage = ref('')
const assessmentsList = ref<Assessment[]>([])

onMounted(async () => {
  try {
    const res = await assessmentService.list({ status: 'published' })
    if (res && Array.isArray(res.assessments)) {
      assessmentsList.value = res.assessments
    } else if (res && Array.isArray((res as any).results)) {
      assessmentsList.value = (res as any).results
    } else if (Array.isArray(res)) {
      assessmentsList.value = res
    }
  } catch (err: any) {
    errorMessage.value = 'Failed to load assessments.'
  } finally {
    loading.value = false
  }
})

const filtered = computed(() => {
  if (tab.value === 'all') return assessmentsList.value
  return assessmentsList.value.filter(a => a.assessment_type === tab.value)
})

const typeIcons: Record<string, string> = { quiz: '📋', test: '📝', exam: '🎓', assignment: '📚', home_package: '🏠' }
const typeColors: Record<string, string> = {
  quiz: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  test: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
  exam: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  assignment: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400',
  home_package: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">{{ t('nav.assessments') }}</h1>
    </div>

    <!-- Tabs -->
    <div class="flex flex-wrap gap-2 bg-gray-100 dark:bg-gray-800 rounded-xl p-1 w-fit">
      <button v-for="t in ['all', 'quiz', 'test', 'assignment', 'exam', 'home_package'] as const" :key="t" @click="tab = t"
        :class="['px-4 py-2 rounded-lg text-sm font-medium transition-all capitalize whitespace-nowrap', tab === t ? 'bg-white dark:bg-gray-700 shadow-sm text-blue-600 dark:text-blue-400' : 'text-gray-500 hover:text-gray-700']">
        {{ t === 'all' ? 'All' : t.replace('_', ' ') + 's' }}
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-20 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl">
      <span class="animate-spin inline-block w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mb-4"></span>
      <p class="text-gray-500">Loading Assessments...</p>
    </div>

    <!-- Empty State -->
    <div v-else-if="filtered.length === 0" class="text-center py-20 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl">
      <span class="text-4xl block mb-3">📁</span>
      <p class="text-gray-500 font-medium">No assessments found in this category.</p>
    </div>

    <!-- Cards -->
    <div v-else class="grid gap-4">
      <div v-for="a in filtered" :key="a.id"
        class="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-5 hover:shadow-lg transition-shadow flex items-center gap-4">
        <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-emerald-500 flex items-center justify-center text-2xl">
          {{ typeIcons[a.assessment_type] || '📝' }}
        </div>
        <div class="flex-1 min-w-0">
          <h3 class="font-semibold text-gray-900 dark:text-white truncate">{{ a.title }}</h3>
          <div class="flex items-center gap-3 mt-1 text-xs text-gray-500">
            <span>{{ a.subject_name || 'Subject' }}</span>
            <span :class="['px-2 py-0.5 rounded-full text-xs font-medium', typeColors[a.assessment_type] || 'bg-gray-100 text-gray-700']">{{ a.assessment_type.replace('_', ' ') }}</span>
            <span v-if="a.duration_minutes">⏱ {{ a.duration_minutes }}min</span>
            <span v-if="a.requires_proctoring" class="px-2 py-0.5 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 rounded-full">🔒 Proctored</span>
            <span v-if="a.is_file_based" class="px-2 py-0.5 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-400 rounded-full">📁 File Upload</span>
          </div>
        </div>
        <div class="text-right">
          <RouterLink :to="a.requires_proctoring ? `/student/exam/${a.id}/proctored` : `/student/exam/${a.id}`"
            class="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-xl hover:bg-blue-700 transition-colors inline-block">
            Start
          </RouterLink>
        </div>
      </div>
    </div>
  </div>
</template>
