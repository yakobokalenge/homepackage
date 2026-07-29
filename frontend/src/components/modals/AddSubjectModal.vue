<template>
  <div v-if="modelValue" class="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
    <div class="bg-white dark:bg-gray-900 rounded-3xl p-6 w-full max-w-md border border-gray-100 dark:border-gray-800 shadow-2xl transform transition-all">
      <div class="flex justify-between items-center mb-6">
        <div>
          <h3 class="text-lg font-bold text-gray-900 dark:text-white">Add New Subject</h3>
          <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">Create a new subject for the database</p>
        </div>
        <button @click="close" class="text-gray-400 hover:text-gray-600 dark:hover:text-white bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 p-2 rounded-xl transition-colors">
          ❌
        </button>
      </div>
      
      <form @submit.prevent="submit" class="space-y-4">
        <div>
          <label class="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1.5">Subject Name <span class="text-red-500">*</span></label>
          <input 
            v-model="form.name" 
            required 
            placeholder="e.g. Computer Science" 
            class="w-full px-4 py-2.5 text-sm border border-gray-200 dark:border-gray-700 rounded-xl bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 outline-none transition-all"
          />
        </div>

        <div>
          <label class="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1.5">Education Level (Optional)</label>
          <select 
            v-model="form.education_level" 
            class="w-full px-4 py-2.5 text-sm border border-gray-200 dark:border-gray-700 rounded-xl bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 outline-none transition-all"
          >
            <option value="">Any / General</option>
            <option value="Pre-Primary">Pre-Primary</option>
            <option value="Primary">Primary</option>
            <option value="Secondary">Secondary (O-Level)</option>
            <option value="High School">High School (A-Level)</option>
            <option value="College/University">College / University</option>
          </select>
        </div>

        <div class="pt-4 flex gap-3">
          <button 
            type="button" 
            @click="close"
            class="flex-1 px-4 py-2.5 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 text-sm font-bold rounded-xl transition-colors"
          >
            Cancel
          </button>
          <button 
            type="submit" 
            :disabled="loading"
            class="flex-1 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-bold rounded-xl transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
          >
            <span v-if="loading" class="animate-spin inline-block w-4 h-4 border-2 border-white/40 border-t-white rounded-full"></span>
            {{ loading ? 'Saving...' : 'Add Subject' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import api from '@/services/api'
import { useNotificationStore } from '@/stores/notification'

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits(['update:modelValue', 'subject-added'])
const notificationStore = useNotificationStore()

const loading = ref(false)
const form = ref({
  name: '',
  education_level: ''
})

// Reset form when opened
watch(() => props.modelValue, (isOpen) => {
  if (isOpen) {
    form.value = { name: '', education_level: '' }
  }
})

function close() {
  emit('update:modelValue', false)
}

function generateCode(name: string): string {
  const chars = name.replace(/[^a-zA-Z0-9]/g, '').toUpperCase()
  const prefix = chars.substring(0, 3).padEnd(3, 'X')
  const randomNum = Math.floor(100 + Math.random() * 900)
  return `${prefix}-${randomNum}`
}

async function submit() {
  if (!form.value.name.trim()) return

  loading.value = true
  try {
    const payload = {
      name: form.value.name.trim(),
      code: generateCode(form.value.name),
      education_level: form.value.education_level
    }

    const { data } = await api.post('/content/subjects/', payload)
    
    notificationStore.success('Subject added successfully!')
    emit('subject-added', data)
    close()
  } catch (err: any) {
    console.error(err)
    notificationStore.error(err.response?.data?.detail || err.response?.data?.code?.[0] || 'Failed to add subject.')
  } finally {
    loading.value = false
  }
}
</script>
