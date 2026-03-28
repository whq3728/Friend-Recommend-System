<script setup>
import { onMounted, ref, computed, watch } from "vue";
import { RouterLink, useRouter } from "vue-router";
import { api } from "../../api/client";
import { useUiStore } from "../../stores/ui";
import {
  ArrowPathIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  DocumentTextIcon,
  HandRaisedIcon,
  HeartIcon,
  StarIcon,
  TrashIcon,
  UsersIcon,
} from "@heroicons/vue/24/outline";
import { StarIcon as StarSolidIcon } from "@heroicons/vue/24/solid";

const ui = useUiStore();
const router = useRouter();

const rows = ref([]);
const err = ref("");
const expanded = ref(new Set());
const favKey = "jnu_hist_favorites";

const favorites = ref(new Set());

// 收藏仅保存在浏览器本地，不回传后端
function loadFav() {
  try {
    const raw = JSON.parse(localStorage.getItem(favKey) || "[]");
    favorites.value = new Set(Array.isArray(raw) ? raw : []);
  } catch {
    favorites.value = new Set();
  }
}

function saveFav() {
  localStorage.setItem(favKey, JSON.stringify([...favorites.value]));
}

function toggleFav(id) {
  if (favorites.value.has(id)) favorites.value.delete(id);
  else favorites.value.add(id);
  favorites.value = new Set(favorites.value);
  saveFav();
  ui.toast(favorites.value.has(id) ? "已收藏本条记录" : "已取消收藏", "ok");
}

function toggleExpand(id) {
  const n = new Set(expanded.value);
  if (n.has(id)) n.delete(id);
  else n.add(id);
  expanded.value = n;
}

onMounted(async () => {
  loadFav();
  err.value = "";
  try {
    rows.value = await api("/api/recommend/history");
  } catch (e) {
    err.value = e instanceof Error ? e.message : "加载失败";
  }
});

async function remove(id) {
  try {
    await api(`/api/recommend/history/${id}`, { method: "DELETE" });
    rows.value = rows.value.filter((r) => r.id !== id);
    ui.toast("已删除记录", "ok");
  } catch (e) {
    err.value = e instanceof Error ? e.message : "删除失败";
  }
}

function modeLabel(m) {
  const map = { friend: "好友", team: "组队", love: "恋爱" };
  return map[m] || m;
}

function modeIcon(m) {
  const map = { friend: HandRaisedIcon, team: UsersIcon, love: HeartIcon };
  return map[m] || null;
}

function modeColor(m) {
  const map = { friend: "var(--mode-friend)", team: "var(--mode-team)", love: "var(--mode-love)" };
  return map[m] || "var(--text-muted)";
}

function modeSoft(m) {
  const map = {
    friend: "var(--mode-friend-soft)",
    team: "var(--mode-team-soft)",
    love: "var(--mode-love-soft)",
  };
  return map[m] || "var(--bg-page)";
}

function matchPercent(score) {
  return Math.round((score || 0) * 100);
}

function highMatchCount(items) {
  if (!items?.length) return 0;
  return items.filter((it) => matchPercent(it.score) >= 70).length;
}

function summary(items) {
  const n = items?.length || 0;
  const high = highMatchCount(items);
  if (n === 0) return "无推荐";
  if (high > 0) return `共 ${n} 人 · ${high} 位高匹配`;
  return `共 ${n} 人`;
}

function dimsLine(it) {
  const d = it.dims;
  if (!d) return matchPercent(it.score) + "% 综合匹配";
  const parts = [];
  if (d.interest_jaccard != null) parts.push(`兴趣 ${Math.round(d.interest_jaccard * 100)}%`);
  if (d.skill_jaccard != null) parts.push(`技能 ${Math.round(d.skill_jaccard * 100)}%`);
  if (d.friend_jaccard != null) parts.push(`好友圈 ${Math.round(d.friend_jaccard * 100)}%`);
  return parts.join(" · ") || `${matchPercent(it.score)}% 综合`;
}

function goRecommend(mode) {
  router.push({ path: "/app/recommend", query: { mode: mode || "friend" } });
}

const sortedRows = computed(() => {
  const list = [...rows.value];
  list.sort((a, b) => {
    const fa = favorites.value.has(a.id) ? 1 : 0;
    const fb = favorites.value.has(b.id) ? 1 : 0;
    if (fa !== fb) return fb - fa;
    return (b.id || 0) - (a.id || 0);
  });
  return list;
});

const HIST_PAGE = 8;
const histVisible = ref(HIST_PAGE);
const pagedRows = computed(() => sortedRows.value.slice(0, histVisible.value));
const hasMoreHist = computed(() => histVisible.value < sortedRows.value.length);

function loadMoreHist() {
  histVisible.value = Math.min(histVisible.value + HIST_PAGE, sortedRows.value.length);
}

watch(rows, () => {
  histVisible.value = HIST_PAGE;
});
</script>

<template>
  <div class="hist">
    <h2><DocumentTextIcon class="h-ico" /> 推荐记录</h2>
    <p class="sub">按时间回顾每次推荐；列表分页加载，展开详情仍按需渲染</p>
    <div v-if="err" class="toast err">{{ err }}</div>
    <p v-if="!err && !rows.length" class="muted">
      暂无记录，去<RouterLink to="/app/recommend">推荐页</RouterLink>开始吧
    </p>

    <article
      v-for="h in pagedRows"
      :key="h.id"
      class="hist-card"
      :style="{ '--mode': modeColor(h.mode), '--mode-soft': modeSoft(h.mode) }"
    >
      <button type="button" class="card-fold" @click="toggleExpand(h.id)">
        <header class="hd">
          <span class="mode-pill">
            <component :is="modeIcon(h.mode)" class="h-ico" />
            {{ modeLabel(h.mode) }}
          </span>
          <time>{{ h.created_at }}</time>
        </header>
        <p class="summary">{{ summary(h.items) }}</p>
        <span class="fold-hint">
          {{ expanded.has(h.id) ? "收起" : "展开详情" }}
          <component :is="expanded.has(h.id) ? ChevronUpIcon : ChevronDownIcon" class="h-ico" />
        </span>
      </button>

      <div v-show="expanded.has(h.id)" class="detail">
        <ol v-if="h.items?.length" class="items">
          <li v-for="it in h.items" :key="it.id">
            <div class="person">
              <RouterLink :to="'/app/user/' + it.id">{{ it.username }}</RouterLink>
              <span class="dim-mini">{{ dimsLine(it) }}</span>
            </div>
            <div class="score-cell">
              <div class="score-bar-wrap">
                <div class="score-bar" :style="{ width: matchPercent(it.score) + '%' }"></div>
              </div>
              <span class="sc">{{ matchPercent(it.score) }}%</span>
            </div>
            <p v-if="it.reason" class="reason">{{ it.reason }}</p>
          </li>
        </ol>
        <p v-else class="muted">无条目</p>
      </div>

      <footer class="card-foot">
        <button
          type="button"
          class="btn btn-ghost btn-sm"
          :class="{ fav: favorites.has(h.id) }"
          @click.stop="toggleFav(h.id)"
        >
          <StarSolidIcon v-if="favorites.has(h.id)" class="h-ico" />
          <StarIcon v-else class="h-ico" />
          {{ favorites.has(h.id) ? "已收藏" : "收藏" }}
        </button>
        <button type="button" class="btn btn-ghost btn-sm" @click.stop="goRecommend(h.mode)">
          <ArrowPathIcon class="h-ico" /> 再次推荐
        </button>
        <button type="button" class="btn btn-ghost btn-sm" @click.stop="remove(h.id)">
          <TrashIcon class="h-ico" /> 删除
        </button>
      </footer>
    </article>

    <div v-if="hasMoreHist" class="more-wrap">
      <button type="button" class="btn btn-ghost" @click="loadMoreHist">加载更多记录</button>
    </div>
  </div>
</template>

<style scoped>
.hist {
  max-width: 720px;
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
.hist-card {
  margin-bottom: 1rem;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border);
  background: var(--bg-panel);
  overflow: hidden;
  border-left: 4px solid var(--mode);
}
.more-wrap {
  text-align: center;
  margin-top: 0.5rem;
}
.card-fold {
  width: 100%;
  text-align: left;
  background: linear-gradient(105deg, var(--mode-soft), var(--bg-panel));
  border: none;
  padding: 1rem 1.15rem 0.5rem;
  cursor: pointer;
  font-family: inherit;
  color: inherit;
}
.hd {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 0.35rem;
}
.mode-pill {
  font-weight: 800;
  color: var(--mode);
  font-size: 0.95rem;
}
time {
  color: var(--text-subtle);
  font-size: 0.82rem;
}
.summary {
  font-size: 0.88rem;
  color: var(--text-muted);
  margin: 0;
}
.fold-hint {
  display: block;
  font-size: 0.75rem;
  color: var(--text-subtle);
  margin-top: 0.45rem;
}
.detail {
  padding: 0 1.15rem 0.75rem;
}
.items {
  margin: 0;
  padding-left: 0;
  list-style: none;
}
.items li {
  margin-bottom: 0.85rem;
  padding-bottom: 0.65rem;
  border-bottom: 1px solid var(--border-light);
}
.items li:last-child {
  border-bottom: none;
}
.person {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  margin-bottom: 0.35rem;
}
.dim-mini {
  font-size: 0.75rem;
  color: var(--text-subtle);
}
.score-cell {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  max-width: 220px;
}
.score-bar-wrap {
  flex: 1;
  height: 6px;
  background: var(--border);
  border-radius: 3px;
  overflow: hidden;
}
.score-bar {
  height: 100%;
  background: var(--mode);
  border-radius: 3px;
  transition: width 0.35s ease;
}
.sc {
  color: var(--mode);
  font-variant-numeric: tabular-nums;
  font-weight: 700;
  font-size: 0.85rem;
}
.reason {
  font-size: 0.8rem;
  color: var(--text-muted);
  margin: 0.35rem 0 0;
}
.card-foot {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  padding: 0.65rem 1rem 1rem;
  border-top: 1px solid var(--border-light);
  background: var(--bg-page);
}
.fav {
  color: var(--jn-gold);
  border-color: var(--jn-gold-soft);
}
.muted {
  color: var(--text-muted);
}
.muted a {
  color: var(--jn-maroon);
}
</style>
