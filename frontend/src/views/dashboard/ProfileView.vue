<script setup>
import { onMounted, reactive, ref, computed } from "vue";
import { api } from "../../api/client";

const loading = ref(true);
const err = ref("");
const ok = ref("");
const form = reactive({
  id: "",
  account: "",
  username: "",
  password: "",
  gender: "",
  grade: "",
  major: "",
  phone: "",
  interests: "",
  skills: "",
  projects: "",
  traits: "",
});

function lines(arr) {
  return (arr || []).join("\n");
}

function parseList(text) {
  return text
    .split(/[\n,，]/)
    .map((s) => s.trim())
    .filter(Boolean);
}

/** 资料完善度：已填写的核心字段占比 */
const completeness = computed(() => {
  const fields = [
    form.username,
    form.gender,
    form.grade,
    form.major,
    form.interests,
    form.skills,
  ];
  const filled = fields.filter((v) => v && String(v).trim()).length;
  return Math.round((filled / fields.length) * 100);
});

onMounted(async () => {
  try {
    const p = await api("/api/profile");
    form.id = String(p.id);
    form.account = p.account || "";
    form.username = p.username || "";
    form.gender = p.gender || "";
    form.grade = p.grade || "";
    form.major = p.major || "";
    form.phone = p.phone || "";
    form.interests = lines(p.interests);
    form.skills = lines(p.skills);
    form.projects = lines(p.projects);
    form.traits = lines(p.traits);
  } catch (e) {
    err.value = e instanceof Error ? e.message : "加载失败";
  } finally {
    loading.value = false;
  }
});

async function save() {
  err.value = "";
  ok.value = "";
  try {
    const body = {
      username: form.username.trim(),
      gender: form.gender.trim(),
      grade: form.grade.trim(),
      major: form.major.trim(),
      phone: form.phone.trim().replace(/\s/g, ""),
      interests: parseList(form.interests),
      skills: parseList(form.skills),
      projects: parseList(form.projects),
      traits: parseList(form.traits),
    };
    if (form.password.trim()) body.password = form.password.trim();
    await api("/api/profile", { method: "PUT", body });
    form.password = "";
    ok.value = "已保存";
  } catch (e) {
    err.value = e instanceof Error ? e.message : "保存失败";
  }
}
</script>

<template>
  <div>
    <h2>个人信息</h2>
    <p class="sub">完善资料有助于获得更合适的推荐</p>
    <div v-if="err" class="toast err">{{ err }}</div>
    <div v-if="ok" class="toast ok">{{ ok }}</div>
    <p v-if="loading" class="muted">加载中…</p>
    <div v-else class="panel">
      <!-- 资料完善度 -->
      <div class="progress-wrap" v-if="completeness < 100">
        <div class="progress-label">
          <span>资料完善度</span>
          <span class="pct">{{ completeness }}%</span>
        </div>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: completeness + '%' }"></div>
        </div>
        <p class="progress-hint">完善昵称、年级、专业、兴趣和技能可获得更好推荐</p>
      </div>

      <p class="note">用户 ID 用于添加好友时查找；登录账号不可修改，昵称可改。</p>
      <div class="field">
        <label>用户 ID</label>
        <input v-model="form.id" readonly class="ro" />
      </div>
      <div class="field">
        <label>登录账号</label>
        <input v-model="form.account" readonly class="ro" />
      </div>
      <div class="field">
        <label>手机号（可选，用于验证码登录与找回密码）</label>
        <input v-model="form.phone" inputmode="tel" maxlength="20" placeholder="未绑定可在此补充" />
      </div>
      <div class="field">
        <label>昵称</label>
        <input v-model="form.username" maxlength="64" required />
      </div>
      <div class="field">
        <label>新密码（留空不改）</label>
        <input v-model="form.password" type="password" autocomplete="new-password" />
      </div>
      <div class="field">
        <label>性别</label>
        <input v-model="form.gender" placeholder="男 / 女 / 其他" />
      </div>
      <div class="field">
        <label>年级</label>
        <input v-model="form.grade" placeholder="如：大一、研二" />
      </div>
      <div class="field">
        <label>专业</label>
        <input v-model="form.major" placeholder="如：计算机科学与技术" />
      </div>
      <div class="field">
        <label>兴趣（每行一条）</label>
        <textarea v-model="form.interests" rows="4" placeholder="如：音乐、运动、编程"></textarea>
      </div>
      <div class="field">
        <label>技能</label>
        <textarea v-model="form.skills" rows="4" placeholder="如：Python、设计、PPT"></textarea>
      </div>
      <div class="field">
        <label>项目 / 比赛</label>
        <textarea v-model="form.projects" rows="3" placeholder="如：大创、比赛 A"></textarea>
      </div>
      <div class="field">
        <label>性格标签（恋爱推荐用）</label>
        <textarea v-model="form.traits" rows="3" placeholder="如：开朗、稳重"></textarea>
      </div>
      <button type="button" class="btn btn-primary" @click="save">保存</button>
    </div>
  </div>
</template>

<style scoped>
h2 {
  margin: 0 0 0.35rem;
}
.sub {
  color: var(--text-muted);
  font-size: 0.9rem;
  margin: 0 0 1rem;
}
.progress-wrap {
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: var(--bg-page);
  border-radius: var(--radius);
  border: 1px solid var(--border-light);
}
.progress-label {
  display: flex;
  justify-content: space-between;
  font-size: 0.88rem;
  margin-bottom: 0.5rem;
}
.pct {
  font-weight: 600;
  color: var(--jn-maroon);
}
.progress-bar {
  height: 6px;
  background: var(--border);
  border-radius: 3px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--jn-maroon), var(--jn-gold));
  border-radius: 3px;
  transition: width 0.3s;
}
.progress-hint {
  font-size: 0.8rem;
  color: var(--text-subtle);
  margin: 0.5rem 0 0;
}
.note {
  font-size: 0.88rem;
  color: var(--text-muted);
  margin: 0 0 1.25rem;
}
.ro {
  opacity: 0.9;
  cursor: not-allowed;
  background: var(--bg-page) !important;
}
.muted {
  color: var(--text-muted);
}
</style>
