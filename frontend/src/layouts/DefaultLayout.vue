<script setup lang="ts">
import { RouterView } from 'vue-router'
import Navbar from '@/components/nav/Navbar.vue'
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <Navbar />
    <main class="flex-1">
      <RouterView />
    </main>
    <footer class="bg-gray-900 text-gray-400 py-12 px-4">
      <div class="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-8">
        <div>
          <h3 class="text-white font-bold text-lg mb-4">📚 HomePackage</h3>
          <p class="text-sm leading-relaxed">Tanzania's national online learning and assessment platform for students and teachers.</p>
        </div>
        <div>
          <h4 class="text-white font-semibold mb-3">Platform</h4>
          <ul class="space-y-2 text-sm">
            <li><RouterLink to="/plans" class="hover:text-white transition-colors">Plans & Pricing</RouterLink></li>
            <li><a href="#" class="hover:text-white transition-colors">Features</a></li>
            <li><a href="#" class="hover:text-white transition-colors">For Schools</a></li>
          </ul>
        </div>
        <div>
          <h4 class="text-white font-semibold mb-3">Support</h4>
          <ul class="space-y-2 text-sm">
            <li><a href="#" class="hover:text-white transition-colors">Help Center</a></li>
            <li><a href="#" class="hover:text-white transition-colors">Contact Us</a></li>
            <li><a href="#" class="hover:text-white transition-colors">Privacy Policy</a></li>
          </ul>
        </div>
        <div>
          <h4 class="text-white font-semibold mb-3">Connect</h4>
          <ul class="space-y-2 text-sm">
            <li>📧 support@homepackage.co.tz</li>
            <li>📞 +255 XXX XXX XXX</li>
            <li>📍 Dar es Salaam, Tanzania</li>
          </ul>
        </div>
      </div>
      <div class="max-w-7xl mx-auto mt-8 pt-8 border-t border-gray-800 text-sm text-center">
        <p>&copy; {{ new Date().getFullYear() }} HomePackage. Built with ❤️ for Tanzania 🇹🇿</p>
      </div>
    </footer>
  </div>
</template>
