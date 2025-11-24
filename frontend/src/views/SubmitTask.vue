<template>
  <div class="submit-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>🚀 提交评测任务</span>
          <el-button text @click="$router.back()">← 返回</el-button>
        </div>
      </template>

      <el-row :gutter="20">
        <!-- 左侧表单 -->
        <el-col :xs="24" :md="12">
          <el-form :model="formData" label-width="100px" status-icon>
            <!-- 评测选择 -->
            <el-form-item label="选择评测">
              <el-select
                v-model="formData.contestId"
                placeholder="请选择评测"
                filterable
                @change="onContestChange">
                <el-option
                  v-for="contest in contests"
                  :key="contest.id"
                  :label="`${contest.title} (ID: ${contest.id})`"
                  :value="contest.id" />
              </el-select>
            </el-form-item>

            <!-- 镜像上传 -->
            <el-form-item label="参赛者镜像">
              <el-upload
                ref="imageUploadRef"
                drag
                action="#"
                :auto-upload="false"
                :accept="uploadConfig.accept"
                :file-list="fileList"
                @change="handleImageChange">
                <template #default>
                  <!-- <el-icon class="el-icon--upload"><CloudUpload /></el-icon> -->
                  <div class="el-upload__text">
                    将参赛者镜像文件拖到此处或 <em>点击上传</em>
                  </div>
                </template>

                <template #tip>
                  <div class="el-upload__tip">
                    仅支持 {{ uploadConfig.accept }} 文件，大小不超过
                    {{ (uploadConfig.tar_max_size / 1024 / 1024).toFixed(0) }}MB
                  </div>
                </template>
              </el-upload>
            </el-form-item>

            <!-- 按钮 -->
            <el-form-item>
              <el-button
                type="primary"
                :loading="submitting"
                :disabled="!formData.contestId || !fileList.length"
                @click="submitTask">
                {{ submitting ? "提交中..." : "提交任务" }}
              </el-button>
              <el-button @click="resetForm">重置</el-button>
            </el-form-item>

            <!-- 进度条 -->
            <!-- <el-progress
              v-if="submitting"
              :percentage="uploadProgress.toFixed(2)" /> -->
          </el-form>
        </el-col>

        <!-- 右侧评测信息 -->
        <el-col :xs="24" :md="12">
          <el-card v-if="selectedContest" class="info-card" shadow="hover">
            <template #header>
              <span>📌 评测信息</span>
            </template>

            <el-descriptions :column="1" border>
              <el-descriptions-item label="评测标题">
                {{ selectedContest.title }}
              </el-descriptions-item>

              <el-descriptions-item label="评测描述">
                {{ selectedContest.description }}
              </el-descriptions-item>

              <el-descriptions-item label="评测镜像">
                <el-tag>{{ selectedContest.image }}</el-tag>
              </el-descriptions-item>
            </el-descriptions>
          </el-card>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
// import { CloudUpload } from "@element-plus/icons-vue";
import { contestApi } from "../api/contest";

const route = useRoute();
const router = useRouter();

const contests = ref([]);
const selectedContest = ref(null);
const fileList = ref([]);
const submitting = ref(false);
const uploadProgress = ref(0);
const uploadConfig = ref({
  allowed_tar_extensions: ["tar", "tar.gz"],
  tar_max_size: 0,
  accept: ".tar,.tar.gz",
});

const formData = ref({
  contestId: route.query.contestId || null,
  participantId: null,
});

// 加载评测列表
const loadContests = async () => {
  try {
    const res = await contestApi.getContests();
    contests.value = res || [];

    if (formData.value.contestId) {
      onContestChange();
    }
  } catch (e) {
    ElMessage.error("加载评测列表失败");
  }
};

// 修改评测选择
const onContestChange = () => {
  selectedContest.value =
    contests.value.find(c => c.id === formData.value.contestId) || null;
};

// 选择上传
const handleImageChange = file => {
  if (!file) return;
  const f = file.raw || file;
  const max = uploadConfig.value.tar_max_size || 500 * 1024 * 1024;
  if ((f.size || 0) > max) {
    ElMessage.error(`文件大小不能超过 ${(max / 1024 / 1024).toFixed(0)}MB`);
    fileList.value = [];
    return;
  }
  const name = file.name || f.name || "";
  const allowed = uploadConfig.value.allowed_tar_extensions || [
    "tar",
    "tar.gz",
  ];
  const ok = allowed.some(ext =>
    name.toLowerCase().endsWith("." + ext.toLowerCase())
  );
  if (!ok) {
    ElMessage.error(`仅支持 ${allowed.map(a => "." + a).join(", ")} 文件`);
    fileList.value = [];
    return;
  }
  fileList.value = [file];
};

// 提交任务
let progressInterval = null;

const submitTask = async () => {
  if (!formData.value.contestId || !fileList.value.length) {
    ElMessage.error("请选择评测并上传镜像文件");
    return;
  }

  submitting.value = true;
  uploadProgress.value = 0;

  progressInterval = setInterval(() => {
    if (uploadProgress.value < 90) {
      uploadProgress.value += Math.random() * 20;
    }
  }, 200);

  try {
    // 自动填充 participantId 为当前登录用户（如果可用）
    try {
      const raw = localStorage.getItem("user");
      if (raw) {
        const u = JSON.parse(raw);
        formData.value.participantId =
          formData.value.participantId || u.id || u.name;
      }
    } catch (e) {}

    const fd = new FormData();
    // 后端 submit 接口使用字段名 unique_id、file，增加 participant_id
    fd.append("unique_id", formData.value.contestId);
    fd.append("file", fileList.value[0].raw);
    if (formData.value.participantId)
      fd.append("participant_id", formData.value.participantId);

    const res = await contestApi.submitTask(fd);

    uploadProgress.value = 100;

    const ahead = Math.max(res?.queue_ahead ?? (res?.queue_size ?? 1) - 1, 0);
    const msgLines = [
      "算法镜像提交成功，已进入评测队列。",
      `提交 ID：${res?.submission_id || "未知"}`,
      `当前排队：前面还有 ${ahead} 个评测任务。`,
    ];

    await ElMessageBox.alert(msgLines.join("\n"), "提交已排队", {
      confirmButtonText: "返回评测列表",
      type: "success",
    });
    router.push("/list");
  } catch (err) {
    ElMessage.error(
      "任务提交失败：" + (err?.desc || err?.message || "未知错误")
    );
  } finally {
    clearInterval(progressInterval);
    submitting.value = false;
  }
};

// 重置
const resetForm = () => {
  formData.value = {
    contestId: formData.value.contestId,
  };
  fileList.value = [];
};

// 状态信息
onMounted(loadContests);

// 加载上传配置
const loadUploadConfig = async () => {
  try {
    const res = await contestApi.getUploadConfig();
    if (res && typeof res === "object") {
      const allowedTar = res.allowed_tar_extensions || [];
      uploadConfig.value = {
        ...res,
        accept: allowedTar.map(e => "." + e).join(","),
      };
    }
  } catch (e) {
    console.error("无法获取上传配置", e);
  }
};

onMounted(() => {
  loadContests();
  loadUploadConfig();
});
</script>

<style scoped>
.submit-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  font-size: 18px;
  font-weight: bold;
}

.info-card {
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

.result-card {
  margin-bottom: 10px;
}

.result-item {
  margin-bottom: 12px;
}

.result-item p {
  margin: 0 0 6px 0;
  font-weight: bold;
}

.log-content {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 12px;
  max-height: 300px;
  white-space: pre-wrap;
  font-family: "Courier New", monospace;
}

:deep(.el-collapse-item__header) {
  font-weight: bold;
  color: #409eff;
}
</style>
