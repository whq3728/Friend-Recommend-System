<script setup>
import { onMounted, ref } from "vue";
import { useRoute, RouterLink } from "vue-router";
import { api } from "../../api/client";
import { ChevronLeftIcon } from "@heroicons/vue/24/outline";

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
        <p><span class="k">昵称</span> {{ data.username }}</p>
        <p><span class="k">年级</span> {{ data.grade || "—" }}</p>
        <p><span class="k">专业</span> {{ data.major || "—" }}</p>
        <p v-if="data.stats">
          <span class="k">兴趣</span> {{ data.stats.interest_count }} 个 ·
          <span class="k">技能</span> {{ data.stats.skill_count }} 项
        </p>
        <button v-if="data.relation !== 'self'" type="button" class="btn btn-primary" @click="sendRequest">
          发起好友请求
        </button>
      </template>

      <template v-else-if="data.relation === 'friend'">
        <p><span class="k">昵称</span> {{ data.username }}</p>
        <p><span class="k">年级 / 专业</span> {{ data.grade }} / {{ data.major }}</p>
        <p><span class="k">兴趣</span> {{ (data.interests || []).join("、") || "—" }}</p>
        <p><span class="k">技能</span> {{ (data.skills || []).join("、") || "—" }}</p>
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
.row {
  margin-top: 1rem;
}
</style>
