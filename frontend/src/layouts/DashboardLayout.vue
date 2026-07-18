<script setup lang="ts">
import { ref, computed } from 'vue'
import { RouterView, RouterLink, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useI18n } from 'vue-i18n'
import NotificationBell from '@/components/nav/NotificationBell.vue'
import LanguageSwitcher from '@/components/common/LanguageSwitcher.vue'

const { t } = useI18n()
const auth = useAuthStore()
const route = useRoute()
const sidebarOpen = ref(true)

const menuItems = computed(() => {
  if (auth.isSuperAdmin) {
    return [
      { icon: '📊', label: 'Admin Dashboard', to: '/admin/dashboard' },
      { icon: '⚙️', label: 'Settings', to: '#' },
    ]
  }
  if (auth.isSchoolAdmin) {
    return [
      { icon: '📊', label: 'School Dashboard', to: '/school-admin/dashboard' },
      { icon: '⚙️', label: 'Settings', to: '#' },
    ]
  }
  if (auth.isTeacher) {
    return [
      { icon: '📊', label: t('nav.dashboard'), to: '/teacher/dashboard' },
      { icon: '📋', label: 'Assessments', to: '/teacher/assessments' },
      { icon: '🗂️', label: 'Question Bank', to: '/teacher/question-bank' },
      { icon: '💳', label: t('nav.billing'), to: '/teacher/billing' },
      { icon: '⚙️', label: t('nav.settings'), to: '#' },
    ]
  }
  return [
    { icon: '📊', label: t('nav.dashboard'), to: '/student/dashboard' },
    { icon: '📋', label: 'Assessments', to: '/student/assessments' },
    { icon: '💳', label: t('nav.billing'), to: '/student/billing' },
    { icon: '⚙️', label: t('nav.settings'), to: '#' },
  ]
})
</script>

<template>
  <div class="min-h-screen flex bg-gray-50 dark:bg-gray-950">
    <!-- Sidebar -->
    <aside
      :class="[sidebarOpen ? 'w-64' : 'w-20', 'hidden md:flex flex-col bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 transition-all duration-300']"
    >
      <div class="p-4 border-b border-gray-200 dark:border-gray-800">
        <RouterLink to="/" class="flex items-center gap-2 text-lg font-bold text-blue-700 dark:text-blue-400">
          <span class="text-2xl">📚</span>
          <span v-if="sidebarOpen">HomePackage</span>
        </RouterLink>
      </div>
      <nav class="flex-1 p-3 space-y-1">
        <RouterLink
          v-for="item in menuItems"
          :key="item.to"
          :to="item.to"
          :class="[
            'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200',
            route.path === item.to || route.path.startsWith(item.to + '/')
              ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400'
              : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
          ]"
        >
          <span class="text-lg">{{ item.icon }}</span>
          <span v-if="sidebarOpen">{{ item.label }}</span>
        </RouterLink>
      </nav>
      <div class="p-3 border-t border-gray-200 dark:border-gray-800">
        <button
          @click="sidebarOpen = !sidebarOpen"
          class="w-full flex items-center justify-center p-2 rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
        >
          <span v-if="sidebarOpen">◀ Collapse</span>
          <span v-else>▶</span>
        </button>
      </div>
    </aside>

    <!-- Main Content -->
    <div class="flex-1 flex flex-col min-w-0">
      <!-- Top Bar -->
      <header class="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 px-4 md:px-6 py-3 flex items-center justify-between sticky top-0 z-30">
        <button @click="sidebarOpen = !sidebarOpen" class="md:hidden p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800">
          <span class="text-xl">☰</span>
        </button>
        <div class="flex-1"></div>
        <div class="flex items-center gap-3">
          <LanguageSwitcher />
          <NotificationBell />
          <div class="flex items-center gap-2">
            <div class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-emerald-500 flex items-center justify-center text-white text-sm font-bold">
              {{ auth.initials }}
            </div>
            <div class="hidden sm:block">
              <p class="text-sm font-medium text-gray-900 dark:text-gray-100">{{ auth.fullName }}</p>
              <p class="text-xs text-gray-500 capitalize">{{ auth.user?.role }}</p>
            </div>
          </div>
          <button @click="auth.logout(); $router.push('/')" class="p-2 text-gray-500 hover:text-red-500 transition-colors" :title="t('nav.logout')">
            🚪
          </button>
        </div>
      </header>

      <main class="flex-1 p-4 md:p-6 overflow-auto">
        <RouterView />
      </main>
    </div>
  </div>
</template>
