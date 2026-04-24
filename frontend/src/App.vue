<script setup>
import { RouterView } from "vue-router";
import { storeToRefs } from "pinia";
import { useUiStore } from "./stores/ui";

// 根组件仅负责页面切换与全局浮动提示，不承载业务状态
const ui = useUiStore();
const { toasts, confirm } = storeToRefs(ui);
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

      <Transition name="modal-fade">
        <div v-if="confirm" class="modal-overlay" @click.self="ui.resolveConfirm(false)">
          <div class="modal-box">
            <p class="modal-msg">{{ confirm.message }}</p>
            <div class="modal-actions">
              <button class="btn btn-ghost" @click="ui.resolveConfirm(false)">取消</button>
              <button class="btn btn-danger-confirm" @click="ui.resolveConfirm(true)">确认</button>
            </div>
          </div>
        </div>
      </Transition>
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
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  backdrop-filter: blur(2px);
}
.modal-box {
  background: var(--bg-panel);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 1.5rem 1.75rem;
  max-width: min(90vw, 360px);
  width: 100%;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.25);
  text-align: center;
}
.modal-msg {
  font-size: 0.95rem;
  color: var(--text);
  margin: 0 0 1.25rem;
  line-height: 1.55;
}
.modal-actions {
  display: flex;
  gap: 0.75rem;
  justify-content: center;
}
.modal-actions .btn {
  flex: 1;
  max-width: 120px;
}
.btn-danger-confirm {
  background: linear-gradient(135deg, var(--jn-maroon), #6d0f2b);
  color: #fff;
  border: none;
}
.btn-danger-confirm:hover {
  filter: brightness(1.05);
}
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.18s ease;
}
.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
</style>
