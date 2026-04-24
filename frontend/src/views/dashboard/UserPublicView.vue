<script setup>
import { onMounted, ref, computed } from "vue";
import { useRoute, RouterLink } from "vue-router";
import { api } from "../../api/client";
import { ChevronLeftIcon, PhoneIcon, UserIcon } from "@heroicons/vue/24/outline";

const props = defineProps({
  id: { type: String, default: "" },
});

const route = useRoute();
const uid = () => String(props.id || route.params.id || "");

const data = ref(null);
const err = ref("");

onMounted(async () => {
  try {
    data.value = await api(`/api/users/${uid()}/public`);
  } catch (e) {
    err.value = e instanceof Error ? e.message : "加载失败";
  }
});

const msg = ref("");

async function sendRequest() {
  msg.value = "";
  try {
    await api("/api/friend-requests", { method: "POST", body: { to_id: parseInt(uid(), 10) } });
    msg.value = "好友请求已发送";
  } catch (e) {
    msg.value = e instanceof Error ? e.message : "发送失败";
  }
}

const fields = computed(() => {
  if (!data.value) return [];
  const d = data.value;
  const result = [];

  // 基础信息
  if (d.phone && d.relation === "friend") {
    result.push({ label: "手机号", value: d.phone, icon: "phone" });
  }
  if (d.gender) {
    result.push({ label: "性别", value: d.gender, icon: "user" });
  }
  if (d.grade || d.major) {
    result.push({ label: "年级/专业", value: [d.grade, d.major].filter(Boolean).join(" / "), icon: "user" });
  }

  return result;
});

const tags = computed(() => {
  if (!data.value) return {};
  const d = data.value;
  const result = {};

  if (d.interests && d.interests.length > 0) {
    result.interests = d.interests;
  }
  if (d.skills && d.skills.length > 0) {
    result.skills = d.skills;
  }
  if (d.projects && d.projects.length > 0) {
    result.projects = d.projects;
  }
  if (d.traits && d.traits.length > 0) {
    result.traits = d.traits;
  }

  return result;
});

const showCount = computed(() => {
  if (!data.value) return {};
  const d = data.value;
  const result = {};

  if (d.stats) {
    if (d.stats.interest_count !== undefined) {
      result.interests = d.stats.interest_count;
    }
    if (d.stats.skill_count !== undefined) {
      result.skills = d.stats.skill_count;
    }
  } else {
    if (d.interest_count !== undefined) {
      result.interests = d.interest_count;
    }
    if (d.skill_count !== undefined) {
      result.skills = d.skill_count;
    }
  }

  return result;
});
</script>

<template>
  <div>
    <RouterLink to="/app/recommend" class="back"
      ><ChevronLeftIcon class="h-ico" /> 返回推荐</RouterLink
    >
    <h2>用户资料</h2>
    <div v-if="err" class="toast err">{{ err }}</div>
    <div v-if="msg" class="toast ok">{{ msg }}</div>
    <div v-if="data" class="panel">
      <template v-if="data.relation === 'stranger'">
        <p class="username">{{ data.username }}</p>
        <p v-if="data.gender"><span class="k">性别</span> {{ data.gender }}</p>
        <p v-if="data.grade"><span class="k">年级</span> {{ data.grade }}</p>
        <p v-if="data.major"><span class="k">专业</span> {{ data.major }}</p>

        <div v-if="data.interests && data.interests.length > 0" class="tag-section">
          <span class="k">兴趣</span>
          <div class="tags">
            <span v-for="tag in data.interests" :key="tag" class="tag interest">{{ tag }}</span>
          </div>
        </div>
        <div v-if="data.skills && data.skills.length > 0" class="tag-section">
          <span class="k">技能</span>
          <div class="tags">
            <span v-for="tag in data.skills" :key="tag" class="tag skill">{{ tag }}</span>
          </div>
        </div>

        <div v-if="Object.keys(showCount).length > 0 && (!data.interests || data.interests.length === 0)" class="stats-row">
          <span v-if="showCount.interests !== undefined">
            <span class="k">兴趣</span> {{ showCount.interests }} 个
          </span>
          <span v-if="showCount.skills !== undefined">
            <span class="k">技能</span> {{ showCount.skills }} 项
          </span>
        </div>

        <p v-if="data.privacy_note" class="privacy-note">{{ data.privacy_note }}</p>
        <button v-if="data.relation !== 'self'" type="button" class="btn btn-primary" @click="sendRequest">
          发起好友请求
        </button>
      </template>

      <template v-else-if="data.relation === 'friend'">
        <p class="username">{{ data.username }}</p>

        <template v-for="field in fields" :key="field.label">
          <p v-if="field.value">
            <span class="k">{{ field.label }}</span> {{ field.value }}
          </p>
        </template>

        <div v-for="(items, key) in tags" :key="key" class="tag-section">
          <span class="k">{{ key === 'interests' ? '兴趣' : key === 'skills' ? '技能' : key === 'projects' ? '项目' : '性格标签' }}</span>
          <div class="tags">
            <span
              v-for="tag in items"
              :key="tag"
              class="tag"
              :class="key === 'interests' ? 'interest' : key === 'skills' ? 'skill' : key === 'projects' ? 'project' : 'trait'"
            >{{ tag }}</span>
          </div>
        </div>

        <div class="row">
          <RouterLink class="btn btn-primary" :to="'/app/chat/' + data.id">发消息</RouterLink>
        </div>
      </template>

      <template v-else>
        <p>这是你的账号，去 <RouterLink to="/app/profile">资料</RouterLink> 编辑。</p>
      </template>
    </div>
  </div>
</template>

<style scoped>
.back {
  font-size: 0.9rem;
  color: var(--text-muted);
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}
.back:hover {
  color: var(--jn-maroon);
}
h2 {
  margin: 0.75rem 0 1rem;
}
.k {
  color: var(--text-muted);
  margin-right: 0.5rem;
  font-size: 0.88rem;
}
.username {
  font-size: 1.2rem;
  font-weight: 600;
  margin-bottom: 1rem;
}
.row {
  margin-top: 1rem;
}
.privacy-note {
  font-size: 0.82rem;
  color: var(--text-subtle);
  background: var(--bg-page);
  padding: 0.75rem;
  border-radius: var(--radius);
  margin: 1rem 0;
}
.tag-section {
  margin: 0.75rem 0;
}
.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-top: 0.35rem;
}
.tag {
  display: inline-block;
  padding: 0.25rem 0.65rem;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 500;
}
.tag.interest {
  background: rgba(59, 130, 246, 0.12);
  color: #2563eb;
}
.tag.skill {
  background: rgba(5, 150, 105, 0.12);
  color: #047857;
}
.tag.project {
  background: rgba(139, 92, 246, 0.12);
  color: #6d28d9;
}
.tag.trait {
  background: rgba(245, 158, 11, 0.12);
  color: #d97706;
}
.stats-row {
  font-size: 0.88rem;
  margin: 0.5rem 0;
}
</style>
