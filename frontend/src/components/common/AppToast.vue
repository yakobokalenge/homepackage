<script setup lang="ts">
import { useNotificationStore, type ToastMessage } from '@/stores/notification'
import { storeToRefs } from 'pinia'

const store = useNotificationStore()
const { toasts } = storeToRefs(store)

const iconMap: Record<ToastMessage['type'], string> = {
  success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️'
}
const colorMap: Record<ToastMessage['type'], string> = {
  success: 'border-emerald-500 bg-emerald-50 dark:bg-emerald-900/30',
  error: 'border-red-500 bg-red-50 dark:bg-red-900/30',
  warning: 'border-amber-500 bg-amber-50 dark:bg-amber-900/30',
  info: 'border-blue-500 bg-blue-50 dark:bg-blue-900/30'
}
</script>

<template>
  <Teleport to="body">
    <div class="fixed top-4 right-4 z-[9999] flex flex-col gap-3 max-w-sm w-full pointer-events-none">
      <TransitionGroup name="toast">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          :class="['pointer-events-auto border-l-4 rounded-xl p-4 shadow-lg backdrop-blur-sm', colorMap[toast.type]]"
        >
          <div class="flex items-start gap-3">
            <span class="text-lg mt-0.5">{{ iconMap[toast.type] }}</span>
            <div class="flex-1 min-w-0">
              <p class="font-semibold text-sm text-gray-900 dark:text-gray-100">{{ toast.title }}</p>
              <p v-if="toast.message" class="text-xs text-gray-600 dark:text-gray-300 mt-1">{{ toast.message }}</p>
            </div>
            <button @click="store.removeToast(toast.id)" class="text-gray-400 hover:text-gray-600 text-lg leading-none">&times;</button>
          </div>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style scoped>
.toast-enter-active { animation: slideIn 0.3s ease-out; }
.toast-leave-active { animation: slideOut 0.3s ease-in; }
@keyframes slideIn { from { opacity: 0; transform: translateX(100%); } to { opacity: 1; transform: translateX(0); } }
@keyframes slideOut { from { opacity: 1; transform: translateX(0); } to { opacity: 0; transform: translateX(100%); } }
</style>
