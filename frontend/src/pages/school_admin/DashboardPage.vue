<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import api from '@/services/api'

const loading = ref(true)
const activeTab = ref<'roles' | 'teachers' | 'classrooms' | 'students' | 'subscriptions'>('roles')
const users = ref<any[]>([])
const classrooms = ref<any[]>([])

const stats = ref({
  total_teachers: 0,
  pending_approvals: 0,
  total_classrooms: 0,
  total_students: 0
})

const selectedUsers = ref<string[]>([])
const paymentMethod = ref('mpesa')
const showBulkPayModal = ref(false)

const teachersList = computed(() => {
  return users.value.filter(u => u.role === 'teacher')
})

const studentsList = computed(() => {
  return users.value.filter(u => u.role === 'student')
})

const userSubscriptionsList = computed(() => {
  return users.value.map((u: any) => ({
    id: u.id,
    name: u.full_name,
    role: u.role,
    email: u.email,
    plan: u.role === 'teacher' ? 'Teacher Premium (Monthly)' : 'Student Basic (Weekly)',
    price: u.role === 'teacher' ? 10000 : 2500,
    status: u.is_verified ? 'Active' : 'Expired'
  }))
})

const selectedTotal = computed(() => {
  return selectedUsers.value.reduce((sum, id) => {
    const usr = userSubscriptionsList.value.find(u => u.id === id)
    return sum + (usr ? usr.price : 0)
  }, 0)
})

function toggleSelectUser(userId: string) {
  const idx = selectedUsers.value.indexOf(userId)
  if (idx > -1) {
    selectedUsers.value.splice(idx, 1)
  } else {
    selectedUsers.value.push(userId)
  }
}

async function triggerBulkPayment() {
  if (selectedUsers.value.length === 0) return
  alert(`Successfully initiated multiple payment of TZS ${selectedTotal.value.toLocaleString()} for ${selectedUsers.value.length} users via ${paymentMethod.value.toUpperCase()}.`)
  showBulkPayModal.value = false
  selectedUsers.value = []
}

const pendingTeachers = computed(() => {
  return teachersList.value.filter(t => !t.is_verified)
})

async function loadData() {
  loading.value = true
  try {
    // 1. Fetch Users
    const usersRes = await api.get('/accounts/users/')
    users.value = Array.isArray(usersRes.data) ? usersRes.data : usersRes.data?.results || []

    // 2. Fetch Classrooms
    const classroomsRes = await api.get('/schools/classrooms/')
    const rawClassrooms = Array.isArray(classroomsRes.data) ? classroomsRes.data : classroomsRes.data?.results || []
    const seenCls = new Set()
    classrooms.value = rawClassrooms.filter((item: any) => {
      const key = `${item.name}-${item.stream}`
      if (seenCls.has(key)) return false
      seenCls.add(key)
      return true
    })

    // Compute stats
    stats.value = {
      total_teachers: teachersList.value.length,
      pending_approvals: pendingTeachers.value.length,
      total_classrooms: classrooms.value.length,
      total_students: studentsList.value.length
    }
  } catch (err) {
    console.error('Failed to load school admin dashboard details:', err)
  } finally {
    loading.value = false
  }
}

async function approveTeacher(teacherId: string) {
  try {
    await api.post(`/accounts/users/${teacherId}/verify/`)
    // Update local state
    const teacher = users.value.find(u => u.id === teacherId)
    if (teacher) {
      teacher.is_verified = true
    }
    stats.value.pending_approvals = pendingTeachers.value.length
  } catch (err) {
    alert('Failed to approve teacher.')
  }
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="bg-gradient-to-r from-blue-900 to-emerald-900 rounded-2xl p-6 text-white border border-emerald-500/20 shadow-xl">
      <h1 class="text-2xl font-bold mb-1">School Administrator Dashboard 🏫</h1>
      <p class="text-emerald-200 text-sm">Manage institutional roster, approve teacher sign-ups, and review classroom streams.</p>
    </div>

    <!-- Quick Stats Roster -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-5 shadow-sm">
        <span class="text-xs font-semibold text-gray-500 block mb-1">Total Teachers</span>
        <span class="text-2xl font-bold text-gray-900 dark:text-white">{{ stats.total_teachers }}</span>
      </div>
      <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-5 shadow-sm">
        <span class="text-xs font-semibold text-gray-500 block mb-1">Pending Approvals</span>
        <span class="text-2xl font-bold" :class="stats.pending_approvals > 0 ? 'text-amber-500' : 'text-gray-900 dark:text-white'">
          {{ stats.pending_approvals }}
        </span>
      </div>
      <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-5 shadow-sm">
        <span class="text-xs font-semibold text-gray-500 block mb-1">Classroom Streams</span>
        <span class="text-2xl font-bold text-gray-900 dark:text-white">{{ stats.total_classrooms }}</span>
      </div>
      <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-5 shadow-sm">
        <span class="text-xs font-semibold text-gray-500 block mb-1">Enrolled Students</span>
        <span class="text-2xl font-bold text-gray-900 dark:text-white">{{ stats.total_students }}</span>
      </div>
    </div>

    <!-- Navigation Tabs -->
    <div class="flex flex-wrap gap-2 border-b border-gray-200 dark:border-gray-800 pb-3">
      <button v-for="t in ['roles', 'teachers', 'classrooms', 'students', 'subscriptions'] as const" :key="t"
        @click="activeTab = t"
        :class="['px-5 py-2.5 rounded-xl text-sm font-semibold transition-all capitalize', activeTab === t ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-600/20' : 'text-gray-500 hover:text-gray-700 dark:text-gray-400']">
        {{ t === 'roles' ? 'Admins Roles & Responsibilities' : t === 'teachers' ? 'Teacher Approvals' : t === 'subscriptions' ? 'Subscription Billing' : t }}
      </button>
    </div>

    <!-- Tab Contents -->
    <div v-if="loading" class="text-center py-20 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl">
      <span class="animate-spin inline-block w-8 h-8 border-4 border-emerald-500 border-t-transparent rounded-full mb-4"></span>
      <p class="text-gray-500">Loading School Admin Dashboard...</p>
    </div>

    <template v-else>
      <!-- 1. ROLES & RESPONSIBILITIES TAB -->
      <div v-if="activeTab === 'roles'" class="grid gap-6 md:grid-cols-2">
        <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm space-y-4">
          <div class="flex items-center gap-3">
            <span class="text-2xl">🔑</span>
            <h3 class="text-lg font-bold text-gray-900 dark:text-white">Teacher Registration Approvals</h3>
          </div>
          <p class="text-sm text-gray-500 leading-relaxed">
            Verify and activate teachers registered to your school. Unapproved teachers cannot build courses, register exam sheets, or grade student works.
          </p>
          <div class="bg-gray-50 dark:bg-gray-800/40 p-4 rounded-xl text-xs space-y-2 text-gray-600 dark:text-gray-400">
            <span class="font-bold uppercase tracking-wider block text-emerald-600 dark:text-emerald-400">Active Tasks</span>
            <p>· Review teacher certificate registrations.</p>
            <p>· Approve pending verification requests.</p>
          </div>
        </div>

        <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm space-y-4">
          <div class="flex items-center gap-3">
            <span class="text-2xl">🏫</span>
            <h3 class="text-lg font-bold text-gray-900 dark:text-white">Classroom Stream Oversight</h3>
          </div>
          <p class="text-sm text-gray-500 leading-relaxed">
            Configure classrooms, sections, and grade levels. Appoint specific teachers to manage individual classrooms as designated "Class Teachers."
          </p>
          <div class="bg-gray-50 dark:bg-gray-800/40 p-4 rounded-xl text-xs space-y-2 text-gray-600 dark:text-gray-400">
            <span class="font-bold uppercase tracking-wider block text-emerald-600 dark:text-emerald-400">Active Tasks</span>
            <p>· Assign teachers to grade classrooms.</p>
            <p>· Adjust student seat limitations.</p>
          </div>
        </div>

        <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm space-y-4">
          <div class="flex items-center gap-3">
            <span class="text-2xl">👥</span>
            <h3 class="text-lg font-bold text-gray-900 dark:text-white">Student Enrollment Directory</h3>
          </div>
          <p class="text-sm text-gray-500 leading-relaxed">
            Monitor student listings and enrollment status. Allocate newly registered students to their corresponding classroom grade levels and streams.
          </p>
          <div class="bg-gray-50 dark:bg-gray-800/40 p-4 rounded-xl text-xs space-y-2 text-gray-600 dark:text-gray-400">
            <span class="font-bold uppercase tracking-wider block text-emerald-600 dark:text-emerald-400">Active Tasks</span>
            <p>· View active student profiles.</p>
            <p>· Track classroom lists.</p>
          </div>
        </div>

        <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm space-y-4">
          <div class="flex items-center gap-3">
            <span class="text-2xl">📊</span>
            <h3 class="text-lg font-bold text-gray-900 dark:text-white">Institutional Performance</h3>
          </div>
          <p class="text-sm text-gray-500 leading-relaxed">
            Oversee grade averages and analytics reports across subjects. Pinpoint academic challenges to refine teacher lessons and curriculum focus.
          </p>
          <div class="bg-gray-50 dark:bg-gray-800/40 p-4 rounded-xl text-xs space-y-2 text-gray-600 dark:text-gray-400">
            <span class="font-bold uppercase tracking-wider block text-emerald-600 dark:text-emerald-400">Active Tasks</span>
            <p>· Review class grade distributions.</p>
            <p>· Check subject average stats.</p>
          </div>
        </div>
      </div>

      <!-- 2. TEACHERS TAB -->
      <div v-else-if="activeTab === 'teachers'" class="space-y-6">
        <h3 class="text-xl font-bold text-gray-900 dark:text-white">Verify Teacher Profiles</h3>
        
        <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl overflow-hidden shadow-sm">
          <table class="w-full text-left text-sm">
            <thead class="bg-gray-50 dark:bg-gray-800/50 text-gray-500 font-semibold">
              <tr>
                <th class="px-6 py-3">Teacher Name</th>
                <th class="px-6 py-3">Email</th>
                <th class="px-6 py-3">Phone</th>
                <th class="px-6 py-3">Verification Status</th>
                <th class="px-6 py-3">Actions</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200 dark:divide-gray-800 text-gray-900 dark:text-gray-100">
              <tr v-for="t in teachersList" :key="t.id" class="hover:bg-gray-50 dark:hover:bg-gray-800/30">
                <td class="px-6 py-4 font-medium">{{ t.full_name }}</td>
                <td class="px-6 py-4 text-gray-500">{{ t.email }}</td>
                <td class="px-6 py-4 text-gray-500">{{ t.phone || 'N/A' }}</td>
                <td class="px-6 py-4">
                  <span :class="['px-2.5 py-1 text-xs font-semibold rounded-full uppercase', t.is_verified ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/20' : 'bg-amber-100 text-amber-700 dark:bg-amber-950/20']">
                    {{ t.is_verified ? 'Verified' : 'Pending Approval' }}
                  </span>
                </td>
                <td class="px-6 py-4">
                  <button v-if="!t.is_verified" @click="approveTeacher(t.id)" class="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-lg transition-colors">
                    Approve
                  </button>
                  <span v-else class="text-xs text-gray-400 font-medium">Approved</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 3. CLASSROOMS TAB -->
      <div v-else-if="activeTab === 'classrooms'" class="space-y-6">
        <h3 class="text-xl font-bold text-gray-900 dark:text-white">Active Classroom Streams</h3>
        <div class="grid gap-4 md:grid-cols-3">
          <div v-for="c in classrooms" :key="c.id" class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm space-y-4">
            <div class="flex justify-between items-start">
              <h4 class="font-bold text-lg text-gray-900 dark:text-white">{{ c.name }}</h4>
              <span class="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs font-bold rounded-full">Stream: {{ c.stream }}</span>
            </div>
            <div class="text-sm text-gray-500 space-y-1">
              <p>Academic Year: <span class="font-semibold text-gray-950 dark:text-white">{{ c.academic_year }}</span></p>
              <p>Max Students capacity: <span class="font-semibold text-gray-950 dark:text-white">{{ c.max_students }} seats</span></p>
            </div>
          </div>
        </div>
      </div>

      <!-- 4. STUDENTS TAB -->
      <div v-else-if="activeTab === 'students'" class="space-y-6">
        <h3 class="text-xl font-bold text-gray-900 dark:text-white">Enrolled Students</h3>
        <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl overflow-hidden shadow-sm">
          <table class="w-full text-left text-sm">
            <thead class="bg-gray-50 dark:bg-gray-800/50 text-gray-500 font-semibold">
              <tr>
                <th class="px-6 py-3">Student Name</th>
                <th class="px-6 py-3">Email</th>
                <th class="px-6 py-3">Phone</th>
                <th class="px-6 py-3">Date Joined</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200 dark:divide-gray-800 text-gray-900 dark:text-gray-100">
              <tr v-for="s in studentsList" :key="s.id" class="hover:bg-gray-50 dark:hover:bg-gray-800/30">
                <td class="px-6 py-4 font-medium">{{ s.full_name }}</td>
                <td class="px-6 py-4 text-gray-500">{{ s.email }}</td>
                <td class="px-6 py-4 text-gray-500">{{ s.phone || 'N/A' }}</td>
                <td class="px-6 py-4 text-gray-500">{{ new Date(s.date_joined).toLocaleDateString() }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 5. SUBSCRIPTIONS MONITORING & BULK BILLING TAB -->
      <div v-else-if="activeTab === 'subscriptions'" class="space-y-6">
        <div class="flex justify-between items-center">
          <div>
            <h3 class="text-xl font-bold text-gray-900 dark:text-white">Institutional Billing & Subscriptions</h3>
            <p class="text-xs text-gray-500 mt-1">Audit status or pay packages for students and teachers collectively.</p>
          </div>
          <button @click="showBulkPayModal = true" :disabled="selectedUsers.length === 0" class="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white text-sm font-semibold rounded-xl flex items-center gap-2 shadow-lg transition-all">
            💳 Pay for Selected ({{ selectedUsers.length }} users)
          </button>
        </div>

        <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl overflow-hidden shadow-sm">
          <table class="w-full text-left text-sm">
            <thead class="bg-gray-50 dark:bg-gray-800/50 text-gray-500 font-semibold border-b border-gray-200 dark:border-gray-800">
              <tr>
                <th class="px-6 py-3 w-10">
                  <input type="checkbox" :checked="selectedUsers.length === userSubscriptionsList.length && userSubscriptionsList.length > 0"
                    @change="selectedUsers = selectedUsers.length === userSubscriptionsList.length ? [] : userSubscriptionsList.map(u => u.id)"
                    class="rounded border-gray-300 dark:border-gray-700" />
                </th>
                <th class="px-6 py-3">User Name</th>
                <th class="px-6 py-3">Role</th>
                <th class="px-6 py-3">Email</th>
                <th class="px-6 py-3">Assigned Plan</th>
                <th class="px-6 py-3">Price</th>
                <th class="px-6 py-3">Status</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200 dark:divide-gray-800 text-gray-900 dark:text-gray-100">
              <tr v-for="u in userSubscriptionsList" :key="u.id" class="hover:bg-gray-50 dark:hover:bg-gray-850">
                <td class="px-6 py-4">
                  <input type="checkbox" :checked="selectedUsers.includes(u.id)" @change="toggleSelectUser(u.id)"
                    class="rounded border-gray-300 dark:border-gray-700" />
                </td>
                <td class="px-6 py-4 font-medium">{{ u.name }}</td>
                <td class="px-6 py-4 capitalize text-xs text-gray-500">{{ u.role }}</td>
                <td class="px-6 py-4 text-gray-500">{{ u.email }}</td>
                <td class="px-6 py-4 font-medium">{{ u.plan }}</td>
                <td class="px-6 py-4 font-bold text-indigo-650">TZS {{ u.price.toLocaleString() }}</td>
                <td class="px-6 py-4">
                  <span :class="['px-2 py-0.5 text-xs font-bold rounded-full uppercase', u.status === 'Active' ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-400' : 'bg-red-100 text-red-700 dark:bg-red-950/30 dark:text-red-400']">
                    {{ u.status }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Bulk Payment Modal Dialog -->
        <div v-if="showBulkPayModal" class="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div class="bg-white dark:bg-gray-900 border border-gray-205 dark:border-gray-800 rounded-2xl w-full max-w-md p-6 space-y-5 shadow-2xl relative">
            <button @click="showBulkPayModal = false" class="absolute top-4 right-4 text-gray-400 hover:text-gray-600">✕</button>
            
            <div>
              <h3 class="text-lg font-bold text-gray-900 dark:text-white">Checkout Preview</h3>
              <p class="text-xs text-gray-500 mt-1">Submit bulk subscription package payment for your school roster.</p>
            </div>

            <div class="p-4 bg-gray-50 dark:bg-gray-800/40 border rounded-xl flex justify-between items-center text-sm font-semibold">
              <span class="text-gray-500">Selected Accounts:</span>
              <span class="text-gray-900 dark:text-white">{{ selectedUsers.length }} users</span>
            </div>

            <div class="p-4 bg-indigo-50/50 dark:bg-indigo-950/20 border border-indigo-100/30 rounded-xl flex justify-between items-center text-base font-bold">
              <span class="text-indigo-700 dark:text-indigo-400">Total Sum:</span>
              <span class="text-indigo-950 dark:text-indigo-200 text-lg">TZS {{ selectedTotal.toLocaleString() }}</span>
            </div>

            <div class="space-y-3">
              <label class="block text-xs font-bold text-gray-500 uppercase tracking-wider">Select Pay Channel</label>
              
              <!-- Payment Brand Cards with inline Text-based Brand Logo icons -->
              <div class="grid grid-cols-2 gap-2">
                <div @click="paymentMethod = 'mpesa'" :class="['p-3 border rounded-xl flex items-center justify-between cursor-pointer transition-all', paymentMethod === 'mpesa' ? 'border-emerald-500 bg-emerald-500/10' : 'border-gray-200 dark:border-gray-800 hover:border-gray-400']">
                  <span class="text-xs font-bold text-emerald-600 dark:text-emerald-400">Vodacom M-Pesa</span>
                  <span class="text-[9px] bg-red-600 text-white font-black px-1 py-0.5 rounded">M-PESA</span>
                </div>
                <div @click="paymentMethod = 'airtel'" :class="['p-3 border rounded-xl flex items-center justify-between cursor-pointer transition-all', paymentMethod === 'airtel' ? 'border-red-500 bg-red-500/10' : 'border-gray-200 dark:border-gray-800 hover:border-gray-400']">
                  <span class="text-xs font-bold text-red-650">Airtel Money</span>
                  <span class="text-[9px] bg-red-500 text-white font-black px-1 py-0.5 rounded">airtel</span>
                </div>
                <div @click="paymentMethod = 'yas'" :class="['p-3 border rounded-xl flex items-center justify-between cursor-pointer transition-all', paymentMethod === 'yas' ? 'border-yellow-500 bg-yellow-500/10' : 'border-gray-200 dark:border-gray-800 hover:border-gray-400']">
                  <span class="text-xs font-bold text-yellow-600 dark:text-yellow-450">Mixx by Yas</span>
                  <span class="text-[9px] bg-yellow-500 text-black font-black px-1 py-0.5 rounded">YAS</span>
                </div>
                <div @click="paymentMethod = 'halopesa'" :class="['p-3 border rounded-xl flex items-center justify-between cursor-pointer transition-all', paymentMethod === 'halopesa' ? 'border-orange-500 bg-orange-500/10' : 'border-gray-200 dark:border-gray-800 hover:border-gray-400']">
                  <span class="text-xs font-bold text-orange-650">HaloPesa</span>
                  <span class="text-[9px] bg-orange-500 text-white font-black px-1 py-0.5 rounded">HALO</span>
                </div>
                <div @click="paymentMethod = 'card'" :class="['p-3 border rounded-xl flex items-center justify-between cursor-pointer transition-all col-span-2', paymentMethod === 'card' ? 'border-blue-500 bg-blue-500/10' : 'border-gray-200 dark:border-gray-800 hover:border-gray-400']">
                  <span class="text-xs font-bold text-blue-600 dark:text-blue-400">Visa / Mastercard / Banks</span>
                  <div class="flex gap-1">
                    <span class="text-[9px] bg-blue-700 text-white font-black px-1 py-0.5 rounded">VISA</span>
                    <span class="text-[9px] bg-orange-600 text-white font-black px-1 py-0.5 rounded">MC</span>
                  </div>
                </div>
              </div>
            </div>

            <button @click="triggerBulkPayment" class="w-full py-3 bg-gradient-to-r from-emerald-600 to-indigo-600 text-white font-bold rounded-xl hover:shadow-lg transition-all">
              Initiate Bulk Payment
            </button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
