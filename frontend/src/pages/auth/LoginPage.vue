<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const router = useRouter()
const auth = useAuthStore()

const email = ref('')
const password = ref('')

async function handleLogin() {
  try {
    const cleanEmail = email.value.trim()
    await auth.login({ email: cleanEmail, password: password.value })
    const redirect = router.currentRoute.value.query.redirect as string
    let target = '/student/dashboard'
    if (auth.isTeacher) target = '/teacher/dashboard'
    else if (auth.isSuperAdmin) target = '/admin/dashboard'
    else if (auth.isSchoolAdmin) target = '/school-admin/dashboard'
    router.push(redirect || target)
  } catch { /* error handled in store */ }
}
</script>

<template>
  <div>
    <h2 class="text-2xl font-bold text-white text-center mb-2">{{ t('auth.login_title') }}</h2>
    <p class="text-blue-200 text-sm text-center mb-8">{{ t('auth.login_subtitle') }}</p>

    <form @submit.prevent="handleLogin" class="space-y-4">
      <div>
        <label class="block text-sm font-medium text-blue-100 mb-1">{{ t('auth.email') }}</label>
        <input v-model="email" type="email" required
          class="w-full px-4 py-3 rounded-xl bg-white/10 border border-white/20 text-white placeholder-blue-300/50 focus:outline-none focus:ring-2 focus:ring-amber-400 focus:border-transparent transition-all"
          :placeholder="t('auth.email')">
      </div>
      <div>
        <label class="block text-sm font-medium text-blue-100 mb-1">{{ t('auth.password') }}</label>
        <input v-model="password" type="password" required
          class="w-full px-4 py-3 rounded-xl bg-white/10 border border-white/20 text-white placeholder-blue-300/50 focus:outline-none focus:ring-2 focus:ring-amber-400 focus:border-transparent transition-all"
          :placeholder="t('auth.password')">
      </div>

      <div class="text-right">
        <a href="#" class="text-xs text-amber-300 hover:underline">{{ t('auth.forgot_password') }}</a>
      </div>

      <div v-if="auth.error" class="p-3 rounded-xl bg-red-500/20 border border-red-400/30 text-red-200 text-sm">
        {{ auth.error }}
      </div>

      <button type="submit" :disabled="auth.loading"
        class="w-full py-3.5 bg-gradient-to-r from-amber-500 to-amber-600 text-white font-semibold rounded-xl hover:shadow-lg hover:shadow-amber-500/30 disabled:opacity-60 transition-all duration-300">
        <span v-if="auth.loading" class="inline-flex items-center gap-2">
          <svg class="animate-spin h-4 w-4" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
          {{ t('common.loading') }}
        </span>
        <span v-else>{{ t('auth.login_btn') }}</span>
      </button>
    </form>

    <!-- Divider -->
    <div class="flex items-center gap-3 my-6">
      <div class="flex-1 h-px bg-white/20"></div>
      <span class="text-sm text-blue-200">{{ t('auth.or') }}</span>
      <div class="flex-1 h-px bg-white/20"></div>
    </div>

    <!-- Google Login -->
    <button class="w-full py-3 bg-white/10 border border-white/20 text-white font-medium rounded-xl hover:bg-white/20 transition-all flex items-center justify-center gap-2">
      <svg class="w-5 h-5" viewBox="0 0 24 24"><path fill="#fff" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"/><path fill="#fff" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" opacity=".7"/><path fill="#fff" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" opacity=".5"/><path fill="#fff" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" opacity=".8"/></svg>
      {{ t('auth.google_login') }}
    </button>

    <p class="text-center text-sm text-blue-200 mt-6">
      {{ t('auth.no_account') }}
      <RouterLink to="/auth/register" class="text-amber-300 font-semibold hover:underline">{{ t('auth.register_btn') }}</RouterLink>
    </p>
  </div>
</template>
