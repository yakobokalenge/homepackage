import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface ToastMessage {
  id: number
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message?: string
  duration?: number
}

let nextId = 0

export const useNotificationStore = defineStore('notification', () => {
  const toasts = ref<ToastMessage[]>([])
  const unreadCount = ref(0)

  function addToast(type: ToastMessage['type'], title: string, message?: string, duration = 5000) {
    const id = nextId++
    toasts.value.push({ id, type, title, message, duration })
    if (duration > 0) {
      setTimeout(() => removeToast(id), duration)
    }
  }

  function removeToast(id: number) {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }

  const success = (title: string, message?: string) => addToast('success', title, message)
  const error = (title: string, message?: string) => addToast('error', title, message)
  const warning = (title: string, message?: string) => addToast('warning', title, message)
  const info = (title: string, message?: string) => addToast('info', title, message)

  return { toasts, unreadCount, addToast, removeToast, success, error, warning, info }
})
