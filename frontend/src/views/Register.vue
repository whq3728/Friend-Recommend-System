<script setup>
import { ref, computed } from "vue";
import { useRouter, RouterLink } from "vue-router";
import { useAuthStore } from "../stores/auth";
import AuthHero from "../components/AuthHero.vue";
import { DevicePhoneMobileIcon, MapPinIcon } from "@heroicons/vue/24/outline";

const PRESET_TAGS = [
  "📚 自习泡馆",
  "🏃 运动健身",
  "🎮 游戏开黑",
  "🎵 音乐现场",
  "📷 摄影扫街",
  "🍜 探店美食",
  "🎬 电影追剧",
  "✈️ 旅行徒步",
  "💻 编程技术",
  "🎨 设计绘画",
  "📖 读书会",
  "🧪 科研实验",
];

const auth = useAuthStore();
const router = useRouter();

const account = ref("");
const username = ref("");
const password = ref("");
const gender = ref("");
const grade = ref("");
const phone = ref("");
const smsCode = ref("");
const selectedTags = ref([]);
const err = ref("");
const ok = ref(false);
const sending = ref(false);
const smsHint = ref("");

const bindPhone = computed(() => phone.value.replace(/\s/g, "").length >= 11);

function toggleTag(t) {
  const i = selectedTags.value.indexOf(t);
  if (i >= 0) selectedTags.value = selectedTags.value.filter((x) => x !== t);
  else if (selectedTags.value.length < 12) selectedTags.value = [...selectedTags.value, t];
}

async function sendCode() {
  err.value = "";
  smsHint.value = "";
  sending.value = true;
  try {
    const res = await auth.sendSms(phone.value.trim().replace(/\s/g, ""));
    smsHint.value = res?.hint || "";
  } catch (e) {
    err.value = e instanceof Error ? e.message : "发送失败";
  } finally {
    sending.value = false;
  }
}

async function submit() {
  err.value = "";
  ok.value = false;
  if (bindPhone.value && !smsCode.value.trim()) {
    err.value = "填写手机号后需填写短信验证码";
    return;
  }
  try {
    await auth.register(account.value.trim(), username.value.trim(), password.value, {
      gender: gender.value,
      grade: grade.value,
      phone: bindPhone.value ? phone.value.trim().replace(/\s/g, "") : "",
      interests: [...selectedTags.value],
      sms_code: bindPhone.value ? smsCode.value.trim() : "",
    });
    ok.value = true;
    setTimeout(() => router.push("/login"), 900);
  } catch (e) {
    err.value = e instanceof Error ? e.message : "注册失败";
  }
}
</script>

<template>
  <AuthHero>
    <div class="card-shell">
      <h1>注册</h1>
      <p class="hint">选几个兴趣标签，注册后即可参与匹配</p>
      <div v-if="err" class="toast err">{{ err }}</div>
      <div v-if="ok" class="toast ok">注册成功，正在跳转登录…</div>
      <form @submit.prevent="submit">
        <div class="field">
          <label>登录账号</label>
          <input v-model="account" required autocomplete="username" placeholder="学号或自定义，用于密码登录" />
        </div>
        <div class="field">
          <label>昵称</label>
          <input v-model="username" required maxlength="64" placeholder="大家看到的称呼" />
        </div>
        <div class="field-row">
          <div class="field half">
            <label>性别</label>
            <select v-model="gender">
              <option value="">不展示</option>
              <option value="男">男</option>
              <option value="女">女</option>
              <option value="其他">其他</option>
            </select>
          </div>
          <div class="field half">
            <label>年级</label>
            <select v-model="grade">
              <option value="">请选择</option>
              <option value="本科一年级">本科一年级</option>
              <option value="本科二年级">本科二年级</option>
              <option value="本科三年级">本科三年级</option>
              <option value="本科四年级">本科四年级</option>
              <option value="硕士">硕士</option>
              <option value="博士">博士</option>
            </select>
          </div>
        </div>
        <div class="field">
          <label>密码（至少 4 位）</label>
          <input v-model="password" type="password" required autocomplete="new-password" />
        </div>

        <div class="section-title">
          <MapPinIcon class="h-ico" /> 兴趣标签（可多选）
        </div>
        <div class="tags">
          <button
            v-for="t in PRESET_TAGS"
            :key="t"
            type="button"
            class="tag"
            :class="{ on: selectedTags.includes(t) }"
            @click="toggleTag(t)"
          >
            {{ t }}
          </button>
        </div>
        <p class="tag-hint">已选 {{ selectedTags.length }} 个，可随时在资料页修改</p>

        <div class="section-title">
          <DevicePhoneMobileIcon class="h-ico" /> 手机号（可选，用于验证码登录与找回密码）
        </div>
        <div class="field code-row">
          <div class="grow">
            <input v-model="phone" inputmode="numeric" maxlength="11" placeholder="不填则仅用账号密码登录" />
          </div>
          <button type="button" class="btn btn-ghost btn-sm" :disabled="sending || !bindPhone" @click="sendCode">
            获取验证码
          </button>
        </div>
        <div v-if="bindPhone" class="field">
          <input v-model="smsCode" maxlength="8" placeholder="验证码（演示 123456）" />
        </div>
        <div v-if="smsHint" class="toast ok small-toast">{{ smsHint }}</div>

        <button type="submit" class="btn btn-primary wide tap-scale">创建账号</button>
      </form>
      <p class="foot">
        已有账号？
        <RouterLink to="/login">登录</RouterLink>
        ·
        <RouterLink to="/">返回首页</RouterLink>
      </p>
    </div>
  </AuthHero>
</template>

<style scoped>
.card-shell {
  width: 100%;
  max-height: min(92vh, 900px);
  overflow-y: auto;
  background: var(--bg-panel);
  border-radius: var(--radius-lg);
  padding: 1.75rem 1.5rem;
  border: 1px solid var(--border);
}
h1 {
  margin: 0;
  font-size: 1.55rem;
}
.hint {
  color: var(--text-muted);
  font-size: 0.88rem;
  margin: 0.35rem 0 1rem;
}
.field-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.65rem;
}
@media (max-width: 480px) {
  .field-row {
    grid-template-columns: 1fr;
  }
}
.field.half {
  margin-bottom: 1rem;
}
.field select {
  width: 100%;
  padding: 0.65rem 0.85rem;
  border-radius: 10px;
  border: 1px solid var(--border);
  background: var(--bg-panel);
  color: var(--text);
  font-family: inherit;
}
.section-title {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--text-muted);
  margin: 1rem 0 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.35rem;
}
.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
}
.tag {
  border: 1px solid var(--border);
  background: var(--bg-page);
  border-radius: 999px;
  padding: 0.35rem 0.75rem;
  font-size: 0.82rem;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.2s;
  color: var(--text-muted);
}
.tag.on {
  border-color: var(--jn-maroon);
  background: var(--jn-maroon-soft);
  color: var(--jn-maroon);
  font-weight: 600;
}
.tag-hint {
  font-size: 0.78rem;
  color: var(--text-subtle);
  margin: 0.5rem 0 0;
}
.code-row {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}
.grow {
  flex: 1;
}
.grow input {
  width: 100%;
  padding: 0.65rem 0.85rem;
  border-radius: 10px;
  border: 1px solid var(--border);
  background: var(--bg-panel);
  color: var(--text);
  font-family: inherit;
}
.small-toast {
  padding: 0.45rem 0.75rem;
  font-size: 0.82rem;
}
.wide {
  width: 100%;
  margin-top: 1rem;
}
.foot {
  margin-top: 1.25rem;
  text-align: center;
  font-size: 0.88rem;
  color: var(--text-muted);
}
.tap-scale:active {
  transform: scale(0.98);
}
</style>
