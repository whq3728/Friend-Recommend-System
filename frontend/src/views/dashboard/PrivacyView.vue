<script setup>
import { onMounted, reactive, ref } from "vue";
import { api } from "../../api/client";
import { useUiStore } from "../../stores/ui";
import { LockClosedIcon } from "@heroicons/vue/24/outline";

const ui = useUiStore();
const loading = ref(true);
const err = ref("");
const prefs = reactive({
  share_interests: true,
  share_skills: true,
  share_friend_graph: true,
});

onMounted(async () => {
  try {
    const p = await api("/api/matching-prefs");
    prefs.share_interests = !!p.share_interests;
    prefs.share_skills = !!p.share_skills;
    prefs.share_friend_graph = !!p.share_friend_graph;
  } catch (e) {
    err.value = e instanceof Error ? e.message : "加载失败";
  } finally {
    loading.value = false;
  }
});

async function save() {
  err.value = "";
  try {
    await api("/api/matching-prefs", { method: "PUT", body: { ...prefs } });
    ui.toast("隐私偏好已保存 ✓", "ok");
  } catch (e) {
    ui.toast(e instanceof Error ? e.message : "保存失败", "err");
  }
}
</script>

<template>
  <div class="privacy">
    <h2><LockClosedIcon class="h-ico" /> 隐私偏好</h2>
    <p class="sub">自主控制哪些信息参与推荐；关闭后<strong>不会</strong>基于该维度把你推荐给他人或匹配他人。</p>
    <div v-if="err" class="toast err">{{ err }}</div>
    <p v-if="loading" class="muted">加载中…</p>

    <div v-else class="layout">
      <div class="panel diagram">
        <h3>推荐示意图</h3>
        <p class="diagram-cap">三项开关分别对应下图中的色块；关掉某一项，该维度在匹配中视为「不参与」。</p>
        <div class="viz">
          <div class="blob i" :class="{ off: !prefs.share_interests }">
            <span>兴趣</span>
          </div>
          <div class="blob s" :class="{ off: !prefs.share_skills }">
            <span>技能</span>
          </div>
          <div class="blob f" :class="{ off: !prefs.share_friend_graph }">
            <span>好友圈</span>
          </div>
          <div class="viz-mid">匹配</div>
        </div>
      </div>

      <div class="panel switches">
        <label class="switch-row">
          <div class="switch-text">
            <span class="title">允许「兴趣标签」参与匹配</span>
            <span class="hint">关闭后不会被基于兴趣推荐，他人也难以因兴趣与你匹配</span>
          </div>
          <button
            type="button"
            role="switch"
            :aria-checked="prefs.share_interests"
            class="switch"
            :class="{ on: prefs.share_interests }"
            @click="prefs.share_interests = !prefs.share_interests"
          >
            <span class="knob" />
          </button>
        </label>

        <label class="switch-row">
          <div class="switch-text">
            <span class="title">允许「技能」参与匹配</span>
            <span class="hint">关闭后组队/技能向推荐会忽略你的技能数据</span>
          </div>
          <button
            type="button"
            role="switch"
            :aria-checked="prefs.share_skills"
            class="switch"
            :class="{ on: prefs.share_skills }"
            @click="prefs.share_skills = !prefs.share_skills"
          >
            <span class="knob" />
          </button>
        </label>

        <label class="switch-row">
          <div class="switch-text">
            <span class="title">允许「好友圈」参与匹配</span>
            <span class="hint">关闭后共同好友维度不再参与，人脉拓展型推荐会减弱</span>
          </div>
          <button
            type="button"
            role="switch"
            :aria-checked="prefs.share_friend_graph"
            class="switch"
            :class="{ on: prefs.share_friend_graph }"
            @click="prefs.share_friend_graph = !prefs.share_friend_graph"
          >
            <span class="knob" />
          </button>
        </label>

        <button type="button" class="btn btn-primary save-btn tap-scale" @click="save">保存设置</button>
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
.layout {
  display: grid;
  grid-template-columns: 1fr 1.15fr;
  gap: 1.25rem;
  align-items: start;
}
@media (max-width: 800px) {
  .layout {
    grid-template-columns: 1fr;
  }
}
.diagram h3 {
  margin: 0 0 0.5rem;
  font-size: 1rem;
}
.diagram-cap {
  font-size: 0.82rem;
  color: var(--text-muted);
  margin: 0 0 1rem;
  line-height: 1.45;
}
.viz {
  position: relative;
  height: 200px;
  border-radius: var(--radius);
  background: linear-gradient(160deg, var(--bg-page), var(--bg-panel));
  border: 1px dashed var(--border);
  overflow: hidden;
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
.switch-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  padding: 1rem 0;
  border-bottom: 1px solid var(--border-light);
  cursor: pointer;
}
.switch-row:last-of-type {
  border-bottom: none;
}
.switch-text {
  flex: 1;
  min-width: 0;
}
.switch-text .title {
  display: block;
  font-weight: 600;
  font-size: 0.95rem;
  margin-bottom: 0.25rem;
}
.switch-text .hint {
  display: block;
  font-size: 0.8rem;
  color: var(--text-subtle);
  line-height: 1.45;
}
.switch {
  flex-shrink: 0;
  width: 52px;
  height: 30px;
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
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
  transition: transform 0.25s cubic-bezier(0.22, 1, 0.36, 1);
}
.switch.on .knob {
  transform: translateX(22px);
}
.save-btn {
  margin-top: 1rem;
  width: 100%;
}
.muted {
  color: var(--text-muted);
}
.tap-scale:active {
  transform: scale(0.99);
}
</style>
