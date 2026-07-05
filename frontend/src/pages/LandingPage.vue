<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'

const { t } = useI18n()

const features = [
  { icon: '📝', key: 'assessments' },
  { icon: '🔒', key: 'proctoring' },
  { icon: '📊', key: 'analytics' },
  { icon: '📱', key: 'mobile' },
]

const stats = [
  { value: '50,000+', key: 'students' },
  { value: '5,000+', key: 'teachers' },
  { value: '1,200+', key: 'schools' },
  { value: '31', key: 'regions' },
]
</script>

<template>
  <div>
    <!-- Hero Section -->
    <section class="relative overflow-hidden bg-gradient-to-br from-blue-950 via-blue-900 to-emerald-900 text-white">
      <div class="absolute inset-0">
        <div class="absolute top-20 left-10 w-72 h-72 bg-blue-500/20 rounded-full blur-3xl animate-pulse"></div>
        <div class="absolute bottom-20 right-10 w-96 h-96 bg-emerald-500/15 rounded-full blur-3xl animate-pulse" style="animation-delay: 2s"></div>
        <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-80 h-80 bg-amber-500/10 rounded-full blur-3xl animate-pulse" style="animation-delay: 4s"></div>
      </div>

      <div class="relative max-w-7xl mx-auto px-4 sm:px-6 py-20 md:py-32">
        <div class="max-w-3xl">
          <div class="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/10 backdrop-blur-sm border border-white/20 text-sm mb-6">
            <span>🇹🇿</span>
            <span>{{ t('app.tagline') }}</span>
          </div>
          <h1 class="text-4xl sm:text-5xl md:text-6xl font-bold leading-tight mb-6">
            {{ t('landing.hero_title') }}
            <span class="bg-gradient-to-r from-amber-400 to-emerald-400 bg-clip-text text-transparent">
              {{ t('landing.hero_title_highlight') }}
            </span>
          </h1>
          <p class="text-lg md:text-xl text-blue-100/80 leading-relaxed mb-10 max-w-2xl">
            {{ t('landing.hero_subtitle') }}
          </p>
          <div class="flex flex-wrap gap-4">
            <RouterLink to="/auth/register" class="px-8 py-3.5 bg-gradient-to-r from-amber-500 to-amber-600 text-white font-semibold rounded-xl hover:shadow-xl hover:shadow-amber-500/30 hover:-translate-y-0.5 transition-all duration-300">
              {{ t('landing.get_started') }}
            </RouterLink>
            <RouterLink to="/plans" class="px-8 py-3.5 bg-white/10 backdrop-blur-sm border border-white/20 text-white font-semibold rounded-xl hover:bg-white/20 transition-all duration-300">
              {{ t('landing.view_plans') }}
            </RouterLink>
          </div>
        </div>
      </div>
    </section>

    <!-- Stats Bar -->
    <section class="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        <div class="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div v-for="stat in stats" :key="stat.key" class="text-center">
            <p class="text-2xl md:text-3xl font-bold bg-gradient-to-r from-blue-600 to-emerald-600 bg-clip-text text-transparent">{{ stat.value }}</p>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">{{ t(`landing.stats_${stat.key}`) }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Features -->
    <section class="py-20 md:py-28 bg-gray-50 dark:bg-gray-950">
      <div class="max-w-7xl mx-auto px-4 sm:px-6">
        <div class="text-center mb-16">
          <h2 class="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-4">{{ t('landing.features_title') }}</h2>
          <p class="text-lg text-gray-500 dark:text-gray-400 max-w-2xl mx-auto">{{ t('landing.features_subtitle') }}</p>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div
            v-for="feature in features"
            :key="feature.key"
            class="group p-6 bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 hover:border-blue-300 dark:hover:border-blue-700 hover:shadow-xl hover:shadow-blue-500/5 hover:-translate-y-1 transition-all duration-300"
          >
            <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-emerald-500 flex items-center justify-center text-2xl mb-4 group-hover:scale-110 transition-transform">
              {{ feature.icon }}
            </div>
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">{{ t(`landing.feature_${feature.key}`) }}</h3>
            <p class="text-sm text-gray-500 dark:text-gray-400 leading-relaxed">{{ t(`landing.feature_${feature.key}_desc`) }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- CTA -->
    <section class="py-20 bg-gradient-to-r from-blue-600 to-emerald-600">
      <div class="max-w-4xl mx-auto px-4 text-center">
        <h2 class="text-3xl md:text-4xl font-bold text-white mb-6">Ready to transform learning?</h2>
        <p class="text-lg text-blue-100 mb-10">Join thousands of students and teachers across Tanzania.</p>
        <RouterLink to="/auth/register" class="inline-flex px-10 py-4 bg-white text-blue-700 font-bold rounded-xl hover:shadow-2xl hover:-translate-y-1 transition-all duration-300">
          {{ t('landing.get_started') }} →
        </RouterLink>
      </div>
    </section>
  </div>
</template>
