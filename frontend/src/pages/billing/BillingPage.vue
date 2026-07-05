<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'
import { paymentService } from '@/services/payment.service'
import type { Subscription, Transaction } from '@/types'

const { t } = useI18n()
const loading = ref(true)
const currentSub = ref<Subscription | null>(null)
const paymentHistory = ref<Transaction[]>([])

function formatDate(dateStr: string) {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' })
}

function formatAmount(amount: any) {
  if (amount === undefined || amount === null) return '—'
  const numericAmount = typeof amount === 'string' ? parseFloat(amount) : amount
  return `TZS ${numericAmount.toLocaleString()}`
}

onMounted(async () => {
  try {
    const subData = await paymentService.getCurrentSubscription()
    currentSub.value = subData
    
    const historyData = await paymentService.getTransactionHistory()
    paymentHistory.value = historyData.transactions
  } catch (err) {
    console.error('Failed to load billing history:', err)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="space-y-6">
    <h1 class="text-2xl font-bold text-gray-900 dark:text-white">{{ t('nav.billing') }}</h1>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-20 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl">
      <span class="animate-spin inline-block w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mb-4"></span>
      <p class="text-gray-500 dark:text-gray-400">Loading Billing Data...</p>
    </div>

    <template v-else>
      <!-- Current Plan -->
      <div class="bg-gradient-to-r from-blue-600 to-emerald-600 rounded-2xl p-6 text-white shadow-sm">
        <div class="flex justify-between items-start">
          <div>
            <p class="text-blue-100 text-sm">{{ t('payment.current_plan') }}</p>
            <h2 class="text-2xl font-bold mt-1">
              {{ currentSub?.plan_detail?.name || currentSub?.plan?.name || 'No Active Plan' }}
            </h2>
            <p class="text-blue-100 text-sm mt-2" v-if="currentSub">
              Renews: {{ formatDate(currentSub.current_period_end) }} (Status: <span class="uppercase font-semibold">{{ currentSub.status }}</span>)
            </p>
            <p class="text-blue-100 text-sm mt-2" v-else>
              Upgrade today to unlock all learning and teaching resources!
            </p>
          </div>
          <RouterLink to="/plans" class="px-4 py-2 bg-white/20 backdrop-blur-sm rounded-xl text-sm font-medium hover:bg-white/30 transition-colors">
            {{ currentSub ? t('payment.upgrade') : 'Subscribe' }}
          </RouterLink>
        </div>
      </div>

      <!-- Payment History -->
      <div class="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 overflow-hidden shadow-sm">
        <div class="p-6 border-b border-gray-200 dark:border-gray-800">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white">{{ t('payment.history') }}</h2>
        </div>
        
        <div v-if="paymentHistory.length === 0" class="text-center py-12 text-gray-500">
          <span class="text-3xl block mb-2">💳</span>
          No payment history recorded yet.
        </div>
        
        <div v-else class="overflow-x-auto">
          <table class="w-full">
            <thead class="bg-gray-50 dark:bg-gray-800/50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Amount</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Method</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200 dark:divide-gray-800">
              <tr v-for="p in paymentHistory" :key="p.id" class="hover:bg-gray-50 dark:hover:bg-gray-800/30 transition-colors">
                <td class="px-6 py-4 text-sm text-gray-900 dark:text-white">{{ formatDate(p.created_at || p.completed_at || '') }}</td>
                <td class="px-6 py-4 text-sm font-semibold text-gray-900 dark:text-white">{{ formatAmount(p.amount) }}</td>
                <td class="px-6 py-4 text-sm text-gray-500 capitalize">{{ p.payment_method }}</td>
                <td class="px-6 py-4">
                  <span :class="['px-2.5 py-1 text-xs font-medium rounded-full uppercase', p.status === 'successful' ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400' : 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400']">
                    {{ p.status }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>
