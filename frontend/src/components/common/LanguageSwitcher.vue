<script setup lang="ts">
import { useI18n } from 'vue-i18n'

defineProps<{ dark?: boolean }>()

const { locale } = useI18n()

function toggleLanguage() {
  locale.value = locale.value === 'en' ? 'sw' : 'en'
  localStorage.setItem('locale', locale.value)
}
</script>

<template>
  <button
    @click="toggleLanguage"
    :class="[
      'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200',
      dark
        ? 'bg-white/10 text-white hover:bg-white/20'
        : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
    ]"
  >
    <span>🌐</span>
    <span>{{ locale === 'en' ? 'SW' : 'EN' }}</span>
  </button>
</template>
