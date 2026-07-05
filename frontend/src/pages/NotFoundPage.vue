<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-950 p-4">
    <div class="text-center">
      <p class="text-8xl mb-6">📚</p>
      <h1 class="text-4xl font-bold text-gray-900 dark:text-white mb-2">Page Not Found</h1>
      <p class="text-gray-500 mb-8">The page you're looking for doesn't exist or has been moved.</p>
      <RouterLink to="/" class="px-8 py-3 bg-gradient-to-r from-blue-600 to-emerald-600 text-white font-semibold rounded-xl hover:shadow-lg transition-all">
        Go Home
      </RouterLink>
    </div>
  </div>
</template>
