<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useI18n } from 'vue-i18n'
import LanguageSwitcher from '@/components/common/LanguageSwitcher.vue'
import NotificationBell from '@/components/nav/NotificationBell.vue'

const { t } = useI18n()
const auth = useAuthStore()
const route = useRoute()
const mobileOpen = ref(false)
</script>

<template>
  <nav class="bg-white/80 dark:bg-gray-900/80 backdrop-blur-xl border-b border-gray-200/50 dark:border-gray-800/50 sticky top-0 z-40">
    <div class="max-w-7xl mx-auto px-4 sm:px-6">
      <div class="flex items-center justify-between h-16">
        <!-- Logo -->
        <RouterLink to="/" class="flex items-center gap-2 text-xl font-bold text-blue-700 dark:text-blue-400 hover:opacity-80 transition-opacity">
          <span class="text-2xl">📚</span>
          <span class="hidden sm:inline">HomePackage</span>
        </RouterLink>

        <!-- Desktop Nav -->
        <div class="hidden md:flex items-center gap-6">
          <RouterLink to="/" :class="['text-sm font-medium transition-colors', route.path === '/' ? 'text-blue-600' : 'text-gray-600 dark:text-gray-300 hover:text-blue-600']">
            {{ t('nav.home') }}
          </RouterLink>
          <RouterLink to="/plans" :class="['text-sm font-medium transition-colors', route.path === '/plans' ? 'text-blue-600' : 'text-gray-600 dark:text-gray-300 hover:text-blue-600']">
            {{ t('nav.plans') }}
          </RouterLink>
        </div>

        <!-- Right -->
        <div class="flex items-center gap-3">
          <LanguageSwitcher />
          <template v-if="auth.isAuthenticated">
            <NotificationBell />
            <RouterLink
              :to="auth.isTeacher ? '/teacher/dashboard' : '/student/dashboard'"
              class="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-xl hover:bg-blue-700 transition-colors"
            >
              {{ t('nav.dashboard') }}
            </RouterLink>
          </template>
          <template v-else>
            <RouterLink to="/auth/login" class="text-sm font-medium text-gray-600 dark:text-gray-300 hover:text-blue-600 transition-colors">
              {{ t('nav.login') }}
            </RouterLink>
            <RouterLink to="/auth/register" class="px-4 py-2 bg-gradient-to-r from-blue-600 to-emerald-600 text-white text-sm font-semibold rounded-xl hover:shadow-lg hover:shadow-blue-500/25 transition-all duration-300">
              {{ t('nav.register') }}
            </RouterLink>
          </template>

          <!-- Mobile menu button -->
          <button @click="mobileOpen = !mobileOpen" class="md:hidden p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800">
            <span class="text-xl">{{ mobileOpen ? '✕' : '☰' }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Mobile Menu -->
    <Transition name="slide-down">
      <div v-if="mobileOpen" class="md:hidden border-t border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 px-4 py-4 space-y-3">
        <RouterLink @click="mobileOpen = false" to="/" class="block py-2 text-gray-700 dark:text-gray-300">{{ t('nav.home') }}</RouterLink>
        <RouterLink @click="mobileOpen = false" to="/plans" class="block py-2 text-gray-700 dark:text-gray-300">{{ t('nav.plans') }}</RouterLink>
        <template v-if="!auth.isAuthenticated">
          <RouterLink @click="mobileOpen = false" to="/auth/login" class="block py-2 text-gray-700 dark:text-gray-300">{{ t('nav.login') }}</RouterLink>
          <RouterLink @click="mobileOpen = false" to="/auth/register" class="block py-2 font-semibold text-blue-600">{{ t('nav.register') }}</RouterLink>
        </template>
      </div>
    </Transition>
  </nav>
</template>

<style scoped>
.slide-down-enter-active, .slide-down-leave-active { transition: all 0.2s ease; }
.slide-down-enter-from, .slide-down-leave-to { opacity: 0; transform: translateY(-8px); }
</style>
