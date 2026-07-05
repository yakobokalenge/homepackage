<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePaymentStore } from '@/stores/payment'
import { paymentService } from '@/services/payment.service'
import { useI18n } from 'vue-i18n'
import type { SubscriptionPlan } from '@/types'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const paymentStore = usePaymentStore()

const planId = route.params.planId as string
const selectedPlan = ref<SubscriptionPlan | null>(null)
const paymentMethod = ref('mpesa')
const phoneNumber = ref('')
const processing = ref(false)
const success = ref(false)
const error = ref('')

const methods = [
  { id: 'mpesa', label: t('payment.mpesa'), icon: '📱', color: 'border-red-400 bg-red-50 dark:bg-red-900/20' },
  { id: 'tigo_pesa', label: t('payment.tigo'), icon: '📱', color: 'border-blue-400 bg-blue-50 dark:bg-blue-900/20' },
  { id: 'airtel_money', label: t('payment.airtel'), icon: '📱', color: 'border-red-400 bg-red-50 dark:bg-red-900/20' },
  { id: 'halo_pesa', label: t('payment.halo'), icon: '📱', color: 'border-orange-400 bg-orange-50 dark:bg-orange-900/20' },
  { id: 'card', label: t('payment.card'), icon: '💳', color: 'border-purple-400 bg-purple-50 dark:bg-purple-900/20' },
]

const isMobileMoney = ref(true)

function selectMethod(id: string) {
  paymentMethod.value = id
  isMobileMoney.value = id !== 'card'
}

function formatTZS(amount: number) {
  return new Intl.NumberFormat('en-TZ', { style: 'currency', currency: 'TZS', minimumFractionDigits: 0 }).format(amount)
}

onMounted(async () => {
  try {
    const plansData = await paymentService.getPlans()
    selectedPlan.value = plansData.find(p => p.id === planId) || null
  } catch (err) {
    console.error('Failed to load plan details:', err)
  }
})

async function handlePayment() {
  if (isMobileMoney.value && !phoneNumber.value) {
    error.value = 'Please enter your phone number'
    return
  }
  processing.value = true
  error.value = ''
  try {
    const res = await paymentStore.initPayment({
      plan_id: planId,
      payment_method: paymentMethod.value as any,
      phone_number: phoneNumber.value ? `255${phoneNumber.value.replace(/^(\+255|255|0)/, '')}` : undefined,
    })
    
    if (res && (res as any).redirect_url) {
      window.location.href = (res as any).redirect_url
      return
    }
    success.value = true
  } catch (e: any) {
    error.value = e.response?.data?.error || e.message || t('payment.failed')
  } finally {
    processing.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-950 py-12">
    <div class="max-w-lg mx-auto px-4">
      <!-- Success State -->
      <div v-if="success" class="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-8 text-center shadow-sm">
        <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center text-3xl">✅</div>
        <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-2">{{ t('payment.success') }}</h2>
        <p class="text-gray-500 mb-6">Your subscription payment has been initiated. Please complete the push prompt on your mobile phone.</p>
        <button @click="router.push('/student/dashboard')" class="px-8 py-3 bg-gradient-to-r from-blue-600 to-emerald-600 text-white font-semibold rounded-xl">
          Go to Dashboard
        </button>
      </div>

      <!-- Checkout Form -->
      <div v-else class="space-y-6">
        <div class="text-center">
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Complete Payment</h1>
          <p class="text-gray-500 text-sm mt-1">
            Plan: <span class="font-semibold text-blue-600 dark:text-blue-400">{{ selectedPlan?.name || 'Loading...' }}</span>
            <span v-if="selectedPlan" class="ml-2 text-gray-700 dark:text-gray-300">({{ formatTZS(Number(selectedPlan.price_tzs)) }})</span>
          </p>
        </div>

        <!-- Payment Method Selection -->
        <div class="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-6 shadow-sm">
          <h3 class="font-semibold text-gray-900 dark:text-white mb-4">{{ t('payment.payment_method') }}</h3>
          <div class="grid grid-cols-2 sm:grid-cols-3 gap-3">
            <button v-for="method in methods" :key="method.id" @click="selectMethod(method.id)"
              :class="['p-3 rounded-xl border-2 text-center transition-all text-sm', paymentMethod === method.id ? method.color + ' border-current' : 'border-gray-200 dark:border-gray-700 hover:border-gray-300']">
              <span class="text-xl block mb-1">{{ method.icon }}</span>
              <span class="font-medium text-gray-700 dark:text-gray-300">{{ method.label }}</span>
            </button>
          </div>
        </div>

        <!-- Mobile Money Form -->
        <div v-if="isMobileMoney" class="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-6 shadow-sm">
          <h3 class="font-semibold text-gray-900 dark:text-white mb-4">{{ t('payment.phone_number') }}</h3>
          <div class="flex items-center gap-2">
            <span class="px-3 py-3 bg-gray-100 dark:bg-gray-800 rounded-xl text-sm font-medium text-gray-600">🇹🇿 +255</span>
            <input v-model="phoneNumber" type="tel" placeholder="7XX XXX XXX"
              class="flex-1 px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none" />
          </div>
          <p class="text-xs text-gray-500 mt-2">You will receive a prompt on your phone to confirm payment.</p>
        </div>

        <!-- Card Form (placeholder) -->
        <div v-else class="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-6 space-y-4 shadow-sm">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Card Number</label>
            <input type="text" placeholder="1234 5678 9012 3456" class="w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none" />
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Expiry</label>
              <input type="text" placeholder="MM/YY" class="w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">CVV</label>
              <input type="text" placeholder="123" class="w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none" />
            </div>
          </div>
        </div>

        <!-- Error -->
        <div v-if="error" class="p-3 rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 text-sm">{{ error }}</div>

        <!-- Pay Button -->
        <button @click="handlePayment" :disabled="processing"
          class="w-full py-4 bg-gradient-to-r from-blue-600 to-emerald-600 text-white font-bold rounded-xl hover:shadow-xl hover:shadow-blue-500/20 disabled:opacity-60 transition-all duration-300 text-lg">
          {{ processing ? t('payment.processing') : t('payment.pay_now') }}
        </button>

        <p class="text-xs text-center text-gray-500">🔒 Secure payment powered by Flutterwave. Your data is encrypted.</p>
      </div>
    </div>
  </div>
</template>
