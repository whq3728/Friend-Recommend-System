<script setup>
import { ref } from "vue";

/**
 * 校园背景：静态渐变 + 可选 /images/campus-hero.jpg，虚化叠层。
 * center：登录注册等居中；首页等用 center=false 全宽内容。
 */
defineProps({
  center: { type: Boolean, default: true },
});

const campusOk = ref(true);
</script>

<template>
  <div class="campus-bg" :class="{ 'campus-bg--center': center }">
    <div class="campus-bg__blobs" aria-hidden="true" />
    <img
      v-show="campusOk"
      class="campus-bg__img"
      src="/images/campus-hero.jpg"
      alt=""
      decoding="async"
      fetchpriority="low"
      @error="campusOk = false"
    />
    <div class="campus-bg__veil" />
    <div class="campus-bg__content">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.campus-bg {
  min-height: 100vh;
  position: relative;
  overflow: hidden;
  background: linear-gradient(145deg, #fdf8f4 0%, #e8f0ff 48%, #fff5f7 100%);
}
.campus-bg--center {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
}
.campus-bg__blobs {
  position: absolute;
  inset: -20%;
  background:
    radial-gradient(ellipse at 25% 30%, rgba(139, 21, 56, 0.1) 0%, transparent 50%),
    radial-gradient(ellipse at 75% 25%, rgba(59, 130, 246, 0.08) 0%, transparent 48%);
  pointer-events: none;
  z-index: 0;
}
.campus-bg__img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0.34;
  filter: blur(1px) saturate(1.06) contrast(1.05);
  transform: scale(1.02);
  pointer-events: none;
  z-index: 0;
}
.campus-bg__veil {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(250, 248, 245, 0.6) 0%, rgba(250, 248, 245, 0.88) 55%, #faf8f5 100%);
  pointer-events: none;
  z-index: 1;
}
.campus-bg__content {
  position: relative;
  z-index: 2;
  width: 100%;
}
.campus-bg--center .campus-bg__content {
  max-width: 440px;
}
</style>
