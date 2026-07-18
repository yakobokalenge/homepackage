<script setup lang="ts">
import { RouterView } from 'vue-router'
</script>

<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-950 flex flex-col">
    <!-- Slim distraction-free container -->
    <div class="flex-1 flex flex-col">
      <RouterView />
    </div>
  </div>
</template>
