<script setup>
import { RouterView } from "vue-router";
import { storeToRefs } from "pinia";
import { useUiStore } from "./stores/ui";

// 根组件仅负责页面切换与全局浮动提示，不承载业务状态
const ui = useUiStore();
const { toasts } = storeToRefs(ui);
</script>

<template>
  <div class="app-root">
    <RouterView v-slot="{ Component }">
      <Transition name="fade-page" mode="out-in">
        <component :is="Component" />
      </Transition>
    </RouterView>

    <Teleport to="body">
      <div class="toast-stack" aria-live="polite">
        <TransitionGroup name="toast-slide">
          <div
            v-for="t in toasts"
            :key="t.id"
            class="float-toast"
            :class="t.type === 'err' ? 'is-err' : 'is-ok'"
          >
            {{ t.message }}
          </div>
        </TransitionGroup>
      </div>
    </Teleport>
  </div>
</template>

<style>
.fade-page-enter-active,
.fade-page-leave-active {
  transition: opacity 0.16s ease;
}
.fade-page-enter-from,
.fade-page-leave-to {
  opacity: 0;
}

.toast-stack {
  position: fixed;
  bottom: 1.25rem;
  left: 50%;
  transform: translateX(-50%);
  z-index: 9999;
  display: flex;
  flex-direction: column-reverse;
  align-items: center;
  gap: 0.5rem;
  pointer-events: none;
  max-width: min(92vw, 420px);
}
.float-toast {
  pointer-events: none;
  padding: 0.55rem 1rem;
  border-radius: 10px;
  font-size: 0.88rem;
  font-weight: 600;
  border: 1px solid var(--border);
}
.float-toast.is-ok {
  background: var(--ok-soft);
  color: #047857;
}
.float-toast.is-err {
  background: var(--err-soft);
  color: #b91c1c;
}
.toast-slide-enter-active,
.toast-slide-leave-active {
  transition: opacity 0.15s ease;
}
.toast-slide-enter-from,
.toast-slide-leave-to {
  opacity: 0;
}
</style>
