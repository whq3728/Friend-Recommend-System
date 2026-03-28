import { defineStore } from "pinia";
import { ref } from "vue";

export const useUiStore = defineStore("ui", () => {
  const toasts = ref([]);
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

  return { toasts, toast };
});
