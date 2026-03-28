<script setup>
import { ref } from "vue";
import { useRoute, useRouter, RouterLink } from "vue-router";
import { useAuthStore } from "../stores/auth";
import AuthHero from "../components/AuthHero.vue";
import { EyeIcon, EyeSlashIcon } from "@heroicons/vue/24/outline";

const auth = useAuthStore();
const router = useRouter();
const route = useRoute();

const tab = ref("account");
const account = ref("");
const password = ref("");
const showPassword = ref(false);
const phone = ref("");
const code = ref("");
const err = ref("");
const sending = ref(false);
const smsHint = ref("");

// 账号密码登录：成功后优先跳转到 guard 记录的原始页面
async function submitAccount() {
  err.value = "";
  try {
    await auth.login(account.value.trim(), password.value);
    const r = route.query.redirect;
    router.push(typeof r === "string" ? r : "/app/recommend");
  } catch (e) {
    err.value = e instanceof Error ? e.message : "登录失败";
  }
}

// 演示环境短信验证码发送
async function sendCode() {
  err.value = "";
  smsHint.value = "";
  sending.value = true;
  try {
    const res = await auth.sendSms(phone.value.trim().replace(/\s/g, ""));
    smsHint.value = res?.hint || "验证码已发送";
  } catch (e) {
    err.value = e instanceof Error ? e.message : "发送失败";
  } finally {
    sending.value = false;
  }
}

// 手机号验证码登录
async function submitPhone() {
  err.value = "";
  try {
    await auth.loginPhone(phone.value.trim().replace(/\s/g, ""), code.value.trim());
    const r = route.query.redirect;
    router.push(typeof r === "string" ? r : "/app/recommend");
  } catch (e) {
    err.value = e instanceof Error ? e.message : "登录失败";
  }
}
</script>

<template>
  <AuthHero>
    <div class="card-shell">
      <h1>登录</h1>
      <p class="hint">欢迎回到 JNU Link</p>

      <div class="tabs" role="tablist">
        <button
          type="button"
          role="tab"
          :aria-selected="tab === 'account'"
          :class="{ on: tab === 'account' }"
          @click="tab = 'account'"
        >
          账号密码
        </button>
        <button
          type="button"
          role="tab"
          :aria-selected="tab === 'phone'"
          :class="{ on: tab === 'phone' }"
          @click="tab = 'phone'"
        >
          手机验证码
        </button>
      </div>

      <div v-if="err" class="toast err shake">{{ err }}</div>
      <div v-if="smsHint" class="toast ok">{{ smsHint }}</div>

      <form v-show="tab === 'account'" class="form-block" @submit.prevent="submitAccount">
        <div class="field">
          <label>账号</label>
          <input v-model="account" required autocomplete="username" placeholder="学号或自定义账号" />
        </div>
        <div class="field">
          <label>密码</label>
          <div class="password-row">
            <input
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              required
              autocomplete="current-password"
              placeholder="输入密码"
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
        <div class="row-between">
          <RouterLink class="link-muted" to="/forgot-password">忘记密码？</RouterLink>
        </div>
        <button type="submit" class="btn btn-primary wide tap-scale">登录</button>
      </form>

      <form v-show="tab === 'phone'" class="form-block" @submit.prevent="submitPhone">
        <div class="field">
          <label>手机号</label>
          <input v-model="phone" inputmode="numeric" autocomplete="tel" placeholder="11 位手机号" maxlength="11" />
        </div>
        <div class="field code-row">
          <div class="grow">
            <label>验证码</label>
            <input v-model="code" inputmode="numeric" placeholder="演示固定为 123456" maxlength="8" />
          </div>
          <button type="button" class="btn btn-ghost btn-code tap-scale" :disabled="sending" @click="sendCode">
            {{ sending ? "发送中…" : "获取验证码" }}
          </button>
        </div>
        <p class="mini">需已在注册时绑定该手机号；演示环境验证码固定为 <strong>123456</strong>。</p>
        <button type="submit" class="btn btn-primary wide tap-scale">验证并登录</button>
      </form>

      <p class="foot">
        没有账号？
        <RouterLink to="/register">注册</RouterLink>
        ·
        <RouterLink to="/">返回首页</RouterLink>
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
  font-size: 1.65rem;
  color: var(--text);
}
.hint {
  color: var(--text-muted);
  font-size: 0.9rem;
  margin: 0.35rem 0 1.25rem;
}
.tabs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.35rem;
  margin-bottom: 1.25rem;
  padding: 0.25rem;
  background: var(--bg-page);
  border-radius: 12px;
  border: 1px solid var(--border-light);
}
.tabs button {
  border: none;
  background: transparent;
  padding: 0.55rem 0.5rem;
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--text-muted);
  border-radius: 10px;
  cursor: pointer;
  font-family: inherit;
  transition: background 0.2s, color 0.2s;
}
.tabs button.on {
  background: var(--bg-panel);
  color: var(--jn-maroon);
  box-shadow: var(--shadow);
}
.form-block {
  animation: fade-in 0.35s ease;
}
@keyframes fade-in {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
.row-between {
  display: flex;
  justify-content: flex-end;
  margin: -0.25rem 0 0.75rem;
}
.link-muted {
  font-size: 0.85rem;
  color: var(--text-muted);
  text-decoration: none;
}
.link-muted:hover {
  color: var(--jn-maroon);
  text-decoration: underline;
}
.wide {
  width: 100%;
  margin-top: 0.35rem;
}
.foot {
  margin-top: 1.5rem;
  text-align: center;
  font-size: 0.9rem;
  color: var(--text-muted);
}
.code-row {
  display: flex;
  gap: 0.5rem;
  align-items: flex-end;
}
.password-row {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}
.toggle-pass {
  flex-shrink: 0;
  min-width: 3.3rem;
  padding-left: 0.7rem;
  padding-right: 0.7rem;
}
.grow {
  flex: 1;
  min-width: 0;
}
.btn-code {
  flex-shrink: 0;
  margin-bottom: 0.05rem;
  white-space: nowrap;
}
.mini {
  font-size: 0.78rem;
  color: var(--text-subtle);
  margin: 0 0 0.75rem;
  line-height: 1.45;
}
.shake {
  animation: shake 0.45s ease;
}
@keyframes shake {
  0%,
  100% {
    transform: translateX(0);
  }
  20% {
    transform: translateX(-6px);
  }
  40% {
    transform: translateX(6px);
  }
  60% {
    transform: translateX(-4px);
  }
  80% {
    transform: translateX(4px);
  }
}
.tap-scale:active {
  transform: scale(0.98);
}
</style>
