<template>
  <div class="home-page">
    <section class="hero">
      <div class="hero-content">
        <p class="hero-tag">医学智能 · 算法验证 · 临床转化</p>
        <h1>医学人工智能算法验证与评估平台</h1>
        <p class="hero-subtitle">
          汇聚临床真实世界数据、遵循国际/国家标准化评估体系与多级安全算力，为医学影像、病理诊断等智能算法提供可信、严谨、可复现的第三方验证服务。
        </p>
        <div class="hero-actions">
          <el-button type="primary" size="large" @click="goToPage('/create')">
            发起医学算法验证
          </el-button>
          <el-button size="large" @click="goToPage('/list')"
            >浏览评估项目</el-button
          >
        </div>
      </div>
      <div class="hero-figure">
        <img :src="img" alt="" srcset="" />
      </div>
    </section>

    <section class="stats">
      <div class="stat-card" v-for="item in stats" :key="item.label">
        <div class="stat-value">{{ item.value }}</div>
        <div class="stat-label">{{ item.label }}</div>
      </div>
    </section>

    <section class="actions">
      <el-row :gutter="24">
        <el-col :xs="24" :md="12">
          <el-card
            shadow="hover"
            class="action-card"
            @click="goToPage('/create')">
            <div class="action-icon">🏥</div>
            <h3>机构发起验证流程</h3>
            <p>
              医院/机构上传需要评估的算法和临床标准数据集，设定核心性能指标，发起一个符合临床要求的验证项目。
            </p>
          </el-card>
        </el-col>
        <el-col :xs="24" :md="12">
          <el-card
            shadow="hover"
            class="action-card"
            @click="goToPage('/submit')">
            <div class="action-icon">🧠</div>
            <h3>参评团队提交流程</h3>
            <p>
              算法团队提交算法程序包（容器镜像），平台自动分配安全算力，执行验证并返回详细的性能报告和操作记录。
            </p>
          </el-card>
        </el-col>
      </el-row>
    </section>

    <section class="highlights">
      <h2>严谨评估体系</h2>
      <el-row :gutter="20">
        <el-col :xs="24" :md="8" v-for="item in highlights" :key="item.title">
          <el-card shadow="never" class="highlight-card">
            <div class="highlight-icon">{{ item.icon }}</div>
            <h4>{{ item.title }}</h4>
            <p>{{ item.desc }}</p>
          </el-card>
        </el-col>
      </el-row>
    </section>

    <section class="process">
      <h2>标准化验证流程</h2>
      <el-steps :active="4" finish-status="success">
        <el-step
          v-for="(step, index) in steps"
          :key="index"
          :title="step.title"
          :description="step.desc" />
      </el-steps>
    </section>

    <!-- <section class="system-card">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>平台运行状态</span>
            <el-tag type="info">{{ backendStatus }}</el-tag>
          </div>
        </template>
        <el-row :gutter="20">
          <el-col :xs="24" :md="12">
            <div class="info-item">
              <div class="info-label">平台版本</div>
              <div class="info-value">Medical AI Eval · v1.0</div>
            </div>
          </el-col>
          <el-col :xs="24" :md="12">
            <div class="info-item">
              <div class="info-label">框架栈</div>
              <div class="info-value">Flask · Vue3 · Docker</div>
            </div>
          </el-col>
        </el-row>
      </el-card>
    </section> -->
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { contestApi } from "../api/contest";
import img from "../assets/1.jpg";
const router = useRouter();
const backendStatus = ref("✅ 已连接");

const stats = [
  { value: "多模态场景", label: "覆盖影像、病理、基因等典型医学 AI 评估场景" },
  { value: "规范化流程", label: "统一的容器镜像验证与结果回收规范" },
  { value: "安全隔离", label: "验证全程在符合医疗安全标准的沙箱环境中运行" },
  { value: "弹性架构", label: "支持按需扩展算力资源与大规模验证任务" },
];

const highlights = [
  {
    icon: "🔐",
    title: "医疗级数据安全隔离",
    desc: "遵循《网络安全法》与医疗数据安全规范，容器全程沙箱运行，确保数据资产安全合规。",
  },
  {
    icon: "📑",
    title: "临床指标权威可信",
    desc: "覆盖敏感度、特异度、AUC、Dice 等完整临床评估指标体系，验证报告一键生成。",
  },
  {
    icon: "⚙️",
    title: "全流程自动化复现",
    desc: "容器运行、算力调度、结果产出全自动化，确保每次评估结果的客观一致性。",
  },
];

const steps = [
  {
    title: "项目创建与配置",
    desc: "定义医学应用场景、上传容器镜像与标准数据集",
  },
  { title: "开放参评与审核", desc: "算法团队完成技术方案确认后，提交评测" },
  {
    title: "安全算力执行与监控",
    desc: "沙箱容器运行，实时采集性能指标与审计日志",
  },
  {
    title: "生成正式评估报告",
    desc: "自动汇总结果，导出权威验证证书与完整审计轨迹",
  },
];

const goToPage = path => {
  router.push(path);
};

const checkBackend = async () => {
  try {
    await contestApi.getContests();
    backendStatus.value = "✅ 已连接";
  } catch (error) {
    backendStatus.value = "❌ 连接失败";
  }
};

checkBackend();
</script>

<style scoped>
.home-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 30px 0 80px;
}

.hero {
  display: flex;
  gap: 40px;
  padding: 40px;
  border-radius: 24px;
  background: linear-gradient(135deg, #0f3d91 0%, #0b6fb8 55%, #0f92d1 100%);
  color: #fff;
  margin-bottom: 32px;
}

.hero-content {
  flex: 1;
}

.hero-tag {
  letter-spacing: 4px;
  font-size: 13px;
  opacity: 0.85;
  margin-bottom: 14px;
  text-transform: uppercase;
}

.hero h1 {
  font-size: 38px;
  margin: 0 0 16px;
  line-height: 1.3;
}

.hero-subtitle {
  font-size: 16px;
  opacity: 0.9;
  line-height: 1.8;
  margin-bottom: 24px;
}

.hero-actions {
  display: flex;
  gap: 16px;
}

.hero-figure {
  flex: 0 0 320px;
  border-radius: 18px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  background: rgba(255, 255, 255, 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 20px;
}

.figure-placeholder {
  border: 2px dashed rgba(255, 255, 255, 0.5);
  border-radius: 14px;
  padding: 40px 20px;
  font-size: 14px;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.8);
}

.stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 32px;
}

.stat-card {
  background: #0f111a;
  color: #f7f8fb;
  border-radius: 16px;
  padding: 20px;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.04);
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 6px;
}

.stat-label {
  font-size: 13px;
  opacity: 0.8;
}

.actions,
.highlights,
.process,
.system-card {
  margin-bottom: 32px;
}

.action-card {
  border-radius: 18px;
  min-height: 180px;
}

.action-card p {
  color: #606266;
  line-height: 1.8;
}

.action-icon {
  font-size: 32px;
  margin-bottom: 12px;
}

.highlights h2,
.process h2 {
  font-size: 22px;
  font-weight: 600;
  margin-bottom: 18px;
}

.highlight-card {
  border-radius: 16px;
  min-height: 170px;
  background: #f7f9fc;
}

.highlight-icon {
  font-size: 30px;
  margin-bottom: 10px;
}

.highlight-card p {
  color: #666;
  line-height: 1.6;
}

.process {
  background: #fff;
  padding: 24px;
  border-radius: 18px;
  box-shadow: 0 10px 30px rgba(15, 61, 145, 0.08);
}

.system-card .info-item {
  padding: 18px;
  background: #f5f7fb;
  border-radius: 10px;
  margin-bottom: 14px;
}

.info-label {
  font-size: 12px;
  color: #a0a5b1;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 6px;
}

.info-value {
  font-size: 16px;
  font-weight: 600;
  color: #1f2a44;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

@media (max-width: 992px) {
  .hero {
    flex-direction: column;
  }
  .hero-figure {
    width: 100%;
  }
}
</style>
