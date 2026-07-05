<script setup lang="ts">
import { useRoute } from 'vue-router'

const route = useRoute()
const assessmentId = route.params.id as string

const session = {
  student: 'Amina Hassan', exam: 'Biology Mid-Term', status: 'flagged', totalFlags: 7,
  started: '2024-02-15 10:00', ended: '2024-02-15 12:00', videoChunks: 72,
}

const flags = [
  { time: '10:05', type: 'Tab Switch', severity: 'high', desc: 'Tab switch #1' },
  { time: '10:12', type: 'No Face', severity: 'high', desc: 'No face detected for 5 seconds' },
  { time: '10:30', type: 'Multiple Faces', severity: 'high', desc: '2 faces detected' },
  { time: '10:45', type: 'Looking Away', severity: 'medium', desc: 'Head turned yaw=35°' },
  { time: '11:02', type: 'Audio Detected', severity: 'medium', desc: 'Voice/noise detected' },
  { time: '11:15', type: 'Copy/Paste', severity: 'low', desc: 'Ctrl+C blocked' },
  { time: '11:40', type: 'Tab Switch', severity: 'high', desc: 'Tab switch #2' },
]

const severityColors: Record<string, string> = {
  high: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  medium: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
  low: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">🔒 Review Proctoring</h1>
      <button class="px-5 py-2.5 bg-emerald-600 text-white font-semibold rounded-xl hover:bg-emerald-700 transition-colors">
        ✅ Mark as Reviewed
      </button>
    </div>

    <!-- Session Info -->
    <div class="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-6 grid grid-cols-2 md:grid-cols-4 gap-4">
      <div><p class="text-xs text-gray-500">Student</p><p class="font-semibold text-gray-900 dark:text-white">{{ session.student }}</p></div>
      <div><p class="text-xs text-gray-500">Exam</p><p class="font-semibold text-gray-900 dark:text-white">{{ session.exam }}</p></div>
      <div><p class="text-xs text-gray-500">Status</p><span class="px-2 py-0.5 bg-red-100 text-red-700 text-xs font-medium rounded-full">{{ session.status }}</span></div>
      <div><p class="text-xs text-gray-500">Total Flags</p><p class="text-2xl font-bold text-red-600">{{ session.totalFlags }}</p></div>
    </div>

    <!-- Violation Timeline -->
    <div class="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-6">
      <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Violation Timeline</h2>
      <div class="space-y-3">
        <div v-for="(flag, i) in flags" :key="i" class="flex items-start gap-4 p-3 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
          <div class="text-sm font-mono text-gray-500 min-w-[60px]">{{ flag.time }}</div>
          <span :class="['px-2 py-0.5 text-xs font-medium rounded-full min-w-[80px] text-center', severityColors[flag.severity]]">{{ flag.severity }}</span>
          <div>
            <p class="text-sm font-medium text-gray-900 dark:text-white">{{ flag.type }}</p>
            <p class="text-xs text-gray-500">{{ flag.desc }}</p>
          </div>
          <button class="ml-auto text-xs text-gray-400 hover:text-gray-600">Dismiss</button>
        </div>
      </div>
    </div>

    <!-- Teacher Notes -->
    <div class="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-6">
      <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Review Notes</h2>
      <textarea rows="4" placeholder="Add your review notes here..." class="w-full p-4 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"></textarea>
    </div>
  </div>
</template>
