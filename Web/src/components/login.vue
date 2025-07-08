<template>
  <div class="app-container">
    <Particles id="tsparticles" :particlesInit="particlesInit" :particlesLoaded="particlesLoaded" :options="options" />
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue'
import { useParticles } from './re'
import '../style.css'
export default defineComponent({
  setup() {
    const { particlesInit, particlesLoaded, options } = useParticles()
    return {
      particlesInit,
      particlesLoaded,
      options
    }
  }
})
</script>

<style></style>
