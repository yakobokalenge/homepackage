<script setup lang="ts">
import { ref, computed } from 'vue'
import { useProctoring } from '../../composables/useProctoring'

const props = defineProps<{
  proctoring: ReturnType<typeof useProctoring>
  videoRef: HTMLVideoElement | null
}>()

const isMinimized = ref(false)

const violationStatusText = computed(() => {
  const flags = props.proctoring.faceDetector.faceCount.value
  if (flags === 0) return 'No face detected! Return to camera.'
  if (flags > 1) return 'Multiple faces detected!'
  if (props.proctoring.faceDetector.isLookingAway.value) return 'Please focus on the screen.'
  if (props.proctoring.audioMonitor.isVoiceDetected.value) return 'Audio/noise detected.'
  return null
})
</script>

<template>
  <div
    v-show="props.proctoring.isStarted.value"
    :class="[
      isMinimized ? 'w-16 h-16' : 'w-48 sm:w-56 h-auto',
      'fixed bottom-6 right-6 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl shadow-2xl overflow-hidden z-50 transition-all duration-300 flex flex-col'
    ]"
  >
    <!-- Header Controls -->
    <div class="px-3 py-1.5 bg-gray-50 dark:bg-gray-800 flex items-center justify-between border-b border-gray-150 dark:border-gray-700">
      <span class="text-[10px] font-bold text-gray-550 flex items-center gap-1 uppercase tracking-wider">
        <span class="w-1.5 h-1.5 rounded-full bg-red-600 animate-ping"></span>
        Proctored
      </span>
      <button @click="isMinimized = !isMinimized" class="text-xs text-gray-400 hover:text-gray-600 dark:hover:text-white">
        {{ isMinimized ? '▲' : '▼' }}
      </button>
    </div>

    <!-- Video Preview & Alerts Container -->
    <div v-show="!isMinimized" class="relative flex-1 bg-black aspect-video flex items-center justify-center">
      <!-- Alerts overlay -->
      <div
        v-if="violationStatusText"
        class="absolute inset-0 bg-red-950/70 border border-red-500 flex items-center justify-center p-3 text-center z-10 transition-all"
      >
        <p class="text-[10px] sm:text-xs font-bold text-red-300 animate-pulse leading-snug">{{ violationStatusText }}</p>
      </div>

      <!-- Video element reference wrapper -->
      <slot></slot>
      
      <!-- Video missing indicator -->
      <div v-if="!props.proctoring.isCameraActive.value" class="text-center p-3 text-gray-500">
        <span class="text-xl block">📷</span>
        <span class="text-[10px]">Initializing camera...</span>
      </div>
    </div>

    <!-- Footer indicators -->
    <div v-show="!isMinimized" class="p-2 bg-gray-50 dark:bg-gray-800 flex items-center justify-between text-[9px] font-bold text-gray-550 border-t border-gray-150 dark:border-gray-700">
      <span :class="props.proctoring.lockdown.isFullscreen.value ? 'text-emerald-600' : 'text-amber-500'">
        {{ props.proctoring.lockdown.isFullscreen.value ? 'Fullscreen ✓' : 'Exited Fullscreen' }}
      </span>
      <span :class="props.proctoring.audioMonitor.audioLevel.value > 30 ? 'text-red-500' : 'text-gray-400'">
        Mic: {{ props.proctoring.audioMonitor.audioLevel.value.toFixed(0) }}dB
      </span>
    </div>
  </div>
</template>
