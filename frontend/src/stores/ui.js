import { defineStore } from "pinia";
import { ref } from "vue";

export const useUiStore = defineStore("ui", () => {
  const toasts = ref([]);
  const confirm = ref(null);
  let nid = 0;

  /** 相同文案+类型已在展示时不再堆叠新气泡 */
  function toast(message, type = "ok", duration = 2800) {
    if (toasts.value.some((t) => t.message === message && t.type === type)) {
      return;
    }
    const id = ++nid;
    toasts.value = [...toasts.value, { id, message, type }];
    window.setTimeout(() => {
      toasts.value = toasts.value.filter((x) => x.id !== id);
    }, duration);
  }

  /** 显示确认弹窗，返回 Promise<boolean> */
  function showConfirm(message) {
    return new Promise((resolve) => {
      confirm.value = { message, resolve };
    });
  }

  function resolveConfirm(result) {
    if (confirm.value) {
      confirm.value.resolve(result);
      confirm.value = null;
    }
  }

  return { toasts, toast, confirm, showConfirm, resolveConfirm };
});
