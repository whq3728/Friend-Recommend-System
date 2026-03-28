<script setup>
/**
 * 登录/注册页外壳：复用 CampusBackdrop（无额外动画）。
 */
import CampusBackdrop from "./CampusBackdrop.vue";
</script>

<template>
  <CampusBackdrop center>
    <div class="auth-slot">
      <slot />
    </div>
  </CampusBackdrop>
</template>

<style scoped>
.auth-slot {
  width: 100%;
  max-width: 440px;
  margin: 0 auto;
}
</style>
