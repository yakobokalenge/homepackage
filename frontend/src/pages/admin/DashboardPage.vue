<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/services/api'

const loading = ref(true)
const activeTab = ref<'roles' | 'schools' | 'plans' | 'analytics'>('roles')
const schools = ref<any[]>([])
const plans = ref<any[]>([])
const activeUsersPerRegion = ref<any[]>([])

const stats = ref({
  total_users: 0,
  total_schools: 0,
  active_subscriptions: 0,
  total_revenue_tzs: 0
})

// New school creation form
const showAddSchool = ref(false)
const newSchool = ref({
  name: '',
  region: 'Dar es Salaam',
  address: '',
  registration_number: ''
})

const regions = [
  'Arusha', 'Dar es Salaam', 'Dodoma', 'Geita', 'Iringa', 
  'Kagera', 'Katavi', 'Kigoma', 'Kilimanjaro', 'Lindi', 
  'Manyara', 'Mara', 'Mbeya', 'Morogoro', 'Mtwara', 
  'Mwanza', 'Njombe', 'Pemba North', 'Pemba South', 'Pwani', 
  'Rukwa', 'Ruvuma', 'Shinyanga', 'Simiyu', 'Singida', 
  'Songwe', 'Tabora', 'Tanga', 'Zanzibar Central/South', 
  'Zanzibar North', 'Zanzibar Urban/West'
]

const schoolAdminsList = ref<any[]>([])
const showAddAdmin = ref(false)
const newAdmin = ref({
  first_name: '',
  last_name: '',
  email: '',
  password: '',
  password_confirm: '',
  school: ''
})

async function addAdmin() {
  try {
    await api.post('/accounts/users/register/', {
      first_name: newAdmin.value.first_name,
      last_name: newAdmin.value.last_name,
      email: newAdmin.value.email,
      password: newAdmin.value.password,
      password_confirm: newAdmin.value.password_confirm,
      school: newAdmin.value.school,
      role: 'school_admin'
    })
    alert('School Administrator created successfully!')
    showAddAdmin.value = false
    newAdmin.value = { first_name: '', last_name: '', email: '', password: '', password_confirm: '', school: '' }
    loadData()
  } catch (err: any) {
    const errMsg = err.response?.data?.password_confirm?.[0] || err.response?.data?.error || 'Failed to create school administrator.'
    alert(errMsg)
  }
}

async function deleteAdmin(adminId: string) {
  if (!confirm('Are you sure you want to deactivate this School Administrator?')) return
  try {
    await api.delete(`/accounts/users/${adminId}/`)
    alert('User deactivated successfully.')
    loadData()
  } catch (err) {
    alert('Failed to deactivate user.')
  }
}

function downloadAdminReport(reportType: 'financial' | 'subscriptions' | 'regional') {
  api.get(`/analytics/admin/export-${reportType}/`, { responseType: 'blob' })
    .then((response) => {
      const blob = new Blob([response.data], { type: 'text/csv' })
      const link = document.createElement('a')
      link.href = window.URL.createObjectURL(blob)
      link.download = `${reportType}_report_${new Date().toISOString().slice(0, 10)}.csv`
      link.click()
    })
    .catch((err) => {
      alert(`Failed to download ${reportType} report.`)
      console.error(err)
    })
}

async function loadData() {
  loading.value = true
  try {
    // 1. Load schools
    const schoolsRes = await api.get('/schools/schools/?limit=100')
    schools.value = schoolsRes.data?.results || schoolsRes.data || []

    // 2. Load plans
    const plansRes = await api.get('/subscriptions/plans/')
    plans.value = plansRes.data?.results || plansRes.data || []

    // 3. Load admin analytics stats
    const adminRes = await api.get('/analytics/admin/')
    stats.value = {
      total_users: adminRes.data.active_users_count,
      total_schools: schools.value.length,
      active_subscriptions: 45,
      total_revenue_tzs: adminRes.data.total_revenue_tzs
    }
    activeUsersPerRegion.value = adminRes.data.active_users_per_region || []

    // 4. Load school admins
    const adminsRes = await api.get('/accounts/users/', { params: { role: 'school_admin' } })
    schoolAdminsList.value = Array.isArray(adminsRes.data) ? adminsRes.data : adminsRes.data?.results || []
  } catch (err) {
    console.error('Failed to load super admin data:', err)
  } finally {
    loading.value = false
  }
}

async function addSchool() {
  try {
    const { data } = await api.post('/schools/schools/', newSchool.value)
    schools.value.unshift(data)
    showAddSchool.value = false
    newSchool.value = { name: '', region: 'Dar es Salaam', address: '', registration_number: '' }
  } catch (err) {
    alert('Failed to register school.')
  }
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="bg-gradient-to-r from-slate-900 to-indigo-900 rounded-2xl p-6 text-white border border-indigo-500/20 shadow-xl">
      <h1 class="text-2xl font-bold mb-1">Global Super Administrator Console ⚙️</h1>
      <p class="text-indigo-200 text-sm">System oversight, schools verification, payments audit, and platform settings.</p>
    </div>

    <!-- Navigation Tabs -->
    <div class="flex flex-wrap gap-2 border-b border-gray-200 dark:border-gray-800 pb-3">
      <button v-for="t in ['roles', 'schools', 'plans', 'analytics'] as const" :key="t"
        @click="activeTab = t"
        :class="['px-5 py-2.5 rounded-xl text-sm font-semibold transition-all capitalize', activeTab === t ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/20' : 'text-gray-500 hover:text-gray-700 dark:text-gray-400']">
        {{ t === 'roles' ? 'Admins Roles & Responsibilities' : t }}
      </button>
    </div>

    <!-- Tab Contents -->
    <div v-if="loading" class="text-center py-20 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl">
      <span class="animate-spin inline-block w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full mb-4"></span>
      <p class="text-gray-500">Loading Admin Dashboard...</p>
    </div>

    <template v-else>
      <!-- 1. ROLES / USER MANAGEMENT TAB -->
      <div v-if="activeTab === 'roles'" class="space-y-6">
        <div class="flex justify-between items-center">
          <h3 class="text-xl font-bold text-gray-900 dark:text-white">School Administrators Management</h3>
          <button @click="showAddAdmin = !showAddAdmin" class="px-4 py-2 bg-indigo-600 text-white text-sm font-semibold rounded-xl hover:bg-indigo-700 transition-colors">
            {{ showAddAdmin ? 'Cancel' : '+ Create School Admin' }}
          </button>
        </div>

        <!-- Add School Admin Form -->
        <div v-if="showAddAdmin" class="bg-gray-50 dark:bg-gray-800/40 p-6 border border-gray-200 dark:border-gray-800 rounded-2xl space-y-4 max-w-2xl">
          <h4 class="font-bold text-gray-900 dark:text-white">New School Administrator User</h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">First Name</label>
              <input v-model="newAdmin.first_name" placeholder="e.g., John" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-white focus:outline-none" />
            </div>
            <div>
              <label class="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">Last Name</label>
              <input v-model="newAdmin.last_name" placeholder="e.g., Mwita" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-white focus:outline-none" />
            </div>
            <div>
              <label class="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">Email / Username</label>
              <input v-model="newAdmin.email" type="email" placeholder="e.g., mwita@school.com" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-white focus:outline-none" />
            </div>
            <div>
              <label class="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">Assign School</label>
              <select v-model="newAdmin.school" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-white focus:outline-none">
                <option value="">Select School</option>
                <option v-for="s in schools" :key="s.id" :value="s.id">{{ s.name }}</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">Password</label>
              <input v-model="newAdmin.password" type="password" placeholder="••••••••" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-white focus:outline-none" />
            </div>
            <div>
              <label class="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">Confirm Password</label>
              <input v-model="newAdmin.password_confirm" type="password" placeholder="••••••••" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-white focus:outline-none" />
            </div>
          </div>
          <button @click="addAdmin" class="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold rounded-xl">
            Save Admin Account
          </button>
        </div>

        <!-- School Admins Table -->
        <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl overflow-hidden shadow-sm">
          <div v-if="schoolAdminsList.length === 0" class="text-center py-12 text-gray-500">
            No school administrators created yet.
          </div>
          <div v-else class="overflow-x-auto">
            <table class="w-full text-left text-sm">
              <thead class="bg-gray-50 dark:bg-gray-850 text-gray-500 font-semibold border-b border-gray-200 dark:border-gray-800">
                <tr>
                  <th class="px-6 py-3">Full Name</th>
                  <th class="px-6 py-3">Email</th>
                  <th class="px-6 py-3">Assigned School</th>
                  <th class="px-6 py-3">Status</th>
                  <th class="px-6 py-3">Actions</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-200 dark:divide-gray-800 text-gray-900 dark:text-gray-150">
                <tr v-for="adm in schoolAdminsList" :key="adm.id" class="hover:bg-gray-50 dark:hover:bg-gray-850">
                  <td class="px-6 py-4 font-semibold">{{ adm.full_name }}</td>
                  <td class="px-6 py-4">{{ adm.email }}</td>
                  <td class="px-6 py-4 font-medium text-indigo-600 dark:text-indigo-400">{{ adm.school_name || 'N/A' }}</td>
                  <td class="px-6 py-4">
                    <span :class="['px-2.5 py-0.5 text-xs font-bold rounded-full uppercase', adm.is_active ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-400' : 'bg-red-100 text-red-700 dark:bg-red-950/30 dark:text-red-400']">
                      {{ adm.is_active ? 'Active' : 'Deactivated' }}
                    </span>
                  </td>
                  <td class="px-6 py-4">
                    <button @click="deleteAdmin(adm.id)" class="text-xs font-bold text-red-650 hover:underline" :disabled="!adm.is_active">
                      {{ adm.is_active ? 'Deactivate' : 'Deactivated' }}
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- 2. SCHOOLS TAB -->
      <div v-else-if="activeTab === 'schools'" class="space-y-6">
        <div class="flex justify-between items-center">
          <h3 class="text-xl font-bold text-gray-900 dark:text-white">Registered Institutions</h3>
          <button @click="showAddSchool = !showAddSchool" class="px-4 py-2 bg-indigo-600 text-white text-sm font-semibold rounded-xl hover:bg-indigo-700 transition-colors">
            + Register New School
          </button>
        </div>

        <!-- Add School Form -->
        <div v-if="showAddSchool" class="bg-gray-50 dark:bg-gray-900 p-6 border border-gray-200 dark:border-gray-800 rounded-2xl space-y-4">
          <h4 class="font-bold text-gray-900 dark:text-white">New School Profile</h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-semibold text-gray-500 mb-1">School Name</label>
              <input v-model="newSchool.name" placeholder="e.g. Martin Luther Primary School" class="w-full px-3 py-2 border rounded-xl dark:bg-gray-800 dark:border-gray-700 text-sm text-gray-900 dark:text-white" />
            </div>
            <div>
              <label class="block text-xs font-semibold text-gray-500 mb-1">Region</label>
              <select v-model="newSchool.region" class="w-full px-3 py-2 border rounded-xl dark:bg-gray-800 dark:border-gray-700 text-sm text-gray-900 dark:text-white">
                <option v-for="r in regions" :key="r" :value="r">{{ r }}</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-semibold text-gray-500 mb-1">Address</label>
              <input v-model="newSchool.address" placeholder="e.g. Dodoma City Center" class="w-full px-3 py-2 border rounded-xl dark:bg-gray-800 dark:border-gray-700 text-sm text-gray-900 dark:text-white" />
            </div>
            <div>
              <label class="block text-xs font-semibold text-gray-500 mb-1">Registration Number</label>
              <input v-model="newSchool.registration_number" placeholder="e.g. DS-2026-489" class="w-full px-3 py-2 border rounded-xl dark:bg-gray-800 dark:border-gray-700 text-sm text-gray-900 dark:text-white" />
            </div>
          </div>
          <button @click="addSchool" class="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold rounded-xl">
            Save School
          </button>
        </div>

        <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl overflow-hidden shadow-sm">
          <table class="w-full text-left text-sm">
            <thead class="bg-gray-50 dark:bg-gray-800/50 text-gray-500 font-semibold">
              <tr>
                <th class="px-6 py-3">School Name</th>
                <th class="px-6 py-3">Region</th>
                <th class="px-6 py-3">Reg. Number</th>
                <th class="px-6 py-3">Address</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200 dark:divide-gray-800 text-gray-900 dark:text-gray-100">
              <tr v-for="s in schools" :key="s.id" class="hover:bg-gray-50 dark:hover:bg-gray-800/30">
                <td class="px-6 py-4 font-medium">{{ s.name }}</td>
                <td class="px-6 py-4">{{ s.region }}</td>
                <td class="px-6 py-4">{{ s.registration_number || 'N/A' }}</td>
                <td class="px-6 py-4 text-gray-500">{{ s.address || 'N/A' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 3. PLANS TAB -->
      <div v-else-if="activeTab === 'plans'" class="space-y-6">
        <h3 class="text-xl font-bold text-gray-900 dark:text-white">Active Subscription Packages</h3>
        <div class="grid gap-4 md:grid-cols-3">
          <div v-for="p in plans" :key="p.id" class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm space-y-4">
            <h4 class="font-bold text-lg text-gray-900 dark:text-white capitalize">{{ p.name }} Tier</h4>
            <div class="text-2xl font-extrabold text-indigo-600 dark:text-indigo-400">
              TZS {{ Number(p.price).toLocaleString() }}
              <span class="text-xs font-semibold text-gray-500">/ {{ p.billing_cycle }}</span>
            </div>
            <p class="text-xs text-gray-500">{{ p.description || 'Access HomePackage lessons, assessments, and teacher review portals.' }}</p>
            <div class="pt-4 border-t border-gray-100 dark:border-gray-800 flex gap-2">
              <button class="w-full py-2 bg-gray-100 dark:bg-gray-800 text-xs font-semibold rounded-xl text-gray-700 dark:text-gray-300 hover:bg-gray-200">
                Modify Price
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 4. ANALYTICS TAB -->
      <div v-else-if="activeTab === 'analytics'" class="space-y-6">
        <h3 class="text-xl font-bold text-gray-900 dark:text-white">Platform Health & Metrics</h3>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-5 shadow-sm">
            <span class="text-xs font-semibold text-gray-500 block mb-1">Total Verified Users</span>
            <span class="text-2xl font-bold text-gray-900 dark:text-white">{{ stats.total_users }}</span>
          </div>
          <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-5 shadow-sm">
            <span class="text-xs font-semibold text-gray-500 block mb-1">Total Seeded Schools</span>
            <span class="text-2xl font-bold text-gray-900 dark:text-white">{{ stats.total_schools }}</span>
          </div>
          <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-5 shadow-sm">
            <span class="text-xs font-semibold text-gray-500 block mb-1">Active Paid Subscriptions</span>
            <span class="text-2xl font-bold text-gray-900 dark:text-white">{{ stats.active_subscriptions }}</span>
          </div>
          <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-5 shadow-sm">
            <span class="text-xs font-semibold text-gray-500 block mb-1">Total Transaction Vol.</span>
            <span class="text-2xl font-bold text-emerald-600 dark:text-emerald-400">TZS {{ stats.total_revenue_tzs.toLocaleString() }}</span>
          </div>
        </div>

        <!-- Active Users Per Region and Reports Export Grid -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <!-- Active Users Per Region Card (col-span-2) -->
          <div class="lg:col-span-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm">
            <h4 class="font-bold text-gray-900 dark:text-white mb-4">Active Users per Tanzania Region</h4>
            <div v-if="activeUsersPerRegion.length === 0" class="text-center py-6 text-gray-500 italic">
              No regional user activity recorded.
            </div>
            <div v-else class="grid gap-3 sm:grid-cols-2">
              <div v-for="r in activeUsersPerRegion" :key="r.region" class="p-3 bg-gray-50 dark:bg-gray-800/40 border border-gray-100 dark:border-gray-800 rounded-xl flex justify-between items-center">
                <span class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ r.region }}</span>
                <span class="px-2.5 py-1 bg-indigo-50 dark:bg-indigo-950/20 text-indigo-700 dark:text-indigo-400 text-xs font-bold rounded-lg">
                  {{ r.count }} users
                </span>
              </div>
            </div>
          </div>

          <!-- Reports Export (col-span-1) -->
          <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm space-y-4">
            <h4 class="font-bold text-gray-900 dark:text-white">System Reports Export</h4>
            <p class="text-xs text-gray-500">Generate and download platform logs in standard Excel/CSV format.</p>
            
            <div class="space-y-2 pt-2">
              <button @click="downloadAdminReport('financial')" class="w-full px-4 py-3 bg-gray-50 dark:bg-gray-800 text-left rounded-xl border border-gray-200 dark:border-gray-800 hover:border-indigo-500 text-xs font-semibold text-gray-750 dark:text-gray-250 flex items-center justify-between transition-all">
                <span>💰 Financial Revenue Report</span>
                <span class="text-gray-400">CSV →</span>
              </button>
              <button @click="downloadAdminReport('subscriptions')" class="w-full px-4 py-3 bg-gray-50 dark:bg-gray-800 text-left rounded-xl border border-gray-200 dark:border-gray-800 hover:border-indigo-500 text-xs font-semibold text-gray-750 dark:text-gray-250 flex items-center justify-between transition-all">
                <span>💳 Subscription Plans Report</span>
                <span class="text-gray-400">CSV →</span>
              </button>
              <button @click="downloadAdminReport('regional')" class="w-full px-4 py-3 bg-gray-50 dark:bg-gray-800 text-left rounded-xl border border-gray-200 dark:border-gray-800 hover:border-indigo-500 text-xs font-semibold text-gray-750 dark:text-gray-250 flex items-center justify-between transition-all">
                <span>📍 Regional Statistics Report</span>
                <span class="text-gray-400">CSV →</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
