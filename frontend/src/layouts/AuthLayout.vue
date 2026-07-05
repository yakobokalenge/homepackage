<script setup lang="ts">
import { RouterView } from 'vue-router'
import LanguageSwitcher from '@/components/common/LanguageSwitcher.vue'
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-900 via-blue-800 to-emerald-900 px-4 py-8">
    <!-- Animated background orbs -->
    <div class="fixed inset-0 overflow-hidden pointer-events-none">
      <div class="absolute -top-40 -right-40 w-80 h-80 bg-blue-500/20 rounded-full blur-3xl animate-pulse"></div>
      <div class="absolute -bottom-40 -left-40 w-96 h-96 bg-emerald-500/15 rounded-full blur-3xl animate-pulse" style="animation-delay: 2s;"></div>
      <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-amber-500/10 rounded-full blur-3xl animate-pulse" style="animation-delay: 4s;"></div>
    </div>

    <div class="relative w-full max-w-md">
      <!-- Logo -->
      <div class="text-center mb-8">
        <RouterLink to="/" class="inline-flex items-center gap-2 text-2xl font-bold text-white">
          <span class="text-3xl">📚</span>
          <span>HomePackage</span>
        </RouterLink>
      </div>

      <!-- Auth Card -->
      <div class="bg-white/10 backdrop-blur-xl rounded-2xl border border-white/20 shadow-2xl p-8">
        <RouterView />
      </div>

      <!-- Language Switcher -->
      <div class="mt-6 flex justify-center">
        <LanguageSwitcher dark />
      </div>
    </div>
  </div>
</template>
