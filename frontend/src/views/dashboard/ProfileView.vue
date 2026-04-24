<script setup>
import { onMounted, reactive, ref, computed } from "vue";
import { api } from "../../api/client";
import { EyeIcon, EyeSlashIcon } from "@heroicons/vue/24/outline";

const loading = ref(true);
const err = ref("");
const ok = ref("");

// 预设选项
const GENDER_OPTIONS = ["男", "女", "其他"];
const GRADE_OPTIONS = ["大一", "大二", "大三", "大四", "研一", "研二", "研三", "博一", "博二+"];
const MAJOR_OPTIONS = [
  "计算机科学与技术",
  "软件工程",
  "人工智能",
  "数据科学",
  "电子信息工程",
  "通信工程",
  "自动化",
  "机械工程",
  "土木工程",
  "金融学",
  "经济学",
  "管理学",
  "市场营销",
  "法学",
  "汉语言文学",
  "新闻传播学",
  "英语",
  "数学",
  "物理学",
  "化学",
  "生物学",
  "医学",
  "心理学",
  "教育学",
  "设计学",
  "艺术学",
  "哲学",
  "社会学",
];

const PRESET_TAGS = [
  "📚 自习泡馆",
  "🏃 运动健身",
  "🎮 游戏开黑",
  "🎵 音乐现场",
  "📷 摄影扫街",
  "🍜 探店美食",
  "🎬 电影追剧",
  "✈️ 旅行徒步",
  "💻 编程技术",
  "🎨 设计绘画",
  "📖 读书会",
  "🧪 科研实验",
];

const PRESET_SKILLS = [
  "Python",
  "Java",
  "C++",
  "前端开发",
  "数据库",
  "数据分析",
  "机器学习",
  "英语表达",
  "PPT制作",
  "写作表达",
  "摄影",
  "设计绘画",
];

// 兴趣/技能标签选择：点击预设标签直接追加到文本框
const txtInterest = ref("");
const txtSkill = ref("");

function insertInterestTag(tag) {
  const current = txtInterest.value;
  const parts = current.split(/[\n,，]/).map(s => s.trim()).filter(Boolean);
  if (!parts.includes(tag)) {
    parts.push(tag);
    txtInterest.value = parts.join("、");
  }
}

function insertSkillTag(tag) {
  const current = txtSkill.value;
  const parts = current.split(/[\n,，]/).map(s => s.trim()).filter(Boolean);
  if (!parts.includes(tag)) {
    parts.push(tag);
    txtSkill.value = parts.join("、");
  }
}

// 性别/年级/专业各用两个字段：下拉 + 手动输入，最终合并到 form
const selGender = ref("");
const selGrade = ref("");
const selMajor = ref("");
const txtGender = ref("");
const txtGrade = ref("");
const txtMajor = ref("");

const showPassword = ref(false);

function syncSelectToForm() {
  form.gender = selGender.value || txtGender.value;
  form.grade = selGrade.value || txtGrade.value;
  form.major = selMajor.value || txtMajor.value;
  form.interests = txtInterest.value;
  form.skills = txtSkill.value;
}

// 双向同步：form 变化时同步回下拉/输入框
function onGenderInput() {
  const v = form.gender;
  if (GENDER_OPTIONS.includes(v)) {
    selGender.value = v;
    txtGender.value = "";
  } else {
    selGender.value = "";
    txtGender.value = v;
  }
}
function onGradeInput() {
  const v = form.grade;
  if (GRADE_OPTIONS.includes(v)) {
    selGrade.value = v;
    txtGrade.value = "";
  } else {
    selGrade.value = "";
    txtGrade.value = v;
  }
}
function onMajorInput() {
  const v = form.major;
  if (MAJOR_OPTIONS.includes(v)) {
    selMajor.value = v;
    txtMajor.value = "";
  } else {
    selMajor.value = "";
    txtMajor.value = v;
  }
}

const form = reactive({
  id: "",
  account: "",
  username: "",
  password: "",
  gender: "",
  grade: "",
  major: "",
  phone: "",
  interests: "",
  skills: "",
  projects: "",
  traits: "",
});

// Big Five 性格建模
const personalityFilled = ref(false);
const showPersonalityModal = ref(false);
const personalityMode = ref("quick");
const bigfiveQuick = reactive({
  extro: 3,
  agreeableness: 3,
  conscientiousness: 3,
  neuroticism: 3,
  openness: 3,
});
const questionnaire = ref([3, 3, 3, 3, 3, 3, 3, 3, 3, 3]);
const BIG5_QUESTIONS = [
  "我在社交场合中通常更愿意主动交流。",
  "我更喜欢热闹的活动而不是独处。",
  "我通常愿意体谅他人、站在对方角度考虑。",
  "当我和别人意见不同时，我更倾向于妥协而不是争辩。",
  "我做事通常有计划，并能按时完成。",
  "我会认真对待细节，尽量避免粗心。",
  "我经常会因为小事而担心或烦恼。",
  "遇到压力时，我容易出现情绪波动。",
  "我喜欢尝试新事物和新的观点。",
  "我对不同领域的想法保持好奇心。",
];

// Big Five 各维度对应的性格标签映射
const BIG5_TRAIT_TAGS = {
  extro: {
    high: ["活泼开朗", "社交达人", "热情洋溢"],
    mid: ["随和友好", "内外兼具"],
    low: ["沉稳内敛", "独立思考", "安静专注"],
  },
  agreeableness: {
    high: ["温柔体贴", "善解人意", "富有同理心"],
    mid: ["通情达理", "懂得让步"],
    low: ["直截了当", "理性客观", "立场坚定"],
  },
  conscientiousness: {
    high: ["严谨认真", "自律可靠", "有条不紊"],
    mid: ["有责任心", "目标明确"],
    low: ["灵活随性", "自由不羁", "轻松自在"],
  },
  neuroticism: {
    high: ["情感细腻", "心思敏感", "感知力强"],
    mid: ["偶尔焦虑", "情绪波动"],
    low: ["心态平和", "乐观积极", "抗压能力强"],
  },
  openness: {
    high: ["好奇心强", "思维开放", "富有创意"],
    mid: ["乐于尝试", "接受新事物"],
    low: ["脚踏实地", "稳重务实", "传统可靠"],
  },
};

function to1to5(x0to1) {
  const x = Number(x0to1);
  if (!Number.isFinite(x)) return 3;
  return Math.max(1, Math.min(5, Math.round(x * 4 + 1)));
}

function lines(arr) {
  return (arr || []).join("\n");
}

function parseList(text) {
  return text
    .split(/[\n,，]/)
    .map((s) => s.trim())
    .filter(Boolean);
}

// 根据 Big Five 值获取标签（1-2低，3中，4-5高）
function getTraitLevel(value) {
  if (value >= 4) return "high";
  if (value <= 2) return "low";
  return "mid";
}

// 生成性格标签
function generateTraits(quickData) {
  const tags = [];
  const dims = ["extro", "agreeableness", "conscientiousness", "neuroticism", "openness"];
  
  dims.forEach((dim) => {
    const level = getTraitLevel(quickData[dim]);
    const traitList = BIG5_TRAIT_TAGS[dim][level];
    // 每个维度随机选1-2个标签
    const count = Math.random() > 0.5 ? 2 : 1;
    const shuffled = [...traitList].sort(() => Math.random() - 0.5);
    tags.push(...shuffled.slice(0, count));
  });
  
  // 去重并限制数量
  const uniqueTags = [...new Set(tags)];
  return uniqueTags.slice(0, 8).join("、");
}

// 计算性格维度描述
function getDimDescription(dim, value) {
  const dimNames = {
    extro: "外向性",
    agreeableness: "宜人性",
    conscientiousness: "尽责性",
    neuroticism: "神经质",
    openness: "开放性",
  };
  const level = getTraitLevel(value);
  const levelText = { high: "高", mid: "中等", low: "低" };
  return `${dimNames[dim]}: ${levelText[level]} (${value}/5)`;
}

const personalitySummary = computed(() => {
  if (!personalityFilled.value) return "";
  return `外向性:${bigfiveQuick.extro} 宜人:${bigfiveQuick.agreeableness} 尽责:${bigfiveQuick.conscientiousness} 神经质:${bigfiveQuick.neuroticism} 开放性:${bigfiveQuick.openness}`;
});

/** 资料完善度：已填写的核心字段占比 */
const completeness = computed(() => {
  const fields = [
    form.username,
    form.gender,
    form.grade,
    form.major,
    form.interests,
    form.skills,
  ];
  const filled = fields.filter((v) => v && String(v).trim()).length;
  return Math.round((filled / fields.length) * 100);
});

onMounted(async () => {
  try {
    const p = await api("/api/profile");
    form.id = String(p.id);
    form.account = p.account || "";
    form.username = p.username || "";
    form.gender = p.gender || "";
    form.grade = p.grade || "";
    form.major = p.major || "";
    form.phone = p.phone || "";
    form.interests = lines(p.interests);
    form.skills = lines(p.skills);
    form.projects = lines(p.projects);
    form.traits = lines(p.traits);
    txtInterest.value = form.interests;
    txtSkill.value = form.skills;
    // 同步到下拉/输入框
    selGender.value = GENDER_OPTIONS.includes(p.gender) ? p.gender : "";
    txtGender.value = GENDER_OPTIONS.includes(p.gender) ? "" : (p.gender || "");
    selGrade.value = GRADE_OPTIONS.includes(p.grade) ? p.grade : "";
    txtGrade.value = GRADE_OPTIONS.includes(p.grade) ? "" : (p.grade || "");
    selMajor.value = MAJOR_OPTIONS.includes(p.major) ? p.major : "";
    txtMajor.value = MAJOR_OPTIONS.includes(p.major) ? "" : (p.major || "");
    personalityFilled.value = !!p.personality_filled;
    if (p.bigfive) {
      bigfiveQuick.extro = to1to5(p.bigfive.extro);
      bigfiveQuick.agreeableness = to1to5(p.bigfive.agreeableness);
      bigfiveQuick.conscientiousness = to1to5(p.bigfive.conscientiousness);
      bigfiveQuick.neuroticism = to1to5(p.bigfive.neuroticism);
      bigfiveQuick.openness = to1to5(p.bigfive.openness);
    }
  } catch (e) {
    err.value = e instanceof Error ? e.message : "加载失败";
  } finally {
    loading.value = false;
  }
});

function openPersonalityModal() {
  showPersonalityModal.value = true;
}

function closePersonalityModal() {
  showPersonalityModal.value = false;
}

async function submitPersonality() {
  err.value = "";
  
  try {
    // 生成性格标签
    const generatedTraits = generateTraits(bigfiveQuick);
    form.traits = generatedTraits;
    
    // 性格测试可以独立更新，不需要传 username
    const body = {};
    
    if (personalityMode.value === "quick") {
      body.personality_mode = "quick";
      body.bigfive_quick = { ...bigfiveQuick };
    } else {
      body.personality_mode = "questionnaire";
      body.bigfive_answers = [...questionnaire.value];
    }
    
    // 性格标签
    body.traits = parseList(form.traits);
    
    await api("/api/profile", { method: "PUT", body });
    
    personalityFilled.value = true;
    showPersonalityModal.value = false;
    ok.value = "性格测试完成，性格标签已自动生成";
    setTimeout(() => { ok.value = ""; }, 3000);
  } catch (e) {
    err.value = e instanceof Error ? e.message : "保存失败";
  }
}

async function save() {
  err.value = "";
  ok.value = "";
  syncSelectToForm();
  try {
    const body = {
      username: form.username.trim(),
      gender: form.gender.trim(),
      grade: form.grade.trim(),
      major: form.major.trim(),
      phone: form.phone.trim().replace(/\s/g, ""),
      interests: parseList(form.interests),
      skills: parseList(form.skills),
      projects: parseList(form.projects),
      traits: parseList(form.traits),
    };
    if (form.password.trim()) body.password = form.password.trim();

    await api("/api/profile", { method: "PUT", body });
    form.password = "";
    ok.value = "已保存";
    setTimeout(() => { ok.value = ""; }, 3000);
  } catch (e) {
    err.value = e instanceof Error ? e.message : "保存失败";
  }
}
</script>

<template>
  <div class="profile-page">
    <h2>个人信息</h2>
    <p class="sub">完善资料有助于获得更合适的推荐</p>
    
    <!-- 未完成性格测试提示 -->
    <div v-if="!personalityFilled" class="panel warn-personality">
      <h3>🧠 还未完成性格测试</h3>
      <p class="sub2">完成 Big Five 性格建模后，系统会把"相似 + 互补"的性格维度融合到推荐里，从而提升推荐准确度。</p>
      <button type="button" class="btn btn-primary" @click="openPersonalityModal">
        开始性格测试
      </button>
    </div>
    
    <!-- 已完成性格测试提示 -->
    <div v-else class="panel ok-personality">
      <div class="ok-personality-header">
        <span class="ok-icon">✓</span>
        <span>已完成性格测试</span>
      </div>
      <p class="personality-summary">{{ personalitySummary }}</p>
      <button type="button" class="btn btn-ghost btn-sm" @click="openPersonalityModal">
        重新测试
      </button>
    </div>
    
    <div v-if="err" class="toast err">{{ err }}</div>
    <div v-if="ok" class="toast ok">{{ ok }}</div>
    <p v-if="loading" class="muted">加载中…</p>
    <div v-else class="panel">
      <!-- 资料完善度 -->
      <div class="progress-wrap" v-if="completeness < 100">
        <div class="progress-label">
          <span>资料完善度</span>
          <span class="pct">{{ completeness }}%</span>
        </div>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: completeness + '%' }"></div>
        </div>
        <p class="progress-hint">完善昵称、年级、专业、兴趣和技能可获得更好推荐</p>
      </div>

      <p class="note">用户 ID 用于添加好友时查找；登录账号不可修改，昵称可改。</p>
      <div class="field">
        <label>用户 ID</label>
        <input v-model="form.id" readonly class="ro" />
      </div>
      <div class="field">
        <label>登录账号</label>
        <input v-model="form.account" readonly class="ro" />
      </div>
      <div class="field">
        <label>手机号（可选，用于验证码登录与找回密码）</label>
        <input v-model="form.phone" inputmode="tel" maxlength="20" placeholder="未绑定可在此补充" />
      </div>
      <div class="field">
        <label>昵称</label>
        <input v-model="form.username" maxlength="64" required />
      </div>
      <div class="field">
        <label>新密码（留空不改）</label>
        <div class="password-row">
          <input
            v-model="form.password"
            :type="showPassword ? 'text' : 'password'"
            autocomplete="new-password"
            placeholder="留空则保持原密码"
          />
          <button
            type="button"
            class="btn btn-ghost btn-sm toggle-pass"
            :aria-label="showPassword ? '隐藏密码' : '显示密码'"
            @click="showPassword = !showPassword"
          >
            <EyeSlashIcon v-if="showPassword" class="h-ico" />
            <EyeIcon v-else class="h-ico" />
          </button>
        </div>
      </div>
      <div class="field">
        <label>性别</label>
        <div class="select-row">
          <select v-model="selGender" @change="txtGender = ''" @input="onGenderInput">
            <option value="">请选择</option>
            <option v-for="g in GENDER_OPTIONS" :key="g" :value="g">{{ g }}</option>
          </select>
          <input v-model="txtGender" placeholder="或手动输入" @input="selGender = ''; onGenderInput" />
        </div>
      </div>
      <div class="field">
        <label>年级</label>
        <div class="select-row">
          <select v-model="selGrade" @change="txtGrade = ''" @input="onGradeInput">
            <option value="">请选择</option>
            <option v-for="g in GRADE_OPTIONS" :key="g" :value="g">{{ g }}</option>
          </select>
          <input v-model="txtGrade" placeholder="或手动输入" @input="selGrade = ''; onGradeInput" />
        </div>
      </div>
      <div class="field">
        <label>专业</label>
        <div class="select-row">
          <select v-model="selMajor" @change="txtMajor = ''" @input="onMajorInput">
            <option value="">请选择</option>
            <option v-for="m in MAJOR_OPTIONS" :key="m" :value="m">{{ m }}</option>
          </select>
          <input v-model="txtMajor" placeholder="或手动输入" @input="selMajor = ''; onMajorInput" />
        </div>
      </div>
      <div class="field">
        <label>兴趣</label>
        <div class="tag-presets">
          <button
            v-for="t in PRESET_TAGS"
            :key="t"
            type="button"
            class="tag"
            @click="insertInterestTag(t)"
          >{{ t }}</button>
        </div>
        <textarea v-model="txtInterest" rows="3" placeholder="点击上方预设标签或直接输入，每项用顿号、或换行分隔"></textarea>
      </div>

      <div class="field">
        <label>技能</label>
        <div class="tag-presets">
          <button
            v-for="t in PRESET_SKILLS"
            :key="t"
            type="button"
            class="tag"
            @click="insertSkillTag(t)"
          >{{ t }}</button>
        </div>
        <textarea v-model="txtSkill" rows="3" placeholder="点击上方预设标签或直接输入，每项用顿号、或换行分隔"></textarea>
      </div>
      <div class="field">
        <label>项目 / 比赛</label>
        <textarea v-model="form.projects" rows="3" placeholder="如：大创、比赛 A"></textarea>
      </div>
      
      <!-- 性格标签（由测试自动生成，也可手动编辑） -->
      <div class="field">
        <label>
          性格标签
          <span class="auto-hint" v-if="personalityFilled">已自动生成，可手动调整</span>
        </label>
        <textarea v-model="form.traits" rows="3" placeholder="完成性格测试后将自动生成，如：活泼开朗、温柔体贴"></textarea>
      </div>

      <button type="button" class="btn btn-primary" @click="save">保存</button>
    </div>

    <!-- 性格测试模态框 -->
    <Teleport to="body">
      <div v-if="showPersonalityModal" class="modal-overlay" @click.self="closePersonalityModal">
        <div class="modal-content">
          <div class="modal-header">
            <h3>🧠 性格测试</h3>
            <button type="button" class="modal-close" @click="closePersonalityModal">×</button>
          </div>
          
          <div class="modal-body">
            <p class="modal-intro">选择测试方式，系统将根据你的回答自动生成性格标签</p>
            
            <div class="mode-tabs">
              <button 
                type="button" 
                class="mode-tab" 
                :class="{ active: personalityMode === 'quick' }"
                @click="personalityMode = 'quick'"
              >
                快速选择
              </button>
              <button 
                type="button" 
                class="mode-tab" 
                :class="{ active: personalityMode === 'questionnaire' }"
                @click="personalityMode = 'questionnaire'"
              >
                10题问卷
              </button>
            </div>

            <!-- 快速选择模式 -->
            <div v-if="personalityMode === 'quick'" class="quick-mode">
              <p class="mode-desc">快速选择你认为自己最符合的描述程度</p>
              <div class="quick-items">
                <div class="quick-item">
                  <label>外向性（社交活跃度）</label>
                  <div class="quick-scale">
                    <span class="scale-label">内向</span>
                    <input 
                      type="range" 
                      min="1" 
                      max="5" 
                      v-model.number="bigfiveQuick.extro"
                      class="slider"
                    />
                    <span class="scale-label">外向</span>
                    <span class="scale-value">{{ bigfiveQuick.extro }}</span>
                  </div>
                  <p class="scale-hint">{{ getDimDescription('extro', bigfiveQuick.extro) }}</p>
                </div>
                
                <div class="quick-item">
                  <label>宜人性（与人和善度）</label>
                  <div class="quick-scale">
                    <span class="scale-label">理性</span>
                    <input 
                      type="range" 
                      min="1" 
                      max="5" 
                      v-model.number="bigfiveQuick.agreeableness"
                      class="slider"
                    />
                    <span class="scale-label">温和</span>
                    <span class="scale-value">{{ bigfiveQuick.agreeableness }}</span>
                  </div>
                  <p class="scale-hint">{{ getDimDescription('agreeableness', bigfiveQuick.agreeableness) }}</p>
                </div>
                
                <div class="quick-item">
                  <label>尽责性（做事靠谱度）</label>
                  <div class="quick-scale">
                    <span class="scale-label">随性</span>
                    <input 
                      type="range" 
                      min="1" 
                      max="5" 
                      v-model.number="bigfiveQuick.conscientiousness"
                      class="slider"
                    />
                    <span class="scale-label">严谨</span>
                    <span class="scale-value">{{ bigfiveQuick.conscientiousness }}</span>
                  </div>
                  <p class="scale-hint">{{ getDimDescription('conscientiousness', bigfiveQuick.conscientiousness) }}</p>
                </div>
                
                <div class="quick-item">
                  <label>神经质（情绪稳定度）</label>
                  <div class="quick-scale">
                    <span class="scale-label">稳定</span>
                    <input 
                      type="range" 
                      min="1" 
                      max="5" 
                      v-model.number="bigfiveQuick.neuroticism"
                      class="slider"
                    />
                    <span class="scale-label">敏感</span>
                    <span class="scale-value">{{ bigfiveQuick.neuroticism }}</span>
                  </div>
                  <p class="scale-hint">{{ getDimDescription('neuroticism', bigfiveQuick.neuroticism) }}</p>
                </div>
                
                <div class="quick-item">
                  <label>开放性（思维开放度）</label>
                  <div class="quick-scale">
                    <span class="scale-label">务实</span>
                    <input 
                      type="range" 
                      min="1" 
                      max="5" 
                      v-model.number="bigfiveQuick.openness"
                      class="slider"
                    />
                    <span class="scale-label">开放</span>
                    <span class="scale-value">{{ bigfiveQuick.openness }}</span>
                  </div>
                  <p class="scale-hint">{{ getDimDescription('openness', bigfiveQuick.openness) }}</p>
                </div>
              </div>
              
              <!-- 预览生成的性格标签 -->
              <div class="traits-preview">
                <p class="preview-title">将生成的性格标签：</p>
                <div class="preview-tags">
                  {{ generateTraits(bigfiveQuick) }}
                </div>
              </div>
            </div>

            <!-- 问卷模式 -->
            <div v-else class="questionnaire-mode">
              <p class="mode-desc">请选择每题描述与你的符合程度（1=完全不符合，5=完全符合）</p>
              <div class="q-list">
                <div v-for="(q, idx) in BIG5_QUESTIONS" :key="'q' + idx" class="q-item">
                  <div class="q-text">{{ idx + 1 }}. {{ q }}</div>
                  <div class="q-options">
                    <label v-for="n in 5" :key="'v' + idx + '_' + n" class="q-option">
                      <input 
                        type="radio" 
                        :value="n" 
                        v-model="questionnaire[idx]"
                      />
                      <span>{{ n }}</span>
                    </label>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <div class="modal-footer">
            <button type="button" class="btn btn-ghost" @click="closePersonalityModal">取消</button>
            <button type="button" class="btn btn-primary" @click="submitPersonality">
              确认完成测试
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.profile-page {
  max-width: 100%;
}
@media (min-width: 768px) {
  .profile-page {
    max-width: 720px;
    margin: 0 auto;
  }
}
h2 {
  margin: 0 0 0.35rem;
}
.sub {
  color: var(--text-muted);
  font-size: 0.9rem;
  margin: 0 0 1rem;
}
.progress-wrap {
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: var(--bg-page);
  border-radius: var(--radius);
  border: 1px solid var(--border-light);
}
.progress-label {
  display: flex;
  justify-content: space-between;
  font-size: 0.88rem;
  margin-bottom: 0.5rem;
}
.pct {
  font-weight: 600;
  color: var(--jn-maroon);
}
.progress-bar {
  height: 6px;
  background: var(--border);
  border-radius: 3px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--jn-maroon), var(--jn-gold));
  border-radius: 3px;
  transition: width 0.3s;
}
.progress-hint {
  font-size: 0.8rem;
  color: var(--text-subtle);
  margin: 0.5rem 0 0;
}
.note {
  font-size: 0.88rem;
  color: var(--text-muted);
  margin: 0 0 1.25rem;
}
.ro {
  opacity: 0.9;
  cursor: not-allowed;
  background: var(--bg-page) !important;
}
.muted {
  color: var(--text-muted);
}

.warn-personality {
  border-color: rgba(245, 158, 11, 0.35);
  margin-bottom: 1rem;
}
.sub2 {
  color: var(--text-muted);
  font-size: 0.9rem;
  margin: 0.35rem 0 0.75rem;
  line-height: 1.6;
}

.ok-personality {
  border-color: rgba(34, 197, 94, 0.35);
  margin-bottom: 1rem;
  background: rgba(34, 197, 94, 0.05);
}
.ok-personality-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #16a34a;
  font-weight: 600;
}
.ok-icon {
  width: 22px;
  height: 22px;
  background: #22c55e;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
}
.personality-summary {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin: 0.5rem 0;
}

.auto-hint {
  font-size: 0.75rem;
  color: #16a34a;
  font-weight: normal;
  margin-left: 0.5rem;
}

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}
.modal-content {
  background: var(--bg-panel);
  border-radius: 16px;
  width: 100%;
  max-width: 500px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--border-light);
}
.modal-header h3 {
  margin: 0;
  font-size: 1.1rem;
}
.modal-close {
  width: 32px;
  height: 32px;
  border: none;
  background: var(--bg-page);
  border-radius: 50%;
  cursor: pointer;
  font-size: 1.5rem;
  color: var(--text-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}
.modal-close:hover {
  background: var(--border);
  color: var(--text);
}
.modal-body {
  padding: 1.25rem;
  overflow-y: auto;
  flex: 1;
}
.modal-intro {
  color: var(--text-muted);
  font-size: 0.9rem;
  margin: 0 0 1rem;
}
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1rem 1.25rem;
  border-top: 1px solid var(--border-light);
}

.mode-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.25rem;
}
.mode-tab {
  flex: 1;
  padding: 0.75rem 1rem;
  border: 2px solid var(--border);
  background: var(--bg-page);
  border-radius: 10px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-muted);
  transition: all 0.2s;
}
.mode-tab:hover {
  border-color: var(--jn-maroon);
  color: var(--jn-maroon);
}
.mode-tab.active {
  border-color: var(--jn-maroon);
  background: rgba(180, 30, 50, 0.08);
  color: var(--jn-maroon);
}
.mode-desc {
  font-size: 0.85rem;
  color: var(--text-subtle);
  margin: 0 0 1rem;
}

/* 快速选择模式 */
.quick-mode {
  animation: fadeIn 0.2s ease;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
.quick-items {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}
.quick-item label {
  display: block;
  font-weight: 600;
  font-size: 0.9rem;
  margin-bottom: 0.5rem;
}
.quick-scale {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.scale-label {
  font-size: 0.75rem;
  color: var(--text-muted);
  min-width: 28px;
}
.slider {
  flex: 1;
  height: 6px;
  -webkit-appearance: none;
  appearance: none;
  background: var(--border);
  border-radius: 3px;
  outline: none;
}
.slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  background: var(--jn-maroon);
  border-radius: 50%;
  cursor: pointer;
  transition: transform 0.2s;
}
.slider::-webkit-slider-thumb:hover {
  transform: scale(1.15);
}
.slider::-moz-range-thumb {
  width: 18px;
  height: 18px;
  background: var(--jn-maroon);
  border-radius: 50%;
  cursor: pointer;
  border: none;
}
.scale-value {
  min-width: 24px;
  text-align: center;
  font-weight: 700;
  color: var(--jn-maroon);
  background: rgba(180, 30, 50, 0.1);
  padding: 0.15rem 0.4rem;
  border-radius: 6px;
  font-size: 0.85rem;
}
.scale-hint {
  font-size: 0.75rem;
  color: var(--text-subtle);
  margin: 0.3rem 0 0;
}

/* 性格标签预览 */
.traits-preview {
  margin-top: 1.5rem;
  padding: 1rem;
  background: var(--bg-page);
  border-radius: 10px;
  border: 1px dashed var(--border);
}
.preview-title {
  font-size: 0.8rem;
  color: var(--text-subtle);
  margin: 0 0 0.5rem;
}
.preview-tags {
  font-size: 0.9rem;
  color: var(--jn-maroon);
  font-weight: 600;
  line-height: 1.6;
}

/* 问卷模式 */
.questionnaire-mode {
  animation: fadeIn 0.2s ease;
}
.q-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.q-item {
  background: var(--bg-page);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 0.85rem;
}
.q-text {
  font-size: 0.88rem;
  color: var(--text);
  margin-bottom: 0.6rem;
  line-height: 1.5;
}
.q-options {
  display: flex;
  justify-content: space-between;
  gap: 0.25rem;
}
.q-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
  cursor: pointer;
}
.q-option input {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: var(--jn-maroon);
}
.q-option span {
  font-size: 0.7rem;
  color: var(--text-muted);
}

/* 下拉 + 手动输入组合 */
.select-row {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  flex-wrap: wrap;
}
.select-row select {
  flex: 1;
  min-width: 120px;
  padding: 0.55rem 0.85rem;
  border-radius: 10px;
  border: 1px solid var(--border);
  background: var(--bg-panel);
  color: var(--text);
  font-size: 0.9rem;
  cursor: pointer;
}
.select-row input {
  flex: 1;
  min-width: 100px;
}

/* 预设标签行 */
.tag-presets {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
  margin-bottom: 0.5rem;
}
.tag {
  padding: 0.3rem 0.7rem;
  border-radius: 999px;
  border: 1.5px solid var(--border);
  background: var(--bg-panel);
  color: var(--text);
  font-size: 0.82rem;
  cursor: pointer;
  transition: all 0.15s;
}
.tag:hover {
  border-color: var(--jn-maroon);
  color: var(--jn-maroon);
}

.password-row {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}
.password-row input {
  flex: 1;
}
.toggle-pass {
  flex-shrink: 0;
  min-width: 3.3rem;
  padding-left: 0.7rem;
  padding-right: 0.7rem;
}
</style>
