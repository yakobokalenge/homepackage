<script setup lang="ts">
import { ref } from 'vue'

const open = ref(false)
const count = ref(3)
</script>

<template>
  <div class="relative">
    <button @click="open = !open" class="relative p-2 rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
      <span class="text-lg">🔔</span>
      <span v-if="count > 0" class="absolute -top-0.5 -right-0.5 w-4 h-4 bg-red-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center">
        {{ count > 9 ? '9+' : count }}
      </span>
    </button>

    <Transition name="dropdown">
      <div v-if="open" class="absolute right-0 mt-2 w-80 bg-white dark:bg-gray-900 rounded-xl shadow-xl border border-gray-200 dark:border-gray-800 overflow-hidden z-50">
        <div class="p-3 border-b border-gray-200 dark:border-gray-800 flex justify-between items-center">
          <h3 class="font-semibold text-sm text-gray-900 dark:text-gray-100">Notifications</h3>
          <button class="text-xs text-blue-600 hover:underline">Mark all read</button>
        </div>
        <div class="max-h-80 overflow-y-auto">
          <div class="p-3 border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors cursor-pointer">
            <p class="text-sm font-medium text-gray-900 dark:text-gray-100">New quiz available</p>
            <p class="text-xs text-gray-500 mt-0.5">Mathematics — Form 3 Weekly Package</p>
            <p class="text-xs text-gray-400 mt-1">2 hours ago</p>
          </div>
          <div class="p-3 border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors cursor-pointer">
            <p class="text-sm font-medium text-gray-900 dark:text-gray-100">Exam results ready</p>
            <p class="text-xs text-gray-500 mt-0.5">Biology mid-term has been graded</p>
            <p class="text-xs text-gray-400 mt-1">5 hours ago</p>
          </div>
          <div class="p-3 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors cursor-pointer">
            <p class="text-sm font-medium text-gray-900 dark:text-gray-100">Subscription reminder</p>
            <p class="text-xs text-gray-500 mt-0.5">Your Premium plan renews in 3 days</p>
            <p class="text-xs text-gray-400 mt-1">1 day ago</p>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.dropdown-enter-active, .dropdown-leave-active { transition: all 0.2s ease; }
.dropdown-enter-from, .dropdown-leave-to { opacity: 0; transform: translateY(-4px) scale(0.95); }
</style>
