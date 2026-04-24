<script setup>
import { ref } from "vue";
import { RouterLink, useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import AuthHero from "../components/AuthHero.vue";
import { EyeIcon, EyeSlashIcon } from "@heroicons/vue/24/outline";

const auth = useAuthStore();
const router = useRouter();

const phone = ref("");
const code = ref("");
const newPassword = ref("");
const showPassword = ref(false);
const err = ref("");
const ok = ref("");
const sending = ref(false);
const countdown = ref(0); // 倒计时秒数
let countdownTimer = null;

async function sendCode() {
  err.value = "";
  ok.value = "";
  sending.value = true;
  try {
    const res = await auth.sendSms(phone.value.trim().replace(/\s/g, ""));
    if (res?.remaining_seconds) {
      // 被限流，显示倒计时
      startCountdown(res.remaining_seconds);
      err.value = `发送太频繁，请 ${res.remaining_seconds} 秒后再试`;
    } else {
      ok.value = "验证码已发送";
      startCountdown(60);
    }
  } catch (e) {
    err.value = e instanceof Error ? e.message : "发送失败";
  } finally {
    sending.value = false;
  }
}

// 启动倒计时
function startCountdown(seconds) {
  countdown.value = seconds;
  if (countdownTimer) clearInterval(countdownTimer);
  countdownTimer = setInterval(() => {
    countdown.value--;
    if (countdown.value <= 0) {
      clearInterval(countdownTimer);
      countdownTimer = null;
    }
  }, 1000);
}

async function submit() {
  err.value = "";
  ok.value = "";
  try {
    await auth.forgotReset(
      phone.value.trim().replace(/\s/g, ""),
      code.value.trim(),
      newPassword.value,
    );
    ok.value = "密码已重置，请使用新密码登录";
    setTimeout(() => router.push("/login"), 1200);
  } catch (e) {
    err.value = e instanceof Error ? e.message : "重置失败";
  }
}
</script>

<template>
  <AuthHero>
    <div class="card-shell">
      <h1>找回密码</h1>
      <p class="hint">通过手机号验证后设置新密码，验证码5分钟内有效</p>
      <div v-if="err" class="toast err">{{ err }}</div>
      <div v-if="ok" class="toast ok">{{ ok }}</div>
      <form @submit.prevent="submit">
        <div class="field">
          <label>手机号</label>
          <input v-model="phone" inputmode="numeric" maxlength="11" placeholder="注册时绑定的手机号" required />
        </div>
        <div class="field code-row">
          <div class="grow">
            <label>验证码</label>
            <input v-model="code" required maxlength="6" inputmode="numeric" placeholder="请输入6位验证码" />
          </div>
          <button type="button" class="btn btn-ghost btn-code" :disabled="sending || countdown > 0" @click="sendCode">
            {{ countdown > 0 ? `${countdown}s` : sending ? "…" : "获取验证码" }}
          </button>
        </div>
        <div class="field">
          <label>新密码（至少 4 位）</label>
          <label>新密码（至少 4 位）</label>
          <div class="password-row">
            <input
              v-model="newPassword"
              :type="showPassword ? 'text' : 'password'"
              required
              minlength="4"
              autocomplete="new-password"
            />
            <button
              type="button"
              class="btn btn-ghost btn-sm toggle-pass"
              :aria-label="showPassword ? '隐藏密码' : '显示密码'"
              @click="showPassword = !showPassword"
            >
              <EyeSlashIcon v-if="showPassword" class="h-ico" />
              <EyeIcon v-else class="h-ico" />
            </button>
          </div>
        </div>
        <button type="submit" class="btn btn-primary wide">重置密码</button>
      </form>
      <p class="foot">
        <RouterLink to="/login">返回登录</RouterLink>
      </p>
    </div>
  </AuthHero>
</template>

<style scoped>
.card-shell {
  width: 100%;
  background: var(--bg-panel);
  border-radius: var(--radius-lg);
  padding: 2rem 1.75rem;
  border: 1px solid var(--border);
}
h1 {
  margin: 0;
  font-size: 1.55rem;
}
.hint {
  color: var(--text-muted);
  font-size: 0.88rem;
  margin: 0.4rem 0 1.25rem;
  line-height: 1.5;
}
.wide {
  width: 100%;
  margin-top: 0.5rem;
}
.foot {
  margin-top: 1.25rem;
  text-align: center;
  font-size: 0.9rem;
}
.code-row {
  display: flex;
  gap: 0.5rem;
  align-items: flex-end;
}
.grow {
  flex: 1;
}
.btn-code {
  flex-shrink: 0;
  margin-bottom: 0.05rem;
}
.password-row {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}
.password-row input {
  flex: 1;
}
.toggle-pass {
  flex-shrink: 0;
  min-width: 3.3rem;
  padding-left: 0.7rem;
  padding-right: 0.7rem;
}
</style>
