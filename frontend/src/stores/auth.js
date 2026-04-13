import { defineStore } from "pinia";
import { ref } from "vue";
import { api } from "../api/client";

export const useAuthStore = defineStore("auth", () => {
  const user = ref(null);
  const ready = ref(false);

  async function fetchMe() {
    try {
      user.value = await api("/api/auth/me");
    } catch {
      user.value = null;
    } finally {
      ready.value = true;
    }
  }

  async function login(account, password) {
    user.value = await api("/api/auth/login", {
      method: "POST",
      body: { account, password },
    });
  }

  async function loginPhone(phone, code) {
    user.value = await api("/api/auth/login-phone", {
      method: "POST",
      body: { phone, code },
    });
  }

  async function sendSms(phone) {
    return api("/api/auth/sms/send", { method: "POST", body: { phone } });
  }

  async function forgotReset(phone, code, new_password) {
    return api("/api/auth/forgot-reset", {
      method: "POST",
      body: { phone, code, new_password },
    });
  }

  /**
   * @param {object} extra - phone, gender, grade, interests[], skills[], sms_code（绑定手机时必填）
   */
  async function register(account, username, password, extra = {}) {
    await api("/api/auth/register", {
      method: "POST",
      body: {
        account,
        username,
        password,
        phone: extra.phone || "",
        gender: extra.gender || "",
        grade: extra.grade || "",
        interests: extra.interests || [],
        skills: extra.skills || [],
        sms_code: extra.sms_code || "",
      },
    });
  }

  async function logout() {
    await api("/api/auth/logout", { method: "POST" });
    user.value = null;
  }

  return {
    user,
    ready,
    fetchMe,
    login,
    loginPhone,
    sendSms,
    forgotReset,
    register,
    logout,
  };
});
