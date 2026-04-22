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

const PRESET_SKILLS = [
  "Python",
  "Java",
  "C++",
  "前端开发",
  "数据库",
  "数据分析",
  "机器学习",
  "英语表达",
  "PPT制作",
  "写作表达",
  "摄影",
  "设计绘画",
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
const selectedSkills = ref([]);
const personalityMode = ref("skip"); // skip | quick | questionnaire

// 快速选择：每维 1..5
const bigfiveQuick = ref({
  extro: 3,
  agreeableness: 3,
  conscientiousness: 3,
  neuroticism: 3,
  openness: 3,
});

// 问卷：10 题，每题 1..5（Likert）
const questionnaire = ref([3, 3, 3, 3, 3, 3, 3, 3, 3, 3]);

const BIG5_QUESTIONS = [
  "我在社交场合中通常更愿意主动交流。",
  "我更喜欢热闹的活动而不是独处。",
  "我通常愿意体谅他人、站在对方角度考虑。",
  "当我和别人意见不同时，我更倾向于妥协而不是争辩。",
  "我做事通常有计划，并能按时完成。",
  "我会认真对待细节，尽量避免粗心。",
  "我经常会因为小事而担心或烦恼。",
  "遇到压力时，我容易出现情绪波动。",
  "我喜欢尝试新事物和新的观点。",
  "我对不同领域的想法保持好奇心。",
];

const err = ref("");
const ok = ref(false);
const sending = ref(false);
const smsHint = ref("");
const countdown = ref(0); // 倒计时秒数
let countdownTimer = null;

const bindPhone = computed(() => phone.value.replace(/\s/g, "").length >= 11);

function toggleTag(t) {
  const i = selectedTags.value.indexOf(t);
  if (i >= 0) selectedTags.value = selectedTags.value.filter((x) => x !== t);
  else if (selectedTags.value.length < 12) selectedTags.value = [...selectedTags.value, t];
}

function toggleSkill(t) {
  const i = selectedSkills.value.indexOf(t);
  if (i >= 0) selectedSkills.value = selectedSkills.value.filter((x) => x !== t);
  else if (selectedSkills.value.length < 12) selectedSkills.value = [...selectedSkills.value, t];
}

async function sendCode() {
  err.value = "";
  smsHint.value = "";
  sending.value = true;
  try {
    const res = await auth.sendSms(phone.value.trim().replace(/\s/g, ""));
    if (res?.remaining_seconds) {
      // 被限流，显示倒计时
      startCountdown(res.remaining_seconds);
      err.value = `发送太频繁，请 ${res.remaining_seconds} 秒后再试`;
    } else {
      smsHint.value = res?.hint || "验证码已发送";
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
      skills: [...selectedSkills.value],
      sms_code: bindPhone.value ? smsCode.value.trim() : "",
      personality_mode: personalityMode.value,
      bigfive_quick:
        personalityMode.value === "quick"
          ? bigfiveQuick.value
          : {},
      bigfive_answers: personalityMode.value === "questionnaire" ? [...questionnaire.value] : [],
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

        <div class="section-title">🧠 性格测试（Big Five，支持跳过）</div>
        <div class="field-row">
          <div class="field half">
            <label>选择方式</label>
            <select v-model="personalityMode">
              <option value="skip">跳过（稍后填写也可以）</option>
              <option value="quick">快速选择（5 维各选 1..5）</option>
              <option value="questionnaire">问卷（10 题 Likert 1..5）</option>
            </select>
          </div>
        </div>

        <div v-if="personalityMode === 'quick'" class="bigfive-quick">
          <p class="tag-hint">快速选择：1 表示完全不符合，5 表示非常符合。</p>
          <div class="field-row">
            <div class="field half">
              <label>外向性 Extroversion</label>
              <select v-model="bigfiveQuick.extro">
                <option v-for="n in 5" :key="'e' + n" :value="n">{{ n }}</option>
              </select>
            </div>
            <div class="field half">
              <label>宜人性 Agreeableness</label>
              <select v-model="bigfiveQuick.agreeableness">
                <option v-for="n in 5" :key="'a' + n" :value="n">{{ n }}</option>
              </select>
            </div>
          </div>
          <div class="field-row">
            <div class="field half">
              <label>尽责性 Conscientiousness</label>
              <select v-model="bigfiveQuick.conscientiousness">
                <option v-for="n in 5" :key="'c' + n" :value="n">{{ n }}</option>
              </select>
            </div>
            <div class="field half">
              <label>神经质 Neuroticism</label>
              <select v-model="bigfiveQuick.neuroticism">
                <option v-for="n in 5" :key="'n' + n" :value="n">{{ n }}</option>
              </select>
            </div>
          </div>
          <div class="field-row">
            <div class="field">
              <label>开放性 Openness</label>
              <select v-model="bigfiveQuick.openness">
                <option v-for="n in 5" :key="'o' + n" :value="n">{{ n }}</option>
              </select>
            </div>
          </div>
        </div>

        <div v-else-if="personalityMode === 'questionnaire'" class="bigfive-q">
          <p class="tag-hint">问卷（10 题）。选择最符合你的选项。</p>
          <div class="q-list">
            <div v-for="(q, idx) in BIG5_QUESTIONS" :key="'q' + idx" class="q-item">
              <div class="q-text">{{ idx + 1 }}. {{ q }}</div>
              <select v-model="questionnaire[idx]">
                <option v-for="n in 5" :key="'v' + idx + '_' + n" :value="n">{{ n }}</option>
              </select>
            </div>
          </div>
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

        <div class="section-title">🧩 技能标签（可多选）</div>
        <div class="tags">
          <button
            v-for="t in PRESET_SKILLS"
            :key="t"
            type="button"
            class="tag"
            :class="{ on: selectedSkills.includes(t) }"
            @click="toggleSkill(t)"
          >
            {{ t }}
          </button>
        </div>
        <p class="tag-hint">已选 {{ selectedSkills.length }} 个，可随时在资料页修改</p>

        <div class="section-title">
          <DevicePhoneMobileIcon class="h-ico" /> 手机号（可选，用于验证码登录与找回密码）
        </div>
        <div class="field code-row">
          <div class="grow">
            <input v-model="phone" inputmode="numeric" maxlength="11" placeholder="不填则仅用账号密码登录" />
          </div>
          <button type="button" class="btn btn-ghost btn-sm" :disabled="sending || !bindPhone || countdown > 0" @click="sendCode">
            {{ countdown > 0 ? `${countdown}s` : sending ? "发送中…" : "获取验证码" }}
          </button>
        </div>
        <div v-if="bindPhone" class="field">
          <input v-model="smsCode" maxlength="6" inputmode="numeric" placeholder="请输入6位验证码" />
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

.bigfive-q .q-list {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  margin: 0.5rem 0 1rem;
}

.q-item {
  background: var(--bg-page);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 0.75rem;
}

.q-text {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin-bottom: 0.4rem;
  line-height: 1.5;
}
</style>
