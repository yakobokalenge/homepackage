import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  SubscriptionPlan,
  Subscription,
  Transaction,
  InitiatePaymentPayload,
  PaymentMethod
} from '@/types'
import { paymentService } from '@/services/payment.service'

export const usePaymentStore = defineStore('payment', () => {
  const plans = ref<SubscriptionPlan[]>([])
  const currentSubscription = ref<Subscription | null>(null)
  const transactions = ref<Transaction[]>([])
  const pendingTransaction = ref<Transaction | null>(null)
  const loading = ref(false)
  const processing = ref(false)
  const error = ref<string | null>(null)
  const pollingInterval = ref<ReturnType<typeof setInterval> | null>(null)

  const hasActiveSubscription = computed(
    () => currentSubscription.value?.status === 'active'
  )
  const currentPlan = computed(() => currentSubscription.value?.plan || null)
  const isPremium = computed(
    () => currentPlan.value?.tier === 'premium' || currentPlan.value?.tier === 'institutional'
  )

  async function fetchPlans() {
    loading.value = true
    try {
      plans.value = await paymentService.getPlans()
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to fetch plans'
    } finally {
      loading.value = false
    }
  }

  async function fetchSubscription() {
    try {
      currentSubscription.value = await paymentService.getCurrentSubscription()
    } catch {
      currentSubscription.value = null
    }
  }

  async function initPayment(payload: InitiatePaymentPayload) {
    processing.value = true
    error.value = null
    try {
      pendingTransaction.value = await paymentService.initiatePayment(payload)
      startPolling(pendingTransaction.value.id)
      return pendingTransaction.value
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Payment initiation failed'
      throw err
    } finally {
      processing.value = false
    }
  }

  async function verifyPayment(transactionId: string) {
    try {
      const result = await paymentService.verifyPayment(transactionId)
      if (result.status === 'successful') {
        stopPolling()
        currentSubscription.value = result.subscription || null
        pendingTransaction.value = null
      }
      return result
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Payment verification failed'
      throw err
    }
  }

  function startPolling(transactionId: string) {
    stopPolling()
    pollingInterval.value = setInterval(async () => {
      try {
        const result = await paymentService.verifyPayment(transactionId)
        if (result.status === 'successful' || result.status === 'failed') {
          stopPolling()
          if (result.status === 'successful') {
            currentSubscription.value = result.subscription || null
          }
          pendingTransaction.value = result.transaction
        }
      } catch {
        // Keep polling
      }
    }, 5000)
  }

  function stopPolling() {
    if (pollingInterval.value) {
      clearInterval(pollingInterval.value)
      pollingInterval.value = null
    }
  }

  async function fetchTransactions(page = 1) {
    loading.value = true
    try {
      const result = await paymentService.getTransactionHistory({ page, limit: 20 })
      transactions.value = result.transactions
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to fetch transactions'
    } finally {
      loading.value = false
    }
  }

  async function cancelSubscription() {
    if (!currentSubscription.value) return
    processing.value = true
    try {
      await paymentService.cancelSubscription(currentSubscription.value.id)
      currentSubscription.value.status = 'cancelled'
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to cancel subscription'
      throw err
    } finally {
      processing.value = false
    }
  }

  function formatTZS(amount: number): string {
    return new Intl.NumberFormat('en-TZ', {
      style: 'currency',
      currency: 'TZS',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount)
  }

  function detectNetwork(phone: string): PaymentMethod | null {
    const cleaned = phone.replace(/\D/g, '')
    if (/^(255|0)?(65|67|68|69)/.test(cleaned)) return 'mpesa'
    if (/^(255|0)?(71|65|67)/.test(cleaned)) return 'tigo_pesa'
    if (/^(255|0)?(78|68)/.test(cleaned)) return 'airtel_money'
    return null
  }

  return {
    plans,
    currentSubscription,
    transactions,
    pendingTransaction,
    loading,
    processing,
    error,
    hasActiveSubscription,
    currentPlan,
    isPremium,
    fetchPlans,
    fetchSubscription,
    initPayment,
    verifyPayment,
    fetchTransactions,
    cancelSubscription,
    stopPolling,
    formatTZS,
    detectNetwork
  }
})
