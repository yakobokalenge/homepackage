<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { useAssessmentStore } from '../../stores/assessment'
import { useNotificationStore } from '../../stores/notification'

const assessmentStore = useAssessmentStore()
const notificationStore = useNotificationStore()

const loading = ref(true)
const selectedType = ref('')
const selectedStatus = ref('')

async function loadData() {
  loading.value = true
  try {
    const params: Record<string, any> = {}
    if (selectedType.value) params.assessment_type = selectedType.value
    if (selectedStatus.value) params.status = selectedStatus.value
    await assessmentStore.fetchAssessments(params)
  } catch {
    notificationStore.error('Failed to load assessments.')
  } finally {
    loading.value = false
  }
}

async function handlePublish(id: string) {
  try {
    await useAssessmentStore().$state // verify store access
    const res = await assessmentStore.updateAssessment(id, { status: 'published' })
    notificationStore.success(`Published: "${res.title}" is now available.`)
  } catch {
    notificationStore.error('Failed to publish assessment.')
  }
}

async function handleClose(id: string) {
  try {
    const res = await assessmentStore.updateAssessment(id, { status: 'closed' })
    notificationStore.success(`Closed: "${res.title}" is now closed.`)
  } catch {
    notificationStore.error('Failed to close assessment.')
  }
}

async function handleDuplicate(id: string) {
  try {
    const res = await assessmentStore.duplicateAssessment(id)
    notificationStore.success(`Duplicated: Created duplicate draft "${res.title}".`)
    loadData()
  } catch {
    notificationStore.error('Failed to duplicate assessment.')
  }
}

async function handleDelete(id: string) {
  if (!confirm('Are you sure you want to delete this assessment? This action is irreversible.')) return
  try {
    await assessmentStore.deleteAssessment(id)
    notificationStore.success('Assessment deleted successfully.')
  } catch {
    notificationStore.error('Failed to delete assessment.')
  }
}

onMounted(loadData)
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Assessment Hub</h1>
        <p class="text-sm text-gray-500 mt-1">Manage quizzes, exams, assignments, and home packages for classrooms.</p>
      </div>
      <RouterLink
        to="/teacher/assessments/create"
        class="px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl shadow-md flex items-center gap-2 hover:scale-[1.02] active:scale-[0.98] transition-all"
      >
        ➕ Create Assessment
      </RouterLink>
    </div>

    <!-- Filters -->
    <div class="p-4 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl flex flex-wrap gap-4 items-center">
      <div class="flex flex-col gap-1">
        <label class="text-[10px] font-bold text-gray-500 uppercase">Assessment Type</label>
        <select
          v-model="selectedType"
          @change="loadData"
          class="px-3 py-1.5 border border-gray-205 dark:border-gray-800 rounded-lg text-xs bg-white dark:bg-gray-900 text-gray-800 dark:text-white focus:outline-none"
        >
          <option value="">All Types</option>
          <option value="quiz">Quiz</option>
          <option value="test">Test</option>
          <option value="assignment">Assignment</option>
          <option value="exam">Exam</option>
          <option value="home_package">Home Package</option>
        </select>
      </div>
      <div class="flex flex-col gap-1">
        <label class="text-[10px] font-bold text-gray-500 uppercase">Status</label>
        <select
          v-model="selectedStatus"
          @change="loadData"
          class="px-3 py-1.5 border border-gray-205 dark:border-gray-800 rounded-lg text-xs bg-white dark:bg-gray-900 text-gray-800 dark:text-white focus:outline-none"
        >
          <option value="">All Statuses</option>
          <option value="draft">Draft</option>
          <option value="published">Published</option>
          <option value="closed">Closed</option>
        </select>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-20 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl">
      <span class="animate-spin inline-block w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mb-4"></span>
      <p class="text-gray-500">Loading Assessments...</p>
    </div>

    <!-- Empty State -->
    <div v-else-if="assessmentStore.assessments.length === 0" class="text-center py-20 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl">
      <span class="text-4xl block mb-2">📋</span>
      <p class="text-gray-600 dark:text-gray-400 font-medium">No assessments found.</p>
      <p class="text-xs text-gray-400 mt-1">Get started by creating your first homework package or quiz.</p>
    </div>

    <!-- Assessment Cards Grid -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div
        v-for="item in assessmentStore.assessments"
        :key="item.id"
        class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-5 hover:shadow-lg transition-all flex flex-col justify-between"
      >
        <div class="space-y-3">
          <!-- Tag Header -->
          <div class="flex items-center justify-between">
            <span class="px-2 py-0.5 bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 text-[10px] font-bold rounded-lg uppercase tracking-wider">
              {{ item.assessment_type.replace('_', ' ') }}
            </span>
            <span :class="[
              item.status === 'published' ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/20 dark:text-emerald-400' :
              item.status === 'closed' ? 'bg-red-100 text-red-800 dark:bg-red-950/20 dark:text-red-400' :
              'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-400',
              'px-2 py-0.5 text-[9px] font-bold rounded-lg uppercase tracking-wider'
            ]">
              {{ item.status }}
            </span>
          </div>

          <!-- Title and details -->
          <div>
            <h3 class="text-sm md:text-base font-bold text-gray-900 dark:text-white truncate" :title="item.title">{{ item.title }}</h3>
            <p class="text-[11px] text-gray-500 mt-1">Subject: {{ item.subject_name }} · Classroom: {{ item.classroom_name || 'General' }}</p>
          </div>

          <!-- Stats list -->
          <div class="grid grid-cols-2 gap-2 p-2.5 bg-gray-50 dark:bg-gray-900/50 rounded-xl text-[10px] font-medium text-gray-500">
            <div>Questions: <span class="text-gray-900 dark:text-white font-bold">{{ item.question_count }}</span></div>
            <div>Total Points: <span class="text-gray-900 dark:text-white font-bold">{{ item.total_points }} pts</span></div>
            <div>Time Limit: <span class="text-gray-900 dark:text-white font-bold">{{ item.time_limit_minutes ? `${item.time_limit_minutes}m` : 'None' }}</span></div>
            <div>Proctored: <span class="text-gray-900 dark:text-white font-bold">{{ item.is_proctored ? 'Yes 🛡️' : 'No' }}</span></div>
          </div>
        </div>

        <!-- Actions -->
        <div class="mt-5 pt-3 border-t border-gray-150 dark:border-gray-800 flex flex-wrap gap-2 justify-end">
          <RouterLink
            :to="`/teacher/assessments/${item.id}`"
            class="px-2.5 py-1.5 bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 hover:bg-blue-100 dark:hover:bg-blue-900/50 text-[10px] font-bold rounded-lg transition-all"
          >
            🔍 Details
          </RouterLink>
          <button
            @click="handleDuplicate(item.id)"
            class="px-2.5 py-1.5 bg-gray-50 dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-100 text-[10px] font-bold rounded-lg transition-all"
          >
            📋 Clone
          </button>
          
          <button
            v-if="item.status === 'draft'"
            @click="handlePublish(item.id)"
            class="px-2.5 py-1.5 bg-emerald-600 hover:bg-emerald-750 text-white text-[10px] font-bold rounded-lg transition-all"
          >
            🚀 Publish
          </button>
          <button
            v-if="item.status === 'published'"
            @click="handleClose(item.id)"
            class="px-2.5 py-1.5 bg-amber-600 hover:bg-amber-700 text-white text-[10px] font-bold rounded-lg transition-all"
          >
            🛑 Close
          </button>
          
          <button
            @click="handleDelete(item.id)"
            class="px-2.5 py-1.5 hover:bg-red-50 text-red-500 text-[10px] font-bold rounded-lg transition-all"
          >
            🗑️ Delete
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
