<script setup lang="ts">
import { RouterView } from 'vue-router'
</script>

<template>
  <!-- Full-screen proctored layout with no navigation, no escape -->
  <div class="fixed inset-0 bg-gray-100 dark:bg-gray-950 z-50 overflow-auto select-none" @contextmenu.prevent>
    <RouterView />
  </div>
</template>

<style scoped>
div {
  user-select: none;
  -webkit-user-select: none;
}
</style>
