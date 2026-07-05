import api from './api'
import type {
  SubscriptionPlan,
  Subscription,
  Transaction,
  InitiatePaymentPayload,
  PaymentVerificationResponse
} from '@/types'

export const paymentService = {
  async getPlans(): Promise<SubscriptionPlan[]> {
    const { data } = await api.get<any>('/subscriptions/plans/')
    if (data && Array.isArray(data.results)) {
      return data.results
    }
    return Array.isArray(data) ? data : []
  },

  async getCurrentSubscription(): Promise<Subscription | null> {
    try {
      const { data } = await api.get<any>('/subscriptions/subscriptions/current/')
      if (data && data.status === 'no_subscription') {
        return null
      }
      return data
    } catch {
      return null
    }
  },

  async initiatePayment(payload: InitiatePaymentPayload): Promise<Transaction> {
    const { data } = await api.post<Transaction>('/payments/initiate/', payload)
    return data
  },

  async verifyPayment(transactionId: string): Promise<PaymentVerificationResponse> {
    const { data } = await api.get<PaymentVerificationResponse>(
      `/payments/verify/${transactionId}/`
    )
    return data
  },

  async getTransactionHistory(params?: {
    page?: number
    limit?: number
    status?: string
  }): Promise<{ transactions: Transaction[]; total: number }> {
    try {
      const { data } = await api.get<any>('/payments/history/', { params })
      let rawList = []
      if (data && Array.isArray(data.results)) {
        rawList = data.results
      } else if (Array.isArray(data)) {
        rawList = data
      }
      return {
        transactions: rawList,
        total: data.count || rawList.length
      }
    } catch {
      return { transactions: [], total: 0 }
    }
  },

  async cancelSubscription(subscriptionId: string): Promise<void> {
    await api.post(`/subscriptions/subscriptions/${subscriptionId}/cancel/`)
  }
}
