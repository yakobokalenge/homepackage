export type PaymentMethod = 'mpesa' | 'tigo_pesa' | 'airtel_money' | 'halo_pesa' | 'visa' | 'mastercard' | 'card'
export type PlanTier = 'basic' | 'premium' | 'institutional'
export type SubscriptionStatus = 'active' | 'expired' | 'cancelled' | 'pending' | 'trial'
export type TransactionStatus = 'pending' | 'processing' | 'successful' | 'failed' | 'refunded'

export interface SubscriptionPlan {
  id: string
  name: string
  tier: PlanTier
  description: string
  price_monthly: number
  price_yearly: number
  price_tzs: string | number
  billing_cycle: 'weekly' | 'monthly' | 'yearly'
  currency: string
  features: PlanFeature[] | string[]
  max_students?: number
  max_assessments?: number
  proctoring_enabled: boolean
  analytics_enabled: boolean
  is_popular?: boolean
}

export interface PlanFeature {
  text: string
  included: boolean
}

export interface Subscription {
  id: string
  user_id: string
  plan_id: string
  plan: SubscriptionPlan
  plan_name?: string
  plan_detail?: SubscriptionPlan
  status: SubscriptionStatus
  payment_method: PaymentMethod
  current_period_start: string
  current_period_end: string
  cancelled_at?: string
  created_at: string
}

export interface Transaction {
  id: string
  user_id: string
  subscription_id?: string
  amount: number
  currency: string
  payment_method: PaymentMethod
  status: TransactionStatus
  reference: string
  phone_number?: string
  description: string
  created_at: string
  completed_at?: string
  metadata?: Record<string, unknown>
}

export interface InitiatePaymentPayload {
  plan_id: string
  payment_method: PaymentMethod
  billing_cycle?: 'weekly' | 'monthly' | 'yearly'
  phone_number?: string
  card_token?: string
}

export interface PaymentVerificationResponse {
  status: TransactionStatus
  transaction: Transaction
  subscription?: Subscription
}

export interface MobileMoneyNetwork {
  id: PaymentMethod
  name: string
  prefix: string[]
  logo: string
  color: string
}
