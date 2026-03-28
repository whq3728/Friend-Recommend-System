<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from "vue";
import { RouterLink, useRoute } from "vue-router";
import { api } from "../../api/client";
import { useAuthStore } from "../../stores/auth";
import { useUiStore } from "../../stores/ui";
import {
  ArrowPathIcon,
  ChatBubbleOvalLeftIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  CloudArrowDownIcon,
  HandRaisedIcon,
  HeartIcon,
  LightBulbIcon,
  SparklesIcon,
  UserIcon,
  UserPlusIcon,
  UsersIcon,
} from "@heroicons/vue/24/outline";

const auth = useAuthStore();
const ui = useUiStore();
const route = useRoute();

function resolveModeFromRoute() {
  const q = route.query.mode;
  return q === "friend" || q === "team" || q === "love" ? q : "friend";
}

const modes = [
  {
    key: "friend",
    label: "好友",
    icon: HandRaisedIcon,
    desc: "拓展人脉 · 认识志趣相投的朋友",
    hint: "侧重共同好友与兴趣，适合日常社交",
    color: "var(--mode-friend)",
    soft: "var(--mode-friend-soft)",
  },
  {
    key: "team",
    label: "组队",
    icon: UsersIcon,
    desc: "找队友 · 组项目 · 参加比赛",
    hint: "侧重技能与项目经历，适合组队做任务",
    color: "var(--mode-team)",
    soft: "var(--mode-team-soft)",
  },
  {
    key: "love",
    label: "恋爱",
    icon: HeartIcon,
    desc: "兴趣相投 · 性格契合",
    hint: "侧重兴趣与性格标签，遇见可能心动的人",
    color: "var(--mode-love)",
    soft: "var(--mode-love-soft)",
  },
];

const mode = ref(resolveModeFromRoute());
const loading = ref(false);
const loadingMore = ref(false);
const err = ref("");
const items = ref([]);
const skip = ref(0);
const deckIndex = ref(0);
const exhausted = ref(false);
const PAGE = 8;

const dragX = ref(0);
const dragging = ref(false);
let dragStartX = 0;
let activePointer = false;

const currentMode = computed(() => modes.find((m) => m.key === mode.value) || modes[0]);

const currentCard = computed(() => items.value[deckIndex.value] || null);
const canLoadMore = computed(() => !exhausted.value && items.value.length > 0 && skip.value < 80);

function matchPercent(score) {
  return Math.round((score || 0) * 100);
}

function fateLabel(score) {
  const p = matchPercent(score);
  if (p >= 85) return "缘分指数 · 极佳";
  if (p >= 70) return "缘分指数 · 很合拍";
  if (p >= 50) return "缘分指数 · 值得一聊";
  return "缘分指数 · 新朋友";
}

function matchReason(item) {
  return item?.reason || "可能合拍";
}

const greeting = computed(() => {
  const h = new Date().getHours();
  const name = auth.user?.username || "你";
  if (h < 6) return `夜深了，${name}，注意休息哦`;
  if (h < 12) return `早上好，${name}，新的一天加油`;
  if (h < 18) return `下午好，${name}，来看看推荐吧`;
  return `晚上好，${name}，放松一下`;
});

async function fetchBatch(append) {
  // append=false 视为换一批，重置游标与卡片位置
  if (append) loadingMore.value = true;
  else {
    loading.value = true;
    err.value = "";
    items.value = [];
    skip.value = 0;
    deckIndex.value = 0;
    exhausted.value = false;
  }
  try {
    const url = `/api/recommend/${mode.value}/detailed?top=${PAGE}&skip=${skip.value}`;
    const res = await api(url);
    const batch = res.items || [];
    if (append && batch.length === 0) {
      exhausted.value = true;
      ui.toast("暂时没有更多候选啦", "ok");
    }
    if (append) {
      const seen = new Set(items.value.map((x) => x.id));
      for (const it of batch) {
        if (!seen.has(it.id)) {
          seen.add(it.id);
          items.value.push(it);
        }
      }
    } else {
      items.value = batch;
    }
    skip.value += batch.length;
  } catch (e) {
    err.value = e instanceof Error ? e.message : "加载失败";
  } finally {
    loading.value = false;
    loadingMore.value = false;
  }
}

watch(mode, () => fetchBatch(false), { immediate: true });

watch(
  () => route.query.mode,
  () => {
    const m = resolveModeFromRoute();
    if (m !== mode.value) mode.value = m;
  },
);

async function loadMore() {
  if (loadingMore.value || loading.value) return;
  await fetchBatch(true);
}

function nextCard() {
  dragX.value = 0;
  if (deckIndex.value < items.value.length - 1) {
    deckIndex.value += 1;
  } else {
    ui.toast("已是最后一张，可点「加载更多」", "ok");
  }
}

function prevCard() {
  dragX.value = 0;
  if (deckIndex.value > 0) {
    deckIndex.value -= 1;
  } else {
    ui.toast("已是第一张", "ok");
  }
}

async function sendRequest(toId) {
  try {
    await api("/api/friend-requests", { method: "POST", body: { to_id: toId } });
    ui.toast("好友请求已发送", "ok");
    nextCard();
  } catch (e) {
    ui.toast(e instanceof Error ? e.message : "发送失败", "err");
  }
}

function onPointerDown(e) {
  if (!currentCard.value) return;
  dragging.value = true;
  activePointer = true;
  dragStartX = e.clientX ?? e.touches?.[0]?.clientX ?? 0;
  dragX.value = 0;
}

function onPointerMove(e) {
  if (!dragging.value || !activePointer) return;
  const x = e.clientX ?? e.touches?.[0]?.clientX ?? 0;
  dragX.value = x - dragStartX;
}

function onPointerUp() {
  if (!dragging.value) return;
  const dx = dragX.value;
  dragging.value = false;
  activePointer = false;
  if (currentCard.value && dx > 72) {
    nextCard();
  } else if (currentCard.value && dx < -72) {
    prevCard();
  }
  dragX.value = 0;
}

function openChatHint() {
  ui.toast("请先加好友，再前往好友列表发起私聊", "ok");
}

function boundUp() {
  onPointerUp();
}

onMounted(() => {
  window.addEventListener("mouseup", boundUp);
  window.addEventListener("touchend", boundUp);
});
onBeforeUnmount(() => {
  window.removeEventListener("mouseup", boundUp);
  window.removeEventListener("touchend", boundUp);
});
</script>

<template>
  <div class="rec">
    <header class="head">
      <p class="greeting"><SparklesIcon class="h-ico" /> {{ greeting }}</p>
      <h2>为你推荐</h2>
      <p class="sub">滑动卡片：右滑下一张 · 左滑上一张；加好友请点下方按钮</p>
    </header>

    <div class="mode-cards">
      <button
        v-for="m in modes"
        :key="m.key"
        type="button"
        class="mode-card tap-scale"
        :class="{ on: mode === m.key }"
        :style="{ '--accent': m.color, '--accent-soft': m.soft }"
        @click="mode = m.key"
      >
        <component :is="m.icon" class="mode-ico" />
        <span class="label">{{ m.label }}</span>
        <span class="desc">{{ m.desc }}</span>
      </button>
    </div>
    <p class="mode-hint">{{ currentMode.hint }}</p>

    <div class="toolbar">
      <button type="button" class="btn btn-ghost btn-sm tap-scale" @click="fetchBatch(false)" :disabled="loading">
        {{ loading ? "加载中…" : "" }}
        <ArrowPathIcon v-if="!loading" class="h-ico" />
        {{ loading ? "" : "换一批" }}
      </button>
      <button
        type="button"
        class="btn btn-ghost btn-sm tap-scale"
        @click="loadMore"
        :disabled="loadingMore || loading || !canLoadMore"
      >
        <CloudArrowDownIcon v-if="!loadingMore && !loading" class="h-ico" />
        {{ loadingMore || loading ? "加载中…" : "加载更多" }}
      </button>
    </div>

    <div v-if="err" class="toast err">{{ err }}</div>
    <p v-if="loading" class="skeleton-line">正在为你匹配同频同学…</p>

    <div v-else-if="items.length && currentCard" class="deck-wrap">
      <div class="deck-hint">
        <span class="hint-left"
          ><ChevronLeftIcon class="h-ico" /> 上一张</span
        >
        <span class="progress">{{ deckIndex + 1 }} / {{ items.length }}</span>
        <span class="hint-right"
          >下一张 <ChevronRightIcon class="h-ico" /></span
        >
      </div>

      <div
        class="deck"
        style="touch-action: none"
        @mousedown="onPointerDown"
        @mousemove="onPointerMove"
        @touchstart.passive="onPointerDown"
        @touchmove.passive="onPointerMove"
      >
        <div
          v-for="(row, i) in items.slice(deckIndex, deckIndex + 2)"
          :key="row.id"
          class="swipe-card"
          :class="{ back: i > 0, front: i === 0 }"
          :style="
            i === 0
              ? {
                  transform: `translateX(${dragX}px)`,
                  '--accent': currentMode.color,
                  '--accent-soft': currentMode.soft,
                }
              : { '--accent': currentMode.color, '--accent-soft': currentMode.soft }
          "
        >
          <div class="card-inner">
            <div class="avatar-ring">{{ row.username?.slice(0, 1) || "?" }}</div>
            <h3 class="uname">{{ row.username }}</h3>
            <p class="fate">{{ fateLabel(row.score) }}</p>
            <div class="score-ring-wrap">
              <div class="score-ring" :style="{ '--p': matchPercent(row.score) + '%' }">
                <span class="pct">{{ matchPercent(row.score) }}%</span>
              </div>
            </div>
            <p class="reason"><LightBulbIcon class="h-ico" /> {{ matchReason(row) }}</p>
            <div v-if="row.dims" class="dim-chips">
              <span v-if="row.dims.common_interests > 0" class="chip">兴趣重合 {{ row.dims.common_interests }}</span>
              <span v-if="row.dims.common_skills > 0" class="chip">技能重合 {{ row.dims.common_skills }}</span>
              <span v-if="row.dims.common_friends > 0" class="chip">共同好友 {{ row.dims.common_friends }}</span>
            </div>
            <div v-if="row.interests_preview?.length" class="tag-block">
              <span class="tag-label">兴趣</span>
              <span v-for="t in row.interests_preview" :key="'i' + t" class="pill">{{ t }}</span>
            </div>
            <div v-if="row.skills_preview?.length" class="tag-block">
              <span class="tag-label">技能</span>
              <span v-for="t in row.skills_preview" :key="'s' + t" class="pill skill">{{ t }}</span>
            </div>
            <div v-if="i === 0" class="card-actions">
              <button type="button" class="btn btn-ghost btn-sm" @click="prevCard"
                ><ChevronLeftIcon class="h-ico" /> 上一张</button
              >
              <button type="button" class="btn btn-ghost btn-sm" @click="nextCard"
                >下一张 <ChevronRightIcon class="h-ico" /></button
              >
              <RouterLink class="btn btn-ghost btn-sm" :to="'/app/user/' + row.id"
                ><UserIcon class="h-ico" /> 资料</RouterLink
              >
              <button type="button" class="btn btn-ghost btn-sm" @click="openChatHint"
                ><ChatBubbleOvalLeftIcon class="h-ico" /> 私聊</button
              >
              <button type="button" class="btn btn-primary btn-sm" @click="sendRequest(row.id)"
                ><UserPlusIcon class="h-ico" /> 加好友</button
              >
            </div>
          </div>
        </div>
      </div>
    </div>

    <p v-else-if="!loading" class="empty">
      暂无推荐，先完善
      <RouterLink to="/app/profile">个人资料</RouterLink>
      试试吧。
    </p>
  </div>
</template>

<style scoped>
.rec {
  max-width: 480px;
  margin: 0 auto;
}
.head {
  margin-bottom: 1.25rem;
}
.greeting {
  font-size: 0.9rem;
  color: var(--text-muted);
  margin: 0 0 0.25rem;
}
.head h2 {
  margin: 0 0 0.3rem;
  font-size: 1.5rem;
}
.sub {
  margin: 0;
  color: var(--text-muted);
  font-size: 0.85rem;
  line-height: 1.45;
}

.mode-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.65rem;
  margin-bottom: 0.5rem;
}
@media (max-width: 640px) {
  .mode-cards {
    grid-template-columns: 1fr;
  }
}
.mode-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.3rem;
  padding: 0.85rem 0.5rem;
  border-radius: var(--radius);
  border: 2px solid var(--border);
  background: var(--bg-panel);
  cursor: pointer;
  text-align: center;
  transition: all 0.2s;
  font-family: inherit;
}
.mode-card:hover {
  border-color: var(--accent);
  background: var(--accent-soft);
}
.mode-card.on {
  border-color: var(--accent);
  background: var(--accent-soft);
}
.mode-ico {
  width: 1.6rem;
  height: 1.6rem;
  display: inline-block;
  flex-shrink: 0;
}
.mode-card .label {
  font-weight: 700;
  font-size: 0.95rem;
}
.mode-card .desc {
  font-size: 0.68rem;
  color: var(--text-muted);
  line-height: 1.3;
}
.mode-hint {
  font-size: 0.8rem;
  color: var(--text-subtle);
  margin: 0 0 1rem;
}
.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.deck-wrap {
  margin-top: 0.5rem;
}
.deck-hint {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.78rem;
  color: var(--text-subtle);
  margin-bottom: 0.65rem;
  padding: 0 0.25rem;
}
.progress {
  font-weight: 700;
  color: var(--jn-maroon);
}
.deck {
  position: relative;
  min-height: 420px;
  touch-action: pan-y;
}
.swipe-card {
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  border-radius: 16px;
  background: var(--bg-panel);
  border: 1px solid var(--border);
  box-shadow: 0 2px 8px rgba(45, 42, 38, 0.06);
  transition: transform 0.06s ease-out;
  user-select: none;
}
.swipe-card.front {
  z-index: 2;
  cursor: grab;
}
.swipe-card.front:active {
  cursor: grabbing;
}
.swipe-card.back {
  z-index: 1;
  transform: scale(0.96) translateY(8px);
  opacity: 0.9;
  pointer-events: none;
}
.card-inner {
  padding: 1.35rem 1.25rem 1.15rem;
  text-align: center;
}
.avatar-ring {
  width: 56px;
  height: 56px;
  margin: 0 auto 0.65rem;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent-soft), var(--bg-page));
  border: 2px solid var(--accent);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.35rem;
  font-weight: 800;
  color: var(--accent);
}
.uname {
  margin: 0;
  font-size: 1.25rem;
}
.fate {
  margin: 0.25rem 0 0.5rem;
  font-size: 0.82rem;
  color: var(--accent);
  font-weight: 700;
}
.score-ring-wrap {
  display: flex;
  justify-content: center;
  margin-bottom: 0.65rem;
}
.score-ring {
  width: 88px;
  height: 88px;
  border-radius: 50%;
  background: conic-gradient(var(--accent) var(--p), var(--border-light) 0);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: inset 0 0 0 6px var(--bg-panel);
}
.score-ring .pct {
  width: 62px;
  height: 62px;
  border-radius: 50%;
  background: var(--bg-panel);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 1rem;
  color: var(--accent);
}
.reason {
  font-size: 0.88rem;
  color: var(--text-muted);
  margin: 0 0 0.65rem;
  line-height: 1.45;
}
.dim-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  justify-content: center;
  margin-bottom: 0.65rem;
}
.chip {
  font-size: 0.72rem;
  padding: 0.2rem 0.5rem;
  border-radius: 8px;
  background: var(--accent-soft);
  color: var(--text);
}
.tag-block {
  text-align: left;
  margin-bottom: 0.5rem;
}
.tag-label {
  display: block;
  font-size: 0.72rem;
  color: var(--text-subtle);
  margin-bottom: 0.25rem;
}
.pill {
  display: inline-block;
  font-size: 0.75rem;
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  background: var(--bg-page);
  border: 1px solid var(--border);
  margin: 0.15rem 0.25rem 0.15rem 0;
  color: var(--text-muted);
}
.pill.skill {
  border-color: rgba(5, 150, 105, 0.35);
  background: rgba(5, 150, 105, 0.08);
}
.card-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  justify-content: center;
  margin-top: 1rem;
  padding-top: 0.85rem;
  border-top: 1px solid var(--border-light);
}

.empty {
  color: var(--text-muted);
  padding: 2rem;
  line-height: 1.6;
  text-align: center;
}
.empty a {
  color: var(--jn-maroon);
}

.skeleton-line {
  padding: 1rem;
  text-align: center;
  color: var(--text-muted);
  border-radius: var(--radius);
  background: var(--bg-panel);
  border: 1px dashed var(--border);
}
.tap-scale:active {
  transform: scale(0.98);
}
</style>
