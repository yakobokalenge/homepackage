<script setup lang="ts">
import { RouterView } from 'vue-router'
</script>

<template>
  <div class="min-h-screen bg-gray-100 dark:bg-gray-950">
    <!-- Minimal header for exam mode -->
    <header class="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 px-4 py-2 flex items-center justify-between">
      <div class="flex items-center gap-2 text-sm font-semibold text-blue-700 dark:text-blue-400">
        <span>📚</span> HomePackage
      </div>
      <div class="text-sm text-gray-500">Exam Mode</div>
    </header>
    <main class="p-4 md:p-6">
      <RouterView />
    </main>
  </div>
</template>
