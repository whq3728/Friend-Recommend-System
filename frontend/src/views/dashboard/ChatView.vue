<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch, nextTick } from "vue";
import { useRoute, RouterLink } from "vue-router";
import { api } from "../../api/client";
import { useAuthStore } from "../../stores/auth";
import { ChevronLeftIcon, FaceSmileIcon } from "@heroicons/vue/24/outline";

const props = defineProps({
  peerId: { type: String, default: "" },
});

const route = useRoute();
const auth = useAuthStore();

const pid = computed(() => String(props.peerId || route.params.peerId || ""));

const stream = ref([]);
const body = ref("");
const err = ref("");
const peerName = ref("");
const lastActive = ref(null);
const sending = ref(false);
const showEmoji = ref(false);
const unreadFromPeer = ref(0);

const EMOJIS = ["😀", "😂", "🥰", "👍", "🎉", "💪", "☕", "📚", "✨", "🙏"];

let maxId = 0;
let timer;

function readStorageKey() {
  const me = auth.user?.id;
  if (!me || !pid.value) return null;
  return `jnu_chat_read_${me}_${pid.value}`;
}

function loadLastRead() {
  const k = readStorageKey();
  if (!k) return 0;
  try {
    return parseInt(localStorage.getItem(k) || "0", 10) || 0;
  } catch {
    return 0;
  }
}

function saveLastRead(id) {
  const k = readStorageKey();
  if (k) localStorage.setItem(k, String(id));
}

function markRead() {
  if (!maxId) return;
  saveLastRead(maxId);
  unreadFromPeer.value = 0;
}

function apiUrl(suffix = "") {
  return `/api/chat/${pid.value}/messages${suffix}`;
}

async function loadInitial() {
  err.value = "";
  try {
    const list = await api(apiUrl());
    stream.value = Array.isArray(list) ? list : [];
    maxId = stream.value.reduce((m, x) => Math.max(m, x.id || 0), 0);
    const lr = loadLastRead();
    unreadFromPeer.value = stream.value.filter(
      (m) => m.sender_id !== auth.user?.id && m.id > lr,
    ).length;
    await nextTick();
    scrollToBottom(false);
  } catch (e) {
    err.value = e instanceof Error ? e.message : "无法加载会话";
  }
}

async function poll() {
  // 仅拉取 after_id 之后的增量消息，降低轮询开销
  if (maxId <= 0) return;
  try {
    const list = await api(`${apiUrl("?after_id=")}${maxId}`);
    if (!Array.isArray(list) || !list.length) return;
    const lr = loadLastRead();
    for (const m of list) {
      stream.value.push(m);
      maxId = Math.max(maxId, m.id);
      if (m.sender_id !== auth.user?.id && m.id > lr) {
        unreadFromPeer.value += 1;
      }
    }
    await nextTick();
    scrollToBottom(true);
  } catch {
    /* 忽略 */
  }
}

async function send() {
  const t = body.value.trim();
  if (!t || sending.value) return;
  err.value = "";
  sending.value = true;
  showEmoji.value = false;
  try {
    const m = await api(apiUrl(), { method: "POST", body: { body: t } });
    body.value = "";
    stream.value.push(m);
    maxId = Math.max(maxId, m.id);
    markRead();
    await nextTick();
    scrollToBottom(true);
  } catch (e) {
    err.value = e instanceof Error ? e.message : "发送失败";
  } finally {
    sending.value = false;
  }
}

function insertEmoji(e) {
  body.value += e;
  showEmoji.value = false;
}

function mine(m) {
  return auth.user && m.sender_id === auth.user.id;
}

function onVis() {
  if (document.visibilityState === "visible") poll();
}

const groupedStream = computed(() => {
  const list = stream.value;
  if (!list.length) return [];
  const groups = [];
  let currentDate = "";
  for (const m of list) {
    const dt = m.created_at ? m.created_at.slice(0, 10) : "";
    if (dt !== currentDate) {
      currentDate = dt;
      groups.push({ type: "divider", date: dt, label: formatDateLabel(dt) });
    }
    groups.push({ type: "msg", ...m });
  }
  return groups;
});

function formatDateLabel(iso) {
  if (!iso) return "";
  const d = new Date(iso + "T12:00:00");
  const today = new Date();
  const t0 = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  const d0 = new Date(d.getFullYear(), d.getMonth(), d.getDate());
  const diffDays = Math.round((t0 - d0) / 86400000);
  if (diffDays === 0) return "今天";
  if (diffDays === 1) return "昨天";
  if (diffDays < 7) return `${diffDays} 天前`;
  if (d.getFullYear() === today.getFullYear()) return `${d.getMonth() + 1}月${d.getDate()}日`;
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日`;
}

function formatLastActive(ts) {
  if (!ts) return null;
  const d = new Date(ts);
  const now = new Date();
  const diff = Math.floor((now - d) / 1000);
  if (diff < 60) return "刚刚活跃";
  if (diff < 3600) return `${Math.floor(diff / 60)} 分钟前活跃`;
  if (diff < 86400) return `${Math.floor(diff / 3600)} 小时前活跃`;
  return `${d.getMonth() + 1}/${d.getDate()} 最后活跃`;
}

function onKeydown(e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    send();
  }
}

const streamEl = ref(null);

function scrollToBottom(smooth) {
  const el = streamEl.value;
  if (!el) return;
  el.scrollTo({
    top: el.scrollHeight,
    behavior: smooth ? "smooth" : "auto",
  });
}

watch(
  () => stream.value.length,
  () => nextTick(() => scrollToBottom(true)),
);

onMounted(async () => {
  await loadInitial();
  try {
    const u = await api(`/api/users/${pid.value}/public`);
    peerName.value = u.username || "用户 " + pid.value;
  } catch {
    peerName.value = "用户 " + pid.value;
  }
  try {
    const info = await api(`/api/chat/${pid.value}/info`);
    lastActive.value = info?.last_message_from_peer_at || null;
  } catch {
    lastActive.value = null;
  }
  timer = setInterval(poll, 2500);
  document.addEventListener("visibilitychange", onVis);
});

onBeforeUnmount(() => {
  clearInterval(timer);
  document.removeEventListener("visibilitychange", onVis);
  saveLastRead(maxId);
});
</script>

<template>
  <div class="chat">
    <header class="top">
      <RouterLink class="back" to="/app/friends"><ChevronLeftIcon class="h-ico" /> 好友</RouterLink>
      <div class="peer-block">
        <h2>
          {{ peerName }}
          <span v-if="unreadFromPeer > 0" class="unread-dot" :title="`${unreadFromPeer} 条未读`" />
        </h2>
        <p class="uid">ID {{ pid }}</p>
        <p v-if="formatLastActive(lastActive)" class="last-active">{{ formatLastActive(lastActive) }}</p>
      </div>
    </header>
    <div v-if="err" class="toast err chat-err">{{ err }}</div>
    <div ref="streamEl" class="stream">
      <div class="stream-inner">
        <template v-for="(item, i) in groupedStream" :key="item.type === 'divider' ? 'd-' + item.date + '-' + i : item.id">
          <div v-if="item.type === 'divider'" class="divider">
            <span>{{ item.label }}</span>
          </div>
          <div v-else class="bubble-wrap" :class="mine(item) ? 'end' : 'start'">
            <div class="bubble" :class="mine(item) ? 'me' : 'they'">
              <div class="txt">{{ item.body }}</div>
              <div class="meta">{{ item.created_at?.slice(11, 16) }}</div>
            </div>
          </div>
        </template>
      </div>
    </div>

    <div v-show="showEmoji" class="emoji-bar">
      <button v-for="e in EMOJIS" :key="e" type="button" class="emoji-btn" @click="insertEmoji(e)">{{ e }}</button>
    </div>

    <form class="compose" @submit.prevent="send">
      <button
        type="button"
        class="btn btn-ghost btn-icon tap-scale"
        title="表情"
        aria-label="打开表情选择"
        @click="showEmoji = !showEmoji"
      >
        <FaceSmileIcon class="h-ico" />
      </button>
      <textarea
        v-model="body"
        rows="2"
        maxlength="4000"
        placeholder="Enter 发送 · Shift+Enter 换行"
        :disabled="sending"
        @focus="markRead"
        @keydown="onKeydown"
      ></textarea>
      <button type="submit" class="btn btn-primary tap-scale" :disabled="sending || !body.trim()">
        {{ sending ? "…" : "发送" }}
      </button>
    </form>
  </div>
</template>

<style scoped>
.chat {
  max-width: 100%;
  margin: 0 auto;
  width: 100%;
  display: flex;
  flex-direction: column;
  /* 占满主区域高度，消息区内部滚动，底部输入框始终留在视口内 */
  /* 顶栏 + main 上下 padding，避免整块超出视口 */
  height: calc(100dvh - 8rem);
  max-height: calc(100dvh - 8rem);
  min-height: 260px;
}
@media (min-width: 768px) {
  .chat {
    max-width: 640px;
  }
}
.top {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 0.75rem;
  flex-shrink: 0;
}
.back {
  color: var(--text-muted);
  font-size: 0.9rem;
  white-space: nowrap;
  padding-top: 0.2rem;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}
.back:hover {
  color: var(--jn-maroon);
}
.peer-block h2 {
  margin: 0;
  font-size: 1.15rem;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}
.unread-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--err);
  border: 2px solid var(--bg-panel);
}
.uid {
  margin: 0.2rem 0 0;
  font-size: 0.82rem;
  color: var(--text-subtle);
}
.last-active {
  margin: 0.15rem 0 0;
  font-size: 0.78rem;
  color: var(--text-subtle);
}
.chat-err {
  flex-shrink: 0;
  margin-bottom: 0.5rem;
}
.stream {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 1rem;
  background: var(--bg-panel);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  margin-bottom: 0.5rem;
  scroll-behavior: smooth;
}
.stream-inner {
  min-height: 40px;
}
.divider {
  display: flex;
  justify-content: center;
  margin: 1rem 0 0.65rem;
}
.divider span {
  font-size: 0.72rem;
  color: var(--text-subtle);
  padding: 0.2rem 0.75rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid var(--border-light);
}
.divider:first-child {
  margin-top: 0;
}
.bubble-wrap {
  display: flex;
  margin-bottom: 0.55rem;
}
.bubble-wrap.start {
  justify-content: flex-start;
}
.bubble-wrap.end {
  justify-content: flex-end;
}
.bubble {
  max-width: 85%;
  padding: 0.55rem 0.9rem;
  border-radius: 16px;
  font-size: 0.94rem;
  border: 1px solid transparent;
  word-break: break-word;
  overflow-wrap: break-word;
}
.bubble.me {
  background: linear-gradient(135deg, #8b1538, #a91d47);
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.15);
}
.bubble.me .meta {
  color: rgba(255, 255, 255, 0.75);
}
.bubble.they {
  background: linear-gradient(145deg, #ffffff, #f8fafc);
  border: 1px solid var(--border);
}
.meta {
  font-size: 0.7rem;
  color: var(--text-subtle);
  margin-top: 0.25rem;
}
.emoji-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  padding: 0.5rem 0 0.5rem;
  flex-shrink: 0;
  position: relative;
  z-index: 1;
}
.emoji-btn {
  border: 1px solid var(--border);
  background: var(--bg-panel);
  border-radius: 10px;
  font-size: 1.25rem;
  padding: 0.25rem 0.45rem;
  cursor: pointer;
  line-height: 1;
}
.emoji-btn:hover {
  background: var(--jn-maroon-soft);
}
.compose {
  display: flex;
  gap: 0.45rem;
  align-items: flex-end;
  flex-shrink: 0;
  padding-bottom: env(safe-area-inset-bottom, 0);
}
.btn-icon {
  padding: 0.5rem 0.65rem;
  font-size: 1.1rem;
}
.compose textarea {
  flex: 1;
  padding: 0.6rem 0.85rem;
  border-radius: 12px;
  border: 1px solid var(--border);
  background: var(--bg-panel);
  color: var(--text);
  font-family: inherit;
  resize: vertical;
  min-height: 48px;
}
.tap-scale:active {
  transform: scale(0.96);
}
</style>
