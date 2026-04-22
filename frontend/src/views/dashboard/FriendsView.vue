<script setup>
import { onMounted, ref, computed, onBeforeUnmount } from "vue";
import { RouterLink } from "vue-router";
import { useVirtualizer } from "@tanstack/vue-virtual";
import { api } from "../../api/client";
import { useUiStore } from "../../stores/ui";
import {
  AcademicCapIcon,
  ChatBubbleLeftRightIcon,
  ClockIcon,
  InboxIcon,
  LightBulbIcon,
  PaperAirplaneIcon,
  SparklesIcon,
  StarIcon,
  UserPlusIcon,
  UsersIcon,
} from "@heroicons/vue/24/outline";

const VIRT_FRIEND_THRESHOLD = 7;
const FRIEND_ROW_ESTIMATE = 236;

const ui = useUiStore();

const friends = ref([]);
const incoming = ref([]);
const outgoing = ref([]);
const err = ref("");
const msg = ref("");
const friendId = ref("");

const swipeState = ref(null);
let sx = 0;

const stats = computed(() => ({
  friends: friends.value.length,
  pending: incoming.value.length,
  outgoing_count: outgoing.value.length,
}));

async function refresh() {
  err.value = "";
  try {
    const [f, inc, out] = await Promise.all([
      api("/api/friends"),
      api("/api/friend-requests/incoming"),
      api("/api/friend-requests/outgoing"),
    ]);
    friends.value = f;
    incoming.value = inc;
    outgoing.value = out;
  } catch (e) {
    err.value = e instanceof Error ? e.message : "加载失败";
  }
}

onMounted(refresh);

async function accept(id) {
  msg.value = "";
  try {
    await api(`/api/friend-requests/${id}/accept`, { method: "POST" });
    ui.toast("已同意，新朋友已加入列表", "ok");
    await refresh();
  } catch (e) {
    ui.toast(e instanceof Error ? e.message : "操作失败", "err");
  }
}

async function reject(id) {
  msg.value = "";
  try {
    await api(`/api/friend-requests/${id}/reject`, { method: "POST" });
    ui.toast("已拒绝该请求", "ok");
    await refresh();
  } catch (e) {
    ui.toast(e instanceof Error ? e.message : "操作失败", "err");
  }
}

async function quickAdd() {
  msg.value = "";
  try {
    const id = parseInt(String(friendId.value), 10);
    if (!id) throw new Error("请输入有效 ID");
    await api("/api/friends/add", { method: "POST", body: { friend_id: id } });
    friendId.value = "";
    ui.toast("已建立双向好友关系", "ok");
    await refresh();
  } catch (e) {
    ui.toast(e instanceof Error ? e.message : "添加失败", "err");
  }
}

function formatSince(ts) {
  if (!ts) return "—";
  const d = new Date(ts);
  const now = new Date();
  const diff = now - d;
  if (diff < 86400000) return "今天成为好友";
  if (diff < 604800000) return `${Math.floor(diff / 86400000)} 天前成为好友`;
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")} 成为好友`;
}

function genderIcon(g) {
  if (g === "男") return "♂️";
  if (g === "女") return "♀️";
  return "✨";
}

function onlineLabel(s) {
  if (s === "online") return { text: "在线", cls: "on" };
  if (s === "away") return { text: "离开", cls: "away" };
  return { text: "离线", cls: "off" };
}

function badgeLabel(key) {
  if (key === "recent_chat") return { icon: ChatBubbleLeftRightIcon, text: "最近互动" };
  if (key === "social_star") return { icon: StarIcon, text: "圈子活跃" };
  return { icon: SparklesIcon, text: key };
}

function reqTouchStart(e, r) {
  sx = e.touches[0].clientX;
  swipeState.value = { id: r.id, dx: 0 };
}

function reqTouchMove(e) {
  if (!swipeState.value) return;
  swipeState.value = {
    ...swipeState.value,
    dx: e.touches[0].clientX - sx,
  };
}

function reqTouchEnd(r) {
  if (!swipeState.value) return;
  const dx = swipeState.value.dx || 0;
  swipeState.value = null;
  if (dx > 70) accept(r.id);
  else if (dx < -70) reject(r.id);
}

onBeforeUnmount(() => {
  swipeState.value = null;
});

const friendsScrollEl = ref(null);
const friendVirtualizer = useVirtualizer(
  computed(() => ({
    count: friends.value.length,
    getScrollElement: () => friendsScrollEl.value,
    estimateSize: () => FRIEND_ROW_ESTIMATE,
    overscan: 4,
  })),
);
</script>

<template>
  <div class="friends-page">
    <h2><UsersIcon class="h-ico" /> 好友与请求</h2>
    <p class="sub">收到请求可右滑同意、左滑拒绝；与好友最近聊过会显示小徽章</p>
    <div v-if="err" class="toast err">{{ err }}</div>
    <div v-if="msg" class="toast ok">{{ msg }}</div>

    <div class="stats-bar">
      <span class="stat"> <strong>{{ stats.friends }}</strong> 位好友 </span>
      <span class="stat stat-pending">
        <strong>{{ stats.pending }}</strong> 条待处理
        <span v-if="stats.pending > 0" class="dot-new" aria-hidden="true" />
      </span>
      <span class="stat"> <strong>{{ stats.outgoing_count }}</strong> 等待通过 </span>
    </div>

    <section class="panel req-panel">
      <h3><InboxIcon class="h-ico" /> 待处理请求</h3>
      <p v-if="!incoming.length" class="muted">
        暂无，去<RouterLink to="/app/recommend">推荐页</RouterLink>看看吧
      </p>
      <div v-else class="req-swipe-list">
        <p class="swipe-tip"><LightBulbIcon class="h-ico" /> 在卡片上右滑同意 · 左滑拒绝</p>
        <div
          v-for="r in incoming"
          :key="r.id"
          class="req-card-wrap"
          @touchstart="reqTouchStart($event, r)"
          @touchmove="reqTouchMove"
          @touchend="reqTouchEnd(r)"
        >
          <div
            class="req-card"
            :style="{ transform: swipeState?.id === r.id ? `translateX(${swipeState.dx}px)` : undefined }"
          >
            <div class="req-main">
              <span class="req-name">{{ r.from_username }}</span>
              <span class="uid">#{{ r.from_id }}</span>
            </div>
            <div class="req-btns">
              <button type="button" class="btn btn-ghost btn-sm" @click="reject(r.id)">拒绝</button>
              <button type="button" class="btn btn-primary btn-sm" @click="accept(r.id)">同意</button>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="panel">
      <h3><PaperAirplaneIcon class="h-ico" /> 我发出的请求</h3>
      <p v-if="!outgoing.length" class="muted">暂无</p>
      <ul v-else class="list flat">
        <li v-for="r in outgoing" :key="r.id">
          <span><ClockIcon class="h-ico" /> {{ r.to_username }}</span>
          <span class="uid">#{{ r.to_id }}</span>
        </li>
      </ul>
    </section>

    <section class="panel">
      <h3><SparklesIcon class="h-ico" /> 我的好友</h3>
      <p v-if="!friends.length" class="muted guide">
        暂无好友，去<RouterLink to="/app/recommend">推荐页</RouterLink>匹配吧
      </p>
      <p v-else-if="friends.length >= VIRT_FRIEND_THRESHOLD" class="virt-hint">
        好友较多时仅渲染可视区域，滚动浏览更流畅
      </p>
      <div v-if="friends.length && friends.length < VIRT_FRIEND_THRESHOLD" class="friend-cards">
        <div v-for="u in friends" :key="u.id" class="friend-card">
          <div class="friend-top">
            <div class="avatar">{{ u.username?.slice(0, 1) || "?" }}</div>
            <div class="friend-meta">
              <span class="name">{{ genderIcon(u.gender) }} {{ u.username }}</span>
              <span class="uid">#{{ u.id }}</span>
              <span v-if="u.grade" class="grade"
                ><AcademicCapIcon class="h-ico" /> {{ u.grade }}</span
              >
              <span class="since"
                ><ClockIcon class="h-ico" /> {{ formatSince(u.friend_since) }}</span
              >
              <span v-if="u.online_status" class="online" :class="onlineLabel(u.online_status).cls">
                {{ onlineLabel(u.online_status).text }}
              </span>
            </div>
          </div>
          <div v-if="u.badges?.length" class="badges">
            <span v-for="b in u.badges" :key="b" class="badge">
              <component :is="badgeLabel(b).icon" class="h-ico" />
              {{ badgeLabel(b).text }}
            </span>
          </div>
          <div class="card-actions">
            <RouterLink class="btn btn-ghost btn-sm" :to="'/app/user/' + u.id">资料</RouterLink>
            <RouterLink class="btn btn-primary btn-sm" :to="'/app/chat/' + u.id">聊天</RouterLink>
          </div>
        </div>
      </div>
      <div
        v-else-if="friends.length"
        ref="friendsScrollEl"
        class="friend-virt-scroll"
      >
        <div
          class="friend-virt-inner"
          :style="{ height: `${friendVirtualizer.getTotalSize()}px`, position: 'relative', width: '100%' }"
        >
          <div
            v-for="v in friendVirtualizer.getVirtualItems()"
            :key="v.key"
            class="friend-virt-row"
            :style="{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              transform: `translateY(${v.start}px)`,
            }"
          >
            <div v-if="friends[v.index]" class="friend-card">
              <div class="friend-top">
                <div class="avatar">{{ friends[v.index].username?.slice(0, 1) || "?" }}</div>
                <div class="friend-meta">
                  <span class="name">{{ genderIcon(friends[v.index].gender) }} {{ friends[v.index].username }}</span>
                  <span class="uid">#{{ friends[v.index].id }}</span>
                  <span v-if="friends[v.index].grade" class="grade"
                    ><AcademicCapIcon class="h-ico" /> {{ friends[v.index].grade }}</span
                  >
                  <span class="since"
                    ><ClockIcon class="h-ico" /> {{ formatSince(friends[v.index].friend_since) }}</span
                  >
                  <span
                    v-if="friends[v.index].online_status"
                    class="online"
                    :class="onlineLabel(friends[v.index].online_status).cls"
                  >
                    {{ onlineLabel(friends[v.index].online_status).text }}
                  </span>
                </div>
              </div>
              <div v-if="friends[v.index].badges?.length" class="badges">
                <span v-for="b in friends[v.index].badges" :key="b" class="badge">
                  <component :is="badgeLabel(b).icon" class="h-ico" />
                  {{ badgeLabel(b).text }}
                </span>
              </div>
              <div class="card-actions">
                <RouterLink class="btn btn-ghost btn-sm" :to="'/app/user/' + friends[v.index].id">资料</RouterLink>
                <RouterLink class="btn btn-primary btn-sm" :to="'/app/chat/' + friends[v.index].id">聊天</RouterLink>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="panel">
      <h3><UserPlusIcon class="h-ico" /> 通过 ID 添加</h3>
      <div class="row">
        <input v-model="friendId" type="number" min="1" placeholder="对方用户 ID" />
        <button type="button" class="btn btn-primary tap-scale" @click="quickAdd">添加</button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.friends-page {
  max-width: 100%;
}
@media (min-width: 768px) {
  .friends-page {
    max-width: 900px;
    margin: 0 auto;
  }
}
h2 {
  margin: 0 0 0.35rem;
  display: flex;
  align-items: center;
  gap: 0.35rem;
}
.sub {
  color: var(--text-muted);
  font-size: 0.88rem;
  margin: 0 0 1rem;
  line-height: 1.5;
}
.stats-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem 1.5rem;
  margin-bottom: 1.25rem;
  padding: 1rem 1.25rem;
  background: linear-gradient(135deg, var(--bg-page), var(--bg-panel));
  border-radius: var(--radius);
  border: 1px solid var(--border-light);
  align-items: center;
}
.stat {
  font-size: 0.88rem;
  color: var(--text-muted);
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}
.stat strong {
  color: var(--jn-maroon);
  font-size: 1.05rem;
}
.stat-pending {
  position: relative;
}
.dot-new {
  width: 8px;
  height: 8px;
  background: var(--err);
  border-radius: 50%;
}
.virt-hint {
  font-size: 0.78rem;
  color: var(--text-subtle);
  margin: 0 0 0.65rem;
}
.friend-virt-scroll {
  max-height: min(70vh, 560px);
  overflow-y: auto;
  padding-right: 2px;
}
.friend-virt-row {
  padding-bottom: 0.75rem;
}
h3 {
  margin: 0 0 0.75rem;
  font-size: 1rem;
}
.swipe-tip {
  font-size: 0.78rem;
  color: var(--text-subtle);
  margin: 0 0 0.65rem;
  display: flex;
  align-items: center;
  gap: 0.35rem;
}
.req-card-wrap {
  overflow: hidden;
  border-radius: var(--radius);
  margin-bottom: 0.5rem;
}
.req-card {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 0.65rem;
  padding: 1rem 1.1rem;
  background: linear-gradient(120deg, var(--jn-maroon-soft), var(--bg-page));
  border: 1px solid var(--border);
  border-radius: var(--radius);
  transition: transform 0.05s ease-out;
}
.req-main {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}
.req-name {
  font-weight: 700;
  font-size: 1.02rem;
}
.list.flat {
  list-style: none;
  margin: 0;
  padding: 0;
}
.list.flat li {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.55rem 0;
  border-bottom: 1px solid var(--border-light);
}
.list.flat li:last-child {
  border-bottom: none;
}
.friend-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.25rem;
}
@media (min-width: 1024px) {
  .friend-cards {
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 1.5rem;
  }
}
.friend-card {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
  padding: 1rem;
  background: var(--bg-page);
  border: 1px solid var(--border-light);
  border-radius: var(--radius);
}
.friend-top {
  display: flex;
  gap: 0.85rem;
  align-items: flex-start;
}
.avatar {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  background: linear-gradient(145deg, var(--jn-maroon-soft), var(--jn-gold-soft));
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 1.2rem;
  color: var(--jn-maroon);
  flex-shrink: 0;
}
.friend-meta {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  min-width: 0;
}
.name {
  font-weight: 600;
}
.grade {
  font-size: 0.8rem;
  color: var(--text-muted);
  display: flex;
  align-items: center;
  gap: 0.25rem;
}
.online {
  font-size: 0.75rem;
  font-weight: 600;
  margin-top: 0.15rem;
}
.online.on {
  color: #059669;
}
.online.away {
  color: var(--warn);
}
.online.off {
  color: var(--text-subtle);
}
.badges {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}
.badge {
  font-size: 0.72rem;
  padding: 0.2rem 0.45rem;
  border-radius: 8px;
  background: var(--bg-panel);
  border: 1px solid var(--border);
  color: var(--text-muted);
}
.uid {
  color: var(--text-subtle);
  font-size: 0.8rem;
}
.since {
  font-size: 0.78rem;
  color: var(--text-subtle);
  display: flex;
  align-items: center;
  gap: 0.25rem;
}
.card-actions {
  display: flex;
  gap: 0.35rem;
  flex-wrap: wrap;
}
.row {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}
.row input {
  flex: 1;
  min-width: 160px;
  padding: 0.6rem 0.85rem;
  border-radius: 10px;
  border: 1px solid var(--border);
  background: var(--bg-panel);
  color: var(--text);
}
.muted {
  color: var(--text-muted);
  font-size: 0.9rem;
}
.muted a {
  color: var(--jn-maroon);
}
.tap-scale:active {
  transform: scale(0.98);
}
</style>
