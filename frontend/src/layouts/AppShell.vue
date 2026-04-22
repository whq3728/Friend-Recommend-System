<script setup>
import { onMounted, ref, onBeforeUnmount, watch } from "vue";
import { RouterLink, RouterView, useRouter, useRoute } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { api } from "../api/client";
import {
  BoltIcon,
  ChatBubbleLeftRightIcon,
  ClockIcon,
  LockClosedIcon,
  SparklesIcon,
  TrophyIcon,
  UserCircleIcon,
  UserGroupIcon,
} from "@heroicons/vue/24/outline";

const auth = useAuthStore();
const router = useRouter();
const route = useRoute();

const summary = ref(null);
let pollTimer;

// 顶栏摘要每分钟刷新一次，避免频繁请求
async function loadSummary() {
  try {
    summary.value = await api("/api/me/summary");
  } catch {
    summary.value = null;
  }
}

async function logout() {
  await auth.logout();
  router.push("/");
}

onMounted(() => {
  loadSummary();
  pollTimer = window.setInterval(loadSummary, 60000);
});

onBeforeUnmount(() => {
  if (pollTimer) window.clearInterval(pollTimer);
});

watch(
  () => route.path,
  (p) => {
    if (p.startsWith("/app")) loadSummary();
  },
);
</script>

<template>
  <div class="shell">
    <header class="top">
      <RouterLink to="/app/recommend" class="brand tap-scale">
        <span class="logo">JNU Link</span>
        <span class="tag">校园社交</span>
      </RouterLink>

      <nav class="nav" aria-label="主导航">
        <RouterLink to="/app/recommend"
          ><SparklesIcon class="h-ico" /> 推荐</RouterLink
        >
        <RouterLink to="/app/friends" class="nav-friends">
          <ChatBubbleLeftRightIcon class="h-ico" />
          好友
          <span v-if="summary?.pending_incoming_requests > 0" class="nav-badge">
            {{ summary.pending_incoming_requests > 9 ? "9+" : summary.pending_incoming_requests }}
          </span>
        </RouterLink>
        <RouterLink to="/app/history"
          ><ClockIcon class="h-ico" /> 记录</RouterLink
        >
        <RouterLink to="/app/profile"
          ><UserCircleIcon class="h-ico" /> 资料</RouterLink
        >
        <RouterLink to="/app/privacy"
          ><LockClosedIcon class="h-ico" /> 隐私</RouterLink
        >
      </nav>

      <div class="user">
        <div v-if="summary" class="stats-mini" title="活跃度与数据概览">
          <span class="pill"><BoltIcon class="h-ico" /> {{ summary.activity_score }}</span>
          <span class="pill"><UserGroupIcon class="h-ico" /> {{ summary.friend_count }}</span>
          <span class="pill"><TrophyIcon class="h-ico" /> {{ summary.recommend_runs }}</span>
        </div>
        <span class="name" v-if="auth.user">{{ auth.user.username }}</span>
        <button type="button" class="btn btn-ghost btn-sm tap-scale" @click="logout">退出</button>
      </div>
    </header>

    <main class="main">
      <RouterView v-slot="{ Component }">
        <Transition name="page-slide" mode="out-in">
          <component :is="Component" />
        </Transition>
      </RouterView>
    </main>
  </div>
</template>

<style scoped>
.shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-page);
}
.top {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.65rem 1rem;
  padding: 0.65rem 1rem;
  border-bottom: 1px solid var(--border);
  background: var(--bg-panel);
  box-shadow: var(--shadow);
  position: sticky;
  top: 0;
  z-index: 10;
}
.brand {
  display: flex;
  flex-direction: column;
  text-decoration: none;
  color: inherit;
}
.brand:hover {
  text-decoration: none;
}
.logo {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 1.15rem;
  color: var(--jn-maroon);
}
.tag {
  font-size: 0.68rem;
  color: var(--text-subtle);
}
.nav {
  display: flex;
  flex-wrap: wrap;
  gap: 0.2rem 0.35rem;
  flex: 1;
  justify-content: center;
}
.nav a {
  color: var(--text-muted);
  font-size: 0.82rem;
  text-decoration: none;
  padding: 0.38rem 0.6rem;
  border-radius: 10px;
  transition: color 0.2s, background 0.2s, transform 0.15s;
  position: relative;
}
.nav a:hover {
  color: var(--jn-maroon);
  background: var(--jn-maroon-soft);
}
.nav a.router-link-active {
  color: var(--jn-maroon);
  font-weight: 600;
  background: var(--jn-maroon-soft);
}
.nav-friends {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
}
.nav-badge {
  min-width: 1.1rem;
  height: 1.1rem;
  padding: 0 0.3rem;
  border-radius: 999px;
  background: var(--err);
  color: #fff;
  font-size: 0.65rem;
  font-weight: 800;
  line-height: 1.1rem;
  text-align: center;
}
.user {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  flex-wrap: wrap;
  justify-content: flex-end;
}
.stats-mini {
  display: none;
  gap: 0.25rem;
  flex-wrap: wrap;
}
@media (min-width: 900px) {
  .stats-mini {
    display: flex;
  }
}
.pill {
  font-size: 0.68rem;
  padding: 0.2rem 0.45rem;
  border-radius: 8px;
  background: var(--bg-page);
  border: 1px solid var(--border-light);
  color: var(--text-muted);
  font-weight: 600;
  white-space: nowrap;
}
.name {
  font-size: 0.85rem;
  color: var(--text-muted);
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.main {
  flex: 1;
  padding: 1rem 1.1rem 2rem;
  width: 100%;
}
@media (min-width: 640px) {
  .main {
    max-width: 960px;
    margin: 0 auto;
    padding: 1.25rem 1.5rem 2.5rem;
  }
}
@media (min-width: 1024px) {
  .main {
    max-width: 1200px;
    padding: 1.5rem 2rem 3rem;
  }
  .top {
    padding: 0.75rem 1.5rem;
  }
  .logo {
    font-size: 1.35rem;
  }
}

.page-slide-enter-active,
.page-slide-leave-active {
  transition: opacity 0.15s ease;
}
.page-slide-enter-from,
.page-slide-leave-to {
  opacity: 0;
}
.tap-scale:active {
  transform: scale(0.98);
}
</style>
