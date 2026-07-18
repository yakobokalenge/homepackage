<script setup lang="ts">
import { computed } from 'vue'
import { useExamStore } from '../../stores/exam'

const examStore = useExamStore()

const timeString = computed(() => {
  if (examStore.timeRemainingSeconds === null) return 'No Time Limit'
  
  const s = examStore.timeRemainingSeconds
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  const sec = s % 60
  
  const hStr = h > 0 ? `${h}:` : ''
  const mStr = String(m).padStart(2, '0')
  const sStr = String(sec).padStart(2, '0')
  
  return `${hStr}${mStr}:${sStr}`
})

const isCritical = computed(() => {
  return examStore.timeRemainingSeconds !== null && examStore.timeRemainingSeconds < 60
})

const isWarning = computed(() => {
  return examStore.timeRemainingSeconds !== null && examStore.timeRemainingSeconds >= 60 && examStore.timeRemainingSeconds < 300
})
</script>

<template>
  <div
    :class="[
      isCritical
        ? 'bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 animate-pulse'
        : isWarning
        ? 'bg-amber-50 dark:bg-amber-950/20 border-amber-200 dark:border-amber-800 text-amber-700 dark:text-amber-400'
        : 'bg-gray-50 dark:bg-gray-900 border-gray-200 dark:border-gray-800 text-gray-700 dark:text-gray-300',
      'flex items-center gap-2 px-3 py-1.5 border rounded-xl font-mono text-sm font-bold shadow-sm transition-all duration-300'
    ]"
  >
    <span class="text-base">⏳</span>
    <span>{{ timeString }}</span>
  </div>
</template>
