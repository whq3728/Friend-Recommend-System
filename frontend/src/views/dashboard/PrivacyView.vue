<script setup>
import { onMounted, reactive, ref } from "vue";
import { api } from "../../api/client";
import { useUiStore } from "../../stores/ui";
import {
  LockClosedIcon,
  EyeIcon,
  UserGroupIcon,
  UsersIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  TrashIcon,
  SparklesIcon,
} from "@heroicons/vue/24/outline";

const ui = useUiStore();
const loading = ref(true);
const err = ref("");

// 推荐隐私偏好（原有的）
const matchingPrefs = reactive({
  share_interests: true,
  share_skills: true,
  share_friend_graph: true,
  share_personality: true,
});

// 陌生人可见设置
const strangerVis = reactive({
  show_gender: true,
  show_grade: true,
  show_major: true,
  show_interests: true,
  show_skills: true,
  show_projects: false,
  show_personality: false,
});

// 好友可见设置（全局默认）
const friendVis = reactive({
  show_phone: false,
  show_gender: true,
  show_grade: true,
  show_major: true,
  show_interests: true,
  show_skills: true,
  show_projects: true,
  show_personality: true,
});

// 好友列表
const friends = ref([]);

// 好友独立设置
const friendOverrides = ref({});
const expandedFriend = ref(null);

// 折叠状态
const expandedSections = reactive({
  matching: true,
  stranger: false,
  friend: false,
  perFriend: false,
});

const matchingFieldLabels = {
  share_interests: { label: "允许「兴趣标签」参与匹配", hint: "关闭后不会被基于兴趣推荐，他人也难以因兴趣与你匹配" },
  share_skills: { label: "允许「技能」参与匹配", hint: "关闭后组队/技能向推荐会忽略你的技能数据" },
  share_friend_graph: { label: "允许「好友圈」参与匹配", hint: "关闭后共同好友维度不再参与，人脉拓展型推荐会减弱" },
  share_personality: { label: "允许「性格标签」参与匹配", hint: "关闭后性格匹配维度不再参与，恋爱/好友推荐的准确度会下降" },
};

const strangerFieldLabels = {
  show_gender: { label: "性别", hint: "在推荐中显示你的性别" },
  show_grade: { label: "年级", hint: "在推荐中显示你的年级" },
  show_major: { label: "专业", hint: "在推荐中显示你的专业" },
  show_interests: { label: "兴趣标签", hint: "在推荐中显示你的兴趣标签" },
  show_skills: { label: "技能", hint: "在推荐中显示你的技能" },
  show_projects: { label: "项目/比赛", hint: "在推荐中显示你的项目经历" },
  show_personality: { label: "性格标签", hint: "在推荐中显示你的性格标签" },
};

const friendFieldLabels = {
  show_phone: { label: "手机号", hint: "好友可以看到你的手机号" },
  show_gender: { label: "性别", hint: "好友可以看到你的性别" },
  show_grade: { label: "年级", hint: "好友可以看到你的年级" },
  show_major: { label: "专业", hint: "好友可以看到你的专业" },
  show_interests: { label: "兴趣标签", hint: "好友可以看到你的兴趣标签" },
  show_skills: { label: "技能", hint: "好友可以看到你的技能" },
  show_projects: { label: "项目/比赛", hint: "好友可以看到你的项目经历" },
  show_personality: { label: "性格标签", hint: "好友可以看到你的性格标签" },
};

async function loadAll() {
  loading.value = true;
  err.value = "";
  try {
    // 并行加载所有设置
    const [matchingRes, strangerRes, friendRes, friendsRes, overridesRes] = await Promise.all([
      api("/api/matching-prefs"),
      api("/api/visibility/stranger"),
      api("/api/visibility/friend"),
      api("/api/friends"),
      api("/api/visibility/friend-overrides").catch(() => []),
    ]);

    Object.assign(matchingPrefs, matchingRes);
    Object.assign(strangerVis, strangerRes);
    Object.assign(friendVis, friendRes);
    friends.value = friendsRes || [];
    friendOverrides.value = {};
    if (Array.isArray(overridesRes)) {
      for (const o of overridesRes) {
        friendOverrides.value[o.friend_id] = o;
      }
    }
  } catch (e) {
    err.value = e instanceof Error ? e.message : "加载失败";
  } finally {
    loading.value = false;
  }
}

async function saveMatching() {
  try {
    await api("/api/matching-prefs", { method: "PUT", body: { ...matchingPrefs } });
    ui.toast("推荐隐私偏好已保存 ✓", "ok");
  } catch (e) {
    ui.toast(e instanceof Error ? e.message : "保存失败", "err");
  }
}

async function saveStranger() {
  try {
    await api("/api/visibility/stranger", { method: "PUT", body: { ...strangerVis } });
    ui.toast("陌生人可见设置已保存 ✓", "ok");
  } catch (e) {
    ui.toast(e instanceof Error ? e.message : "保存失败", "err");
  }
}

async function saveFriend() {
  try {
    await api("/api/visibility/friend", { method: "PUT", body: { ...friendVis } });
    ui.toast("好友可见设置已保存 ✓", "ok");
  } catch (e) {
    ui.toast(e instanceof Error ? e.message : "保存失败", "err");
  }
}

async function loadFriendOverrides(friendId) {
  try {
    const override = await api(`/api/visibility/friend-overrides/${friendId}`);
    friendOverrides.value[friendId] = override;
  } catch (e) {
    friendOverrides.value[friendId] = null;
  }
}

async function saveFriendOverride(friendId) {
  const override = friendOverrides.value[friendId];
  if (!override) return;

  try {
    await api(`/api/visibility/friend-overrides/${friendId}`, { method: "PUT", body: override });
    ui.toast("好友隐私设置已保存 ✓", "ok");
  } catch (e) {
    ui.toast(e instanceof Error ? e.message : "保存失败", "err");
  }
}

async function deleteFriendOverride(friendId) {
  try {
    await api(`/api/visibility/friend-overrides/${friendId}`, { method: "DELETE" });
    delete friendOverrides.value[friendId];
    ui.toast("已恢复全局默认设置 ✓", "ok");
  } catch (e) {
    ui.toast(e instanceof Error ? e.message : "删除失败", "err");
  }
}

function toggleFriendExpand(friendId) {
  if (expandedFriend.value === friendId) {
    expandedFriend.value = null;
  } else {
    expandedFriend.value = friendId;
    if (!friendOverrides.value.hasOwnProperty(friendId)) {
      loadFriendOverrides(friendId);
    }
  }
}

function getFieldValue(friendId, field, defaultValue) {
  const override = friendOverrides.value[friendId];
  if (override && override[field] !== null && override[field] !== undefined) {
    return override[field];
  }
  return defaultValue;
}

function setFieldValue(friendId, field, value) {
  if (!friendOverrides.value[friendId]) {
    friendOverrides.value[friendId] = {
      friend_id: friendId,
      show_phone: null,
      show_gender: null,
      show_grade: null,
      show_major: null,
      show_interests: null,
      show_skills: null,
      show_projects: null,
      show_personality: null,
    };
  }
  friendOverrides.value[friendId][field] = value;
}

function hasOverride(friendId) {
  const override = friendOverrides.value[friendId];
  if (!override) return false;
  return Object.values(override).some((v) => v !== null && v !== undefined && v !== "" && v !== friendId);
}

onMounted(() => {
  loadAll();
});
</script>

<template>
  <div class="privacy">
    <h2><LockClosedIcon class="h-ico" /> 隐私设置</h2>
    <p class="sub">控制你的资料对不同人群的可见范围，以及哪些信息参与推荐匹配。</p>
    <div v-if="err" class="toast err">{{ err }}</div>
    <p v-if="loading" class="muted">加载中…</p>

    <div v-else class="sections">
      <!-- 推荐隐私偏好 -->
      <div class="panel section">
        <button class="section-header" @click="expandedSections.matching = !expandedSections.matching">
          <div class="section-title">
            <SparklesIcon class="h-ico" />
            <span>推荐隐私偏好</span>
          </div>
          <ChevronUpIcon v-if="expandedSections.matching" class="h-ico" />
          <ChevronDownIcon v-else class="h-ico" />
        </button>

        <div v-if="expandedSections.matching" class="section-body">
          <p class="section-desc">控制哪些信息参与推荐匹配；关闭后该维度不会用于匹配计算。</p>

          <div class="viz">
            <div class="blob i" :class="{ off: !matchingPrefs.share_interests }">
              <span>兴趣</span>
            </div>
            <div class="blob s" :class="{ off: !matchingPrefs.share_skills }">
              <span>技能</span>
            </div>
            <div class="blob f" :class="{ off: !matchingPrefs.share_friend_graph }">
              <span>好友圈</span>
            </div>
            <div class="blob p" :class="{ off: !matchingPrefs.share_personality }">
              <span>性格</span>
            </div>
            <div class="viz-mid">匹配</div>
          </div>

          <div class="switch-list">
            <label v-for="(info, key) in matchingFieldLabels" :key="key" class="switch-row">
              <div class="switch-text">
                <span class="title">{{ info.label }}</span>
                <span class="hint">{{ info.hint }}</span>
              </div>
              <button
                type="button"
                role="switch"
                :aria-checked="matchingPrefs[key]"
                class="switch"
                :class="{ on: matchingPrefs[key] }"
                @click="matchingPrefs[key] = !matchingPrefs[key]"
              >
                <span class="knob" />
              </button>
            </label>
          </div>

          <button type="button" class="btn btn-primary save-btn tap-scale" @click="saveMatching">
            保存推荐偏好
          </button>
        </div>
      </div>

      <!-- 陌生人可见设置 -->
      <div class="panel section">
        <button class="section-header" @click="expandedSections.stranger = !expandedSections.stranger">
          <div class="section-title">
            <EyeIcon class="h-ico" />
            <span>推荐时陌生人可见</span>
          </div>
          <ChevronUpIcon v-if="expandedSections.stranger" class="h-ico" />
          <ChevronDownIcon v-else class="h-ico" />
        </button>

        <div v-if="expandedSections.stranger" class="section-body">
          <p class="section-desc">控制当你在推荐中展示给陌生人时，对方能看到哪些资料。</p>

          <div class="switch-list">
            <label v-for="(info, key) in strangerFieldLabels" :key="key" class="switch-row">
              <div class="switch-text">
                <span class="title">{{ info.label }}</span>
                <span class="hint">{{ info.hint }}</span>
              </div>
              <button
                type="button"
                role="switch"
                :aria-checked="strangerVis[key]"
                class="switch"
                :class="{ on: strangerVis[key] }"
                @click="strangerVis[key] = !strangerVis[key]"
              >
                <span class="knob" />
              </button>
            </label>
          </div>

          <button type="button" class="btn btn-primary save-btn tap-scale" @click="saveStranger">
            保存陌生人设置
          </button>
        </div>
      </div>

      <!-- 好友可见设置（全局） -->
      <div class="panel section">
        <button class="section-header" @click="expandedSections.friend = !expandedSections.friend">
          <div class="section-title">
            <UserGroupIcon class="h-ico" />
            <span>好友可见（全局默认）</span>
          </div>
          <ChevronUpIcon v-if="expandedSections.friend" class="h-ico" />
          <ChevronDownIcon v-else class="h-ico" />
        </button>

        <div v-if="expandedSections.friend" class="section-body">
          <p class="section-desc">设置所有好友能看到哪些资料。下方可以对单个好友单独设置覆盖此默认值。</p>

          <div class="switch-list">
            <label v-for="(info, key) in friendFieldLabels" :key="key" class="switch-row">
              <div class="switch-text">
                <span class="title">{{ info.label }}</span>
                <span class="hint">{{ info.hint }}</span>
              </div>
              <button
                type="button"
                role="switch"
                :aria-checked="friendVis[key]"
                class="switch"
                :class="{ on: friendVis[key] }"
                @click="friendVis[key] = !friendVis[key]"
              >
                <span class="knob" />
              </button>
            </label>
          </div>

          <button type="button" class="btn btn-primary save-btn tap-scale" @click="saveFriend">
            保存好友默认设置
          </button>
        </div>
      </div>

      <!-- 好友独立隐私设置 -->
      <div class="panel section">
        <button class="section-header" @click="expandedSections.perFriend = !expandedSections.perFriend">
          <div class="section-title">
            <UsersIcon class="h-ico" />
            <span>好友独立隐私设置</span>
          </div>
          <ChevronUpIcon v-if="expandedSections.perFriend" class="h-ico" />
          <ChevronDownIcon v-else class="h-ico" />
        </button>

        <div v-if="expandedSections.perFriend" class="section-body">
          <p class="section-desc">针对单个好友设置可见范围，优先级高于全局好友设置。</p>

          <div v-if="friends.length === 0" class="empty-state">
            <UsersIcon class="empty-icon" />
            <p>暂无好友，添加好友后可单独设置隐私</p>
          </div>

          <div v-else class="friend-list">
            <div v-for="friend in friends" :key="friend.id" class="friend-item">
              <button class="friend-header" @click="toggleFriendExpand(friend.id)">
                <div class="friend-info">
                  <span class="friend-name">{{ friend.username }}</span>
                  <span v-if="hasOverride(friend.id)" class="override-badge">已自定义</span>
                </div>
                <ChevronUpIcon v-if="expandedFriend === friend.id" class="h-ico" />
                <ChevronDownIcon v-else class="h-ico" />
              </button>

              <div v-if="expandedFriend === friend.id" class="friend-body">
                <div class="switch-list compact">
                  <label v-for="(info, key) in friendFieldLabels" :key="key" class="switch-row compact-row">
                    <div class="switch-text">
                      <span class="title">{{ info.label }}</span>
                    </div>
                    <div class="switch-with-default">
                      <button
                        type="button"
                        role="switch"
                        :aria-checked="getFieldValue(friend.id, key, friendVis[key])"
                        class="switch"
                        :class="{ on: getFieldValue(friend.id, key, friendVis[key]) }"
                        @click="setFieldValue(friend.id, key, !getFieldValue(friend.id, key, friendVis[key]))"
                      >
                        <span class="knob" />
                      </button>
                      <span v-if="!hasOverride(friend.id) || friendOverrides[friend.id]?.[key] === null || friendOverrides[friend.id]?.[key] === undefined" class="default-hint">
                        (默认: {{ friendVis[key] ? "显示" : "隐藏" }})
                      </span>
                    </div>
                  </label>
                </div>

                <div class="friend-actions">
                  <button type="button" class="btn btn-primary btn-sm tap-scale" @click="saveFriendOverride(friend.id)">
                    保存
                  </button>
                  <button
                    v-if="hasOverride(friend.id)"
                    type="button"
                    class="btn btn-ghost btn-sm tap-scale"
                    @click="deleteFriendOverride(friend.id)"
                  >
                    <TrashIcon class="h-ico" />
                    恢复默认
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.privacy {
  max-width: 900px;
}
h2 {
  margin: 0 0 0.35rem;
}
.sub {
  color: var(--text-muted);
  font-size: 0.88rem;
  margin: 0 0 1.25rem;
  line-height: 1.55;
  max-width: 720px;
}
.sections {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}
.section {
  padding: 0;
  overflow: hidden;
}
.section-header {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.25rem;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 600;
  color: var(--text);
  text-align: left;
  transition: background 0.15s;
}
.section-header:hover {
  background: rgba(0, 0, 0, 0.03);
}
.section-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.section-body {
  padding: 0 1.25rem 1.25rem;
}
.section-desc {
  color: var(--text-muted);
  font-size: 0.85rem;
  margin: 0 0 1rem;
  line-height: 1.5;
}
.matching-diagram {
  margin-bottom: 1rem;
  border-radius: var(--radius);
  overflow: hidden;
  background: var(--bg-page);
  padding: 0.5rem;
  text-align: center;
}
.matching-diagram svg {
  display: inline-block;
  max-width: 100%;
}
.diag-block {
  transition: opacity 0.25s ease;
}
.diag-block.off {
  opacity: 0.3;
}

/* viz 图示样式 */
.viz {
  position: relative;
  height: 200px;
  border-radius: var(--radius);
  background: linear-gradient(160deg, var(--bg-page), var(--bg-panel));
  border: 1px dashed var(--border);
  overflow: hidden;
  margin-bottom: 1rem;
}
.blob {
  position: absolute;
  width: 88px;
  height: 88px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.78rem;
  font-weight: 700;
  color: #fff;
  transition: opacity 0.3s, transform 0.3s;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.12);
}
.blob.off {
  opacity: 0.22;
  transform: scale(0.92);
}
.blob.i {
  background: linear-gradient(135deg, #3b82f6, #1d4ed8);
  left: 12%;
  top: 18%;
}
.blob.s {
  background: linear-gradient(135deg, #059669, #047857);
  right: 14%;
  top: 22%;
}
.blob.f {
  background: linear-gradient(135deg, #8b5cf6, #6d28d9);
  left: 38%;
  bottom: 12%;
}
.blob.p {
  background: linear-gradient(135deg, #f59e0b, #d97706);
  right: 28%;
  bottom: 22%;
}
.viz-mid {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--bg-panel);
  border: 2px solid var(--jn-maroon);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.72rem;
  font-weight: 800;
  color: var(--jn-maroon);
  box-shadow: var(--shadow);
}
.switch-list {
  display: flex;
  flex-direction: column;
}
.switch-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  padding: 0.85rem 0;
  border-bottom: 1px solid var(--border-light);
  cursor: pointer;
}
.switch-row:last-child {
  border-bottom: none;
}
.switch-row.compact-row {
  padding: 0.6rem 0;
}
.switch-text {
  flex: 1;
  min-width: 0;
}
.switch-text .title {
  display: block;
  font-weight: 500;
  font-size: 0.92rem;
}
.switch-text .hint {
  display: block;
  font-size: 0.78rem;
  color: var(--text-subtle);
  line-height: 1.4;
}
.switch {
  flex-shrink: 0;
  width: 48px;
  height: 28px;
  border-radius: 999px;
  border: none;
  background: #d6d3d1;
  position: relative;
  cursor: pointer;
  transition: background 0.25s ease;
  padding: 0;
}
.switch.on {
  background: linear-gradient(90deg, #10b981, #059669);
}
.switch .knob {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
  transition: transform 0.25s cubic-bezier(0.22, 1, 0.36, 1);
}
.switch.on .knob {
  transform: translateX(20px);
}
.save-btn {
  margin-top: 1.25rem;
  width: 100%;
}
.muted {
  color: var(--text-muted);
}
.tap-scale:active {
  transform: scale(0.99);
}

/* 好友列表样式 */
.friend-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.friend-item {
  border: 1px solid var(--border-light);
  border-radius: var(--radius);
  overflow: hidden;
}
.friend-header {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.85rem 1rem;
  background: var(--bg-page);
  border: none;
  cursor: pointer;
  font-size: 0.9rem;
  text-align: left;
  transition: background 0.15s;
}
.friend-header:hover {
  background: rgba(0, 0, 0, 0.03);
}
.friend-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
.friend-name {
  font-weight: 500;
}
.override-badge {
  font-size: 0.72rem;
  background: var(--jn-gold);
  color: #fff;
  padding: 0.15rem 0.5rem;
  border-radius: 999px;
}
.friend-body {
  padding: 1rem;
  background: var(--bg-panel);
}
.switch-with-default {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.default-hint {
  font-size: 0.72rem;
  color: var(--text-subtle);
}
.friend-actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 1rem;
}
.btn-sm {
  padding: 0.4rem 0.85rem;
  font-size: 0.82rem;
}
.empty-state {
  text-align: center;
  padding: 2rem 1rem;
  color: var(--text-muted);
}
.empty-icon {
  width: 48px;
  height: 48px;
  margin-bottom: 0.75rem;
  opacity: 0.4;
}
@media (max-width: 480px) {
  .section-header {
    padding: 0.85rem 1rem;
  }
  .section-body {
    padding: 0 1rem 1rem;
  }
}
</style>
