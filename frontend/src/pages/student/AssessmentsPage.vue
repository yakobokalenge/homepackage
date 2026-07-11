<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { assessmentService } from '@/services/assessment.service'
import type { Assessment } from '@/types/assessment'

const router = useRouter()
const loading = ref(true)
const assessmentsList = ref<Assessment[]>([])

onMounted(async () => {
  try {
    assessmentsList.value = await assessmentService.list({ status: 'published' })
  } catch (err) {
    console.error('Failed to load assessments:', err)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="space-y-6">
    <!-- Title -->
    <div>
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Revision Assessments</h1>
      <p class="text-sm text-gray-500 mt-1">Take interactive practice quizzes and homework exams online.</p>
    </div>

    <!-- Loader -->
    <div v-if="loading" class="text-center py-20 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl">
      <span class="animate-spin inline-block w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mb-4"></span>
      <p class="text-gray-500">Loading Available Assessments...</p>
    </div>

    <!-- Grid -->
    <template v-else>
      <div v-if="assessmentsList.length === 0" class="text-center py-16 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl text-gray-500">
        <span class="text-4xl block mb-2">🎉</span>
        No assessments are currently published for your stream. Check back later!
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div v-for="ass in assessmentsList" :key="ass.id" class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-5 hover:shadow-lg transition-all flex flex-col justify-between space-y-4">
          <div class="space-y-2">
            <div class="flex justify-between items-center text-xs">
              <span class="px-2 py-0.5 bg-blue-50 text-blue-700 dark:bg-blue-950/20 dark:text-blue-400 font-bold uppercase rounded">{{ ass.assessment_type.replace('_', ' ') }}</span>
              <span class="text-gray-500 font-medium">{{ ass.duration_minutes ? `${ass.duration_minutes} min` : 'No limit' }}</span>
            </div>
            <h3 class="font-bold text-gray-900 dark:text-white text-base leading-snug">{{ ass.title }}</h3>
            <p class="text-xs text-gray-500 line-clamp-2">{{ ass.description || 'No description provided.' }}</p>
          </div>

          <div class="pt-4 border-t border-gray-100 dark:border-gray-850 flex items-center justify-between">
            <div class="text-xs">
              <span class="text-gray-500 block">Subject:</span>
              <span class="font-bold text-indigo-650 dark:text-indigo-400">{{ ass.subject_name }}</span>
            </div>
            <button @click="router.push(`/student/exam/${ass.id}`)" class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl text-xs transition-all shadow-sm">
              Start Assessment
            </button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
