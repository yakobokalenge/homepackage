<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { paymentService } from '@/services/payment.service'
import type { SubscriptionPlan } from '@/types'

const { t } = useI18n()
const billingCycle = ref<'weekly' | 'monthly' | 'yearly'>('monthly')
const loading = ref(true)
const dbPlans = ref<SubscriptionPlan[]>([])

function formatTZS(amount: number) {
  return new Intl.NumberFormat('en-TZ', { style: 'currency', currency: 'TZS', minimumFractionDigits: 0 }).format(amount)
}

const cycleSuffix = computed(() => {
  return { weekly: t('payment.per_week'), monthly: t('payment.per_month'), yearly: t('payment.per_year') }[billingCycle.value]
})

onMounted(async () => {
  try {
    const plansData = await paymentService.getPlans()
    dbPlans.value = plansData
  } catch (err) {
    console.error('Failed to load pricing plans:', err)
  } finally {
    loading.value = false
  }
})

// Filter and group plans by billing cycle
const activePlans = computed(() => {
  const list = dbPlans.value.filter(p => p.billing_cycle === billingCycle.value)
  
  // Format them for template display
  const icons: Record<string, string> = { basic: '📗', premium: '📘', institutional: '🏫' }
  return list.map(p => ({
    id: p.id,
    tier: p.tier,
    name: p.name,
    icon: icons[p.tier] || '📝',
    price: Number(p.price_tzs),
    features: Array.isArray(p.features) ? p.features : [],
    popular: p.tier === 'premium'
  }))
})
</script>

<template>
  <div class="py-16 md:py-24">
    <div class="max-w-7xl mx-auto px-4">
      <!-- Header -->
      <div class="text-center mb-12">
        <h1 class="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-4">{{ t('payment.choose_plan') }}</h1>
        <p class="text-gray-500 dark:text-gray-400 max-w-xl mx-auto">Choose a plan that fits your learning needs. All plans include TZS pricing with M-Pesa, Tigo Pesa, and Airtel Money support.</p>

        <!-- Billing Toggle -->
        <div class="inline-flex mt-8 bg-gray-100 dark:bg-gray-800 rounded-xl p-1">
          <button v-for="cycle in ['weekly', 'monthly', 'yearly'] as const" :key="cycle" @click="billingCycle = cycle"
            :class="['px-5 py-2 text-sm font-medium rounded-lg transition-all', billingCycle === cycle ? 'bg-white dark:bg-gray-700 text-blue-600 dark:text-blue-400 shadow-sm' : 'text-gray-500 hover:text-gray-700']">
            {{ t(`payment.${cycle}`) }}
            <span v-if="cycle === 'yearly'" class="ml-1 text-xs text-emerald-600">-17%</span>
          </button>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="text-center py-20 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl max-w-5xl mx-auto">
        <span class="animate-spin inline-block w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mb-4"></span>
        <p class="text-gray-500">Loading Pricing Plans...</p>
      </div>

      <!-- Empty State -->
      <div v-else-if="activePlans.length === 0" class="text-center py-20 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl max-w-5xl mx-auto">
        <span class="text-4xl block mb-3">🏷️</span>
        <p class="text-gray-500 font-medium">No plans available for this billing cycle.</p>
      </div>

      <!-- Plans Grid -->
      <div v-else class="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
        <div v-for="plan in activePlans" :key="plan.id"
          :class="['relative rounded-2xl border p-6 transition-all duration-300 hover:-translate-y-1 shadow-sm',
            plan.popular
              ? 'bg-gradient-to-b from-blue-50 to-white dark:from-blue-950/50 dark:to-gray-900 border-blue-300 dark:border-blue-700 shadow-xl shadow-blue-500/10'
              : 'bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-800 hover:shadow-lg']">

          <!-- Popular Badge -->
          <div v-if="plan.popular" class="absolute -top-3 left-1/2 -translate-x-1/2">
            <span class="px-4 py-1 bg-gradient-to-r from-blue-600 to-emerald-600 text-white text-xs font-bold rounded-full">Most Popular</span>
          </div>

          <div class="text-center mb-6">
            <span class="text-3xl">{{ plan.icon }}</span>
            <h3 class="text-xl font-bold text-gray-900 dark:text-white mt-2">{{ plan.name }}</h3>
            <div class="mt-4">
              <span class="text-3xl font-bold text-gray-900 dark:text-white">{{ formatTZS(plan.price) }}</span>
              <span class="text-gray-500 text-sm">{{ cycleSuffix }}</span>
            </div>
          </div>

          <!-- Features -->
          <ul class="space-y-3 mb-8">
            <li v-for="(feature, idx) in plan.features" :key="typeof feature === 'string' ? feature : (feature.text || idx)" class="flex items-start gap-2 text-sm">
              <span class="text-emerald-500 mt-0.5">✓</span>
              <span class="text-gray-700 dark:text-gray-300">
                {{ typeof feature === 'string' ? feature : feature.text }}
              </span>
            </li>
          </ul>

          <RouterLink :to="`/checkout/${plan.id}?cycle=${billingCycle}`"
            :class="['block w-full py-3 text-center font-semibold rounded-xl transition-all duration-300',
              plan.popular
                ? 'bg-gradient-to-r from-blue-600 to-emerald-600 text-white hover:shadow-lg hover:shadow-blue-500/25'
                : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700']">
            Get Started
          </RouterLink>
        </div>
      </div>
    </div>
  </div>
</template>
