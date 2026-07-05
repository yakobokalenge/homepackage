<script setup lang="ts">
import { onMounted } from 'vue'
import { RouterView } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AppToast from '@/components/common/AppToast.vue'

const auth = useAuthStore()

onMounted(async () => {
  if (auth.token) {
    await auth.fetchUser()
  }
})
</script>

<template>
  <div id="homepackage-app" class="min-h-screen bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-gray-100 transition-colors">
    <RouterView />
    <AppToast />
  </div>
</template>
