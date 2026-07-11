import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  scrollBehavior: () => ({ top: 0 }),
  routes: [
    {
      path: '/',
      component: () => import('@/layouts/DefaultLayout.vue'),
      children: [
        { path: '', name: 'home', component: () => import('@/pages/LandingPage.vue') },
        { path: 'plans', name: 'plans', component: () => import('@/pages/plans/PlansPage.vue') },
      ]
    },
    {
      path: '/auth',
      component: () => import('@/layouts/AuthLayout.vue'),
      children: [
        { path: 'login', name: 'login', component: () => import('@/pages/auth/LoginPage.vue') },
        { path: 'register', name: 'register', component: () => import('@/pages/auth/RegisterPage.vue') },
      ]
    },
    {
      path: '/student',
      component: () => import('@/layouts/DashboardLayout.vue'),
      meta: { requiresAuth: true, role: 'student' },
      children: [
        { path: 'dashboard', name: 'student-dashboard', component: () => import('@/pages/student/DashboardPage.vue') },
        { path: 'assessments', name: 'student-assessments', component: () => import('@/pages/student/AssessmentsPage.vue') },
        { path: 'billing', name: 'student-billing', component: () => import('@/pages/billing/BillingPage.vue') },
      ]
    },
    {
      path: '/student/exam/:id',
      name: 'take-exam',
      component: () => import('@/pages/student/ExamPage.vue'),
      meta: { requiresAuth: true, role: 'student' }
    },
    {
      path: '/teacher',
      component: () => import('@/layouts/DashboardLayout.vue'),
      meta: { requiresAuth: true, role: 'teacher' },
      children: [
        { path: 'dashboard', name: 'teacher-dashboard', component: () => import('@/pages/teacher/DashboardPage.vue') },
        { path: 'assessments/create', name: 'create-assessment', component: () => import('@/pages/teacher/CreateAssessmentPage.vue') },
        { path: 'billing', name: 'teacher-billing', component: () => import('@/pages/billing/BillingPage.vue') },
      ]
    },
    {
      path: '/admin',
      component: () => import('@/layouts/DashboardLayout.vue'),
      meta: { requiresAuth: true, role: 'super_admin' },
      children: [
        { path: 'dashboard', name: 'admin-dashboard', component: () => import('@/pages/admin/DashboardPage.vue') },
      ]
    },
    {
      path: '/school-admin',
      component: () => import('@/layouts/DashboardLayout.vue'),
      meta: { requiresAuth: true, role: 'school_admin' },
      children: [
        { path: 'dashboard', name: 'school-admin-dashboard', component: () => import('@/pages/school_admin/DashboardPage.vue') },
      ]
    },
    {
      path: '/checkout/:planId',
      name: 'checkout',
      component: () => import('@/pages/billing/CheckoutPage.vue'),
      meta: { requiresAuth: true }
    },
    { path: '/:pathMatch(.*)*', name: 'not-found', component: () => import('@/pages/NotFoundPage.vue') }
  ]
})

router.beforeEach((to, _from, next) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.token) {
    next({ name: 'login', query: { redirect: to.fullPath } })
  } else if (to.meta.requiresAuth && to.meta.role) {
    const userRole = auth.user?.role
    const requiredRole = to.meta.role as string
    if (userRole === requiredRole || (userRole === 'super_admin' && requiredRole === 'school_admin') || (userRole === 'super_admin' && requiredRole === 'teacher')) {
      next()
    } else {
      next('/')
    }
  } else {
    next()
  }
})

export default router
