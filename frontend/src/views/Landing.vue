<script setup>
import { ref } from "vue";
import { RouterLink } from "vue-router";
import CampusBackdrop from "../components/CampusBackdrop.vue";
import { ChatBubbleLeftRightIcon, HandRaisedIcon, LockClosedIcon, ShieldCheckIcon } from "@heroicons/vue/24/outline";

// 首页仅包含介绍与引导动作，PSI说明默认折叠
const psiExpanded = ref(false);
</script>

<template>
  <CampusBackdrop :center="false">
    <div class="landing">
      <header class="hero">
        <p class="badge">暨南大学校园</p>
        <h1>JNU Link</h1>
        <p class="sub">遇见志趣相投的伙伴</p>
        <p class="desc">
          完善你的兴趣、技能与经历，我们会为你推荐可能聊得来的同学。拓展人脉、找队友、遇见心动——一切从这里开始。
        </p>
        <div class="cta">
          <RouterLink class="btn btn-primary" to="/login">进入</RouterLink>
          <RouterLink class="btn btn-ghost" to="/register">注册</RouterLink>
        </div>
      </header>

      <section class="psi-card-wrap">
        <button
          type="button"
          class="psi-card"
          :class="{ expanded: psiExpanded }"
          @click="psiExpanded = !psiExpanded"
        >
          <span class="psi-title"
            ><ShieldCheckIcon class="h-ico" /> 系统说明</span
          >
          <span class="psi-toggle">{{ psiExpanded ? "收起" : "展开" }}</span>
          <p v-show="psiExpanded" class="psi-content">
            本系统基于轻量级隐私集合求交（PSI）技术，在不泄露原始兴趣数据的前提下完成匹配。你的兴趣、技能等隐私数据仅用于计算与他人的交集大小，不会以明文形式传输或展示给任何第三方。
          </p>
        </button>
      </section>

      <section class="grid">
        <article class="card">
          <span class="icon"><HandRaisedIcon class="h-ico" /></span>
          <h3>发现同好</h3>
          <p>好友、组队、恋爱三种场景，为你推荐更可能合拍的人。</p>
        </article>
        <article class="card">
          <span class="icon"><LockClosedIcon class="h-ico" /></span>
          <h3>隐私可控</h3>
          <p>自主选择哪些资料参与推荐，不参与的内容不会被用于匹配。</p>
        </article>
        <article class="card">
          <span class="icon"><ChatBubbleLeftRightIcon class="h-ico" /></span>
          <h3>好友与聊天</h3>
          <p>发起好友请求，成为好友后即可查看完整资料、随时聊天。</p>
        </article>
      </section>

      <footer class="foot">
        <RouterLink to="/login">登录</RouterLink>
        ·
        <RouterLink to="/register">注册</RouterLink>
      </footer>
    </div>
  </CampusBackdrop>
</template>

<style scoped>
.landing {
  max-width: 900px;
  margin: 0 auto;
  padding: 2.5rem 1.25rem 3rem;
}
.hero {
  text-align: center;
  margin-bottom: 2.5rem;
}
.badge {
  display: inline-block;
  padding: 0.3rem 0.9rem;
  border-radius: 999px;
  background: var(--jn-maroon-soft);
  color: var(--jn-maroon);
  font-size: 0.8rem;
  font-weight: 600;
  margin: 0 0 1.25rem;
}
.hero h1 {
  font-size: clamp(2.5rem, 8vw, 3.5rem);
  margin: 0;
  color: var(--text);
  font-weight: 700;
}
.hero h1::after {
  content: "";
  display: block;
  width: 48px;
  height: 4px;
  background: linear-gradient(90deg, var(--jn-maroon), var(--jn-gold));
  margin: 0.5rem auto 0;
  border-radius: 2px;
}
.sub {
  font-size: 1.2rem;
  color: var(--text-muted);
  margin: 0.5rem 0 1rem;
}
.desc {
  text-align: center;
  color: var(--text-muted);
  font-size: 1rem;
  max-width: 520px;
  margin: 0 auto 1.75rem;
  line-height: 1.7;
}
.cta {
  display: flex;
  gap: 0.75rem;
  justify-content: center;
  flex-wrap: wrap;
}

.psi-card-wrap {
  margin-bottom: 2rem;
}
.psi-card {
  display: block;
  width: 100%;
  text-align: left;
  padding: 1rem 1.25rem;
  background: var(--bg-panel);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  cursor: pointer;
  font-family: inherit;
}
.psi-title {
  font-weight: 600;
  font-size: 0.95rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.psi-toggle {
  font-size: 0.82rem;
  color: var(--text-subtle);
}
.psi-content {
  margin: 1rem 0 0;
  font-size: 0.9rem;
  color: var(--text-muted);
  line-height: 1.65;
}

.grid {
  display: grid;
  gap: 1.25rem;
}
@media (min-width: 640px) {
  .grid {
    grid-template-columns: repeat(3, 1fr);
  }
}
.card {
  background: var(--bg-panel);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 1.5rem;
}
.icon {
  font-size: 1.75rem;
  display: block;
  margin-bottom: 0.75rem;
}
.card h3 {
  margin: 0 0 0.5rem;
  font-size: 1.05rem;
  color: var(--text);
}
.card p {
  margin: 0;
  font-size: 0.9rem;
  color: var(--text-muted);
  line-height: 1.55;
}
.foot {
  margin-top: 3rem;
  text-align: center;
  font-size: 0.88rem;
  color: var(--text-subtle);
}
.foot a:hover {
  color: var(--jn-maroon);
}
</style>
