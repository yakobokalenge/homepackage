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
        { path: 'billing', name: 'student-billing', component: () => import('@/pages/billing/BillingPage.vue') },
        { path: 'assessments', name: 'student-assessments', component: () => import('@/pages/student/AssessmentsPage.vue') },
        { path: 'attempts/:id/result', name: 'student-attempt-result', component: () => import('@/pages/student/AssessmentResultPage.vue') },
      ]
    },
    {
      path: '/student/assessments/:id/take',
      component: () => import('@/layouts/ExamLayout.vue'),
      meta: { requiresAuth: true, role: 'student' },
      children: [
        { path: '', name: 'take-assessment', component: () => import('@/pages/student/TakeAssessmentPage.vue') }
      ]
    },
    {
      path: '/teacher',
      component: () => import('@/layouts/DashboardLayout.vue'),
      meta: { requiresAuth: true, role: 'teacher' },
      children: [
        { path: 'dashboard', name: 'teacher-dashboard', component: () => import('@/pages/teacher/DashboardPage.vue') },
        { path: 'billing', name: 'teacher-billing', component: () => import('@/pages/billing/BillingPage.vue') },
        { path: 'assessments', name: 'teacher-assessments', component: () => import('@/pages/teacher/AssessmentsPage.vue') },
        { path: 'assessments/create', name: 'teacher-assessment-create', component: () => import('@/pages/teacher/CreateAssessmentPage.vue') },
        { path: 'assessments/:id', name: 'teacher-assessment-detail', component: () => import('@/pages/teacher/AssessmentDetailPage.vue') },
        { path: 'attempts/:id/grade', name: 'teacher-grade-attempt', component: () => import('@/pages/teacher/GradeAttemptPage.vue') },
        { path: 'proctoring/:attemptId', name: 'teacher-review-proctoring', component: () => import('@/pages/teacher/ReviewProctoringPage.vue') },
        { path: 'question-bank', name: 'teacher-question-bank', component: () => import('@/pages/teacher/QuestionBankPage.vue') },
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
