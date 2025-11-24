<template>
  <div class="create-container">
    <el-card class="create-card">
      <template #header>
        <div class="card-header">
          <span>🎨 创建算法评测</span>
        </div>
      </template>

      <el-row :gutter="24" class="create-layout">
        <el-col :xs="24" :lg="16">
          <el-form
            ref="formRef"
            :model="form"
            :rules="rules"
            label-position="top"
            @submit="handleSubmit">
            <el-row :gutter="20">
              <el-col :xs="24" :md="24">
                <el-form-item label="评测标题" prop="title">
                  <el-input
                    v-model="form.title"
                    placeholder="例如：Python 算法评测 2024"
                    clearable />
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item label="评测详情描述" prop="description">
              <el-input
                v-model="form.description"
                type="textarea"
                :rows="4"
                placeholder="描述算法评测目标、规则、数据以及评分方式..."
                clearable />
            </el-form-item>

            <el-divider>文件上传</el-divider>

            <el-row :gutter="20">
              <el-col :xs="24" :md="8">
                <el-form-item label="评测镜像" prop="image">
                  <el-upload
                    class="upload-block"
                    drag
                    action="#"
                    :auto-upload="false"
                    :on-change="handleImageChange"
                    :on-remove="handleImageRemove"
                    :accept="uploadConfig.acceptTar">
                    <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                    <div class="el-upload__text">拖拽或 <em>点击上传</em></div>
                    <template #tip>
                      <div class="el-upload__tip">
                        仅支持 {{ uploadConfig.acceptTar }}，≤{{
                          (uploadConfig.tar_max_size / 1024 / 1024).toFixed(0)
                        }}MB
                      </div>
                    </template>
                  </el-upload>
                  <div v-if="form.image" class="file-info">
                    ✓ {{ form.image.name }}
                  </div>
                </el-form-item>
              </el-col>
              <el-col :xs="24" :md="8">
                <el-form-item label="评测数据源 (source)" prop="source">
                  <el-upload
                    class="upload-block"
                    drag
                    action="#"
                    :auto-upload="false"
                    :on-change="handleSourceChange"
                    :on-remove="handleSourceRemove"
                    :accept="uploadConfig.acceptZip">
                    <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                    <div class="el-upload__text">拖拽或 <em>点击上传</em></div>
                    <template #tip>
                      <div class="el-upload__tip">
                        仅支持 {{ uploadConfig.acceptZip }}，≤{{
                          (uploadConfig.zip_max_size / 1024 / 1024).toFixed(0)
                        }}MB
                      </div>
                    </template>
                  </el-upload>
                  <div v-if="form.source" class="file-info">
                    ✓ {{ form.source.name }}
                  </div>
                </el-form-item>
              </el-col>
              <el-col :xs="24" :md="8">
                <el-form-item label="结果集 (result)" prop="result">
                  <el-upload
                    class="upload-block"
                    drag
                    action="#"
                    :auto-upload="false"
                    :on-change="handleResultChange"
                    :on-remove="handleResultRemove"
                    :accept="uploadConfig.acceptZip">
                    <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                    <div class="el-upload__text">拖拽或 <em>点击上传</em></div>
                    <template #tip>
                      <div class="el-upload__tip">
                        仅支持 {{ uploadConfig.acceptZip }}，≤{{
                          (uploadConfig.zip_max_size / 1024 / 1024).toFixed(0)
                        }}MB
                      </div>
                    </template>
                  </el-upload>
                  <div v-if="form.result" class="file-info">
                    ✓ {{ form.result.name }}
                  </div>
                </el-form-item>
              </el-col>
              <el-col :xs="24" :md="8">
                <el-form-item label="封面图" prop="coverImage">
                  <el-upload
                    class="upload-block"
                    drag
                    action="#"
                    :auto-upload="false"
                    :on-change="handleCoverImageChange"
                    :on-remove="handleCoverImageRemove"
                    :accept="uploadConfig.acceptImage">
                    <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                    <div class="el-upload__text">拖拽或 <em>点击上传</em></div>
                    <template #tip>
                      <div class="el-upload__tip">
                        仅支持 {{ uploadConfig.acceptImage }}
                      </div>
                    </template>
                  </el-upload>
                  <div v-if="form.coverImage" class="file-info">
                    ✓ {{ form.coverImage.name }}
                  </div>
                </el-form-item>
              </el-col>
            </el-row>

            <div class="form-actions">
              <el-button
                type="primary"
                @click="submitForm(formRef)"
                :loading="loading">
                {{ loading ? "创建中..." : "创建评测" }}
              </el-button>
              <el-button @click="formRef?.resetFields()" :disabled="loading">
                重置
              </el-button>
            </div>
          </el-form>
        </el-col>

        <el-col :xs="24" :lg="8">
          <div class="side-panel">
            <h4>发布须知</h4>
            <ul>
              <li>
                上传镜像文件必须小于{{
                  (uploadConfig.tar_max_size / 1024 / 1024).toFixed(0)
                }}MB。
              </li>
              <li>镜像必须能在无网络环境运行。</li>
              <li>数据集压缩包解压后目录不要含中文。</li>
              <li>建议提交前完整跑通评测流程。</li>
            </ul>

            <h4>约定配置</h4>
            <ul>
              <li>
                上传的镜像在评测时会把参赛者输出的目录作为
                <strong style="color: red">/input</strong> 挂载至评测镜像内
              </li>
              <li>镜像运行时间要在5分钟内，否则视为失败</li>
              <li>运行限制cpu 分配 2核,请注意资源消耗</li>
            </ul>

            <el-progress
              v-if="uploadProgress > 0 && uploadProgress < 100"
              :percentage="uploadProgress.toFixed(2)"
              :stroke-width="12"
              style="margin-top: 20px" />
          </div>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { useRouter } from "vue-router";
import { UploadFilled } from "@element-plus/icons-vue";
import { contestApi } from "../api/contest";

const router = useRouter();
const formRef = ref();
const loading = ref(false);
const uploadProgress = ref(0);
const uploadConfig = ref({
  allowed_tar_extensions: ["tar", "tar.gz"],
  allowed_zip_extensions: ["zip"],
  allowed_image_extensions: ["jpg", "png"],
  tar_max_size: 500 * 1024 * 1024,
  zip_max_size: 500 * 1024 * 1024,
  image_max_size: 5 * 1024 * 1024,
});

const form = reactive({
  title: "",
  description: "",
  image: null,
  source: null,
  result: null,
  coverImage: null, // Added cover image field
});

const rules = {
  title: [
    { required: true, message: "请输入评测标题", trigger: "blur" },
    { min: 2, max: 100, message: "标题长度应为 2-100 个字符", trigger: "blur" },
  ],
  description: [
    { required: true, message: "请输入评测描述", trigger: "blur" },
    {
      min: 10,
      max: 1000,
      message: "描述长度应为 10-1000 个字符",
      trigger: "blur",
    },
  ],
  image: [{ required: true, message: "请选择评测镜像", trigger: "change" }],
  source: [{ required: true, message: "请选择评测数据源", trigger: "change" }],
  result: [{ required: true, message: "请选择结果集", trigger: "change" }],
  coverImage: [
    { required: true, message: "请选择封面图", trigger: "change" },
    {
      validator: (rule, value, callback) => {
        if (!value) return callback();
        const isJpgPng = /\.(jpg|png)$/.test(value.name);
        if (!isJpgPng) {
          return callback(new Error("封面图仅支持 .jpg 和 .png 格式"));
        }
        callback();
      },
      trigger: "change",
    },
  ],
};

const handleImageChange = file => {
  if (!file) return;
  const max = uploadConfig.value.tar_max_size || 500 * 1024 * 1024;
  if ((file.size || file.raw?.size) > max) {
    ElMessage.error(
      `评测镜像文件过大（最大 ${(max / 1024 / 1024).toFixed(0)}MB）`
    );
    return;
  }
  const name = file.name || file.raw?.name || "";
  const allowed = uploadConfig.value.allowed_tar_extensions || [
    "tar",
    "tar.gz",
  ];
  const ok = allowed.some(ext =>
    name.toLowerCase().endsWith("." + ext.toLowerCase())
  );
  if (!ok) {
    ElMessage.error(`只支持 ${allowed.map(a => "." + a).join(", ")} 文件`);
    return;
  }
  form.image = file.raw || file;
};

const handleImageRemove = () => {
  form.image = null;
};

const handleSourceChange = file => {
  if (!file) return;
  const max = uploadConfig.value.zip_max_size || 500 * 1024 * 1024;
  if ((file.size || file.raw?.size) > max) {
    ElMessage.error(
      `评测数据源文件过大（最大 ${(max / 1024 / 1024).toFixed(0)}MB）`
    );
    return;
  }
  const name = file.name || file.raw?.name || "";
  const allowed = uploadConfig.value.allowed_zip_extensions || ["zip"];
  const ok = allowed.some(ext =>
    name.toLowerCase().endsWith("." + ext.toLowerCase())
  );
  if (!ok) {
    ElMessage.error(`只支持 ${allowed.map(a => "." + a).join(", ")} 文件`);
    return;
  }
  form.source = file.raw || file;
};

const handleSourceRemove = () => {
  form.source = null;
};

const handleResultChange = file => {
  if (!file) return;
  const max = uploadConfig.value.zip_max_size || 500 * 1024 * 1024;
  if ((file.size || file.raw?.size) > max) {
    ElMessage.error(
      `结果集文件过大（最大 ${(max / 1024 / 1024).toFixed(0)}MB）`
    );
    return;
  }
  const name = file.name || file.raw?.name || "";
  const allowed = uploadConfig.value.allowed_zip_extensions || ["zip"];
  const ok = allowed.some(ext =>
    name.toLowerCase().endsWith("." + ext.toLowerCase())
  );
  if (!ok) {
    ElMessage.error(`只支持 ${allowed.map(a => "." + a).join(", ")} 文件`);
    return;
  }
  form.result = file.raw || file;
};

const handleResultRemove = () => {
  form.result = null;
};

const handleCoverImageChange = file => {
  if (!file) return;
  const max = uploadConfig.value.image_max_size || 5 * 1024 * 1024;
  if ((file.size || file.raw?.size) > max) {
    ElMessage.error(
      `封面图文件过大（最大 ${(max / 1024 / 1024).toFixed(1)}MB）`
    );
    return;
  }
  const name = file.name || file.raw?.name || "";
  const allowed = uploadConfig.value.allowed_image_extensions || ["jpg", "png"];
  const ok = allowed.some(ext =>
    name.toLowerCase().endsWith("." + ext.toLowerCase())
  );
  if (!ok) {
    ElMessage.error(`封面图仅支持 ${allowed.map(a => "." + a).join(", ")}`);
    return;
  }
  form.coverImage = file.raw || file;
};

const handleCoverImageRemove = () => {
  form.coverImage = null;
};

const submitForm = async formRef => {
  if (!formRef) return;
  await formRef.validate(async valid => {
    if (!valid) return;

    const formData = new FormData();
    formData.append("title", form.title);
    formData.append("description", form.description);
    formData.append("image", form.image);
    formData.append("source", form.source);
    formData.append("result", form.result);
    if (form.coverImage) {
      formData.append("cover_image", form.coverImage); // Include cover image in submission
    }

    try {
      loading.value = true;
      const response = await contestApi.createContest(formData);

      if (response && response.status === "success") {
        ElMessage.success("评测创建成功！");
        router.push("/");
      } else {
        ElMessage.error(response.data?.error || "创建失败");
      }
    } catch (error) {
      ElMessage.error("创建评测时发生错误");
    } finally {
      loading.value = false;
    }
  });
};

// 加载服务端上传配置并应用到本页面
const loadUploadConfig = async () => {
  try {
    const res = await contestApi.getUploadConfig();
    if (res && typeof res === "object") {
      const allowedTar = res.allowed_tar_extensions || [];
      const allowedZip = res.allowed_zip_extensions || [];
      const allowedImg = res.allowed_image_extensions || [];
      uploadConfig.value = {
        ...res,
        acceptTar: allowedTar.map(e => "." + e).join(","),
        acceptZip: allowedZip.map(e => "." + e).join(","),
        acceptImage: allowedImg.map(e => "." + e).join(","),
      };
    }
  } catch (e) {
    // 忽略失败，保留默认值
    console.error("无法获取上传配置", e);
  }
};

onMounted(() => {
  loadUploadConfig();
});
</script>

<style scoped>
.create-container {
  padding: 20px;
}

.create-card {
  width: 100%;
  margin: 0 auto;
}

.create-layout {
  align-items: stretch;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 18px;
  font-weight: bold;
}

.file-info {
  margin-top: 10px;
  padding: 8px 12px;
  background-color: #f0f9ff;
  border-left: 3px solid #409eff;
  color: #409eff;
  font-size: 14px;
  border-radius: 2px;
}

.upload-block {
  width: 100%;
}

.upload-block :deep(.el-upload-dragger) {
  width: 100%;
}

.upload-hint {
  padding: 16px;
  border: 1px dashed #e4e7ed;
  border-radius: 4px;
  background: #fdf6ec;
  color: #ad6700;
  font-size: 13px;
}

.form-actions {
  margin-top: 20px;
  display: flex;
  gap: 12px;
}

.side-panel {
  height: 100%;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  padding: 20px;
  background: #fafafa;
  display: flex;
  flex-direction: column;
}

.side-panel h4 {
  margin: 0 0 10px;
  font-size: 16px;
  font-weight: 600;
}

.side-panel ul {
  padding-left: 18px;
  margin: 0 0 12px;
  color: #666;
  font-size: 13px;
  line-height: 2.6;
}

.panel-alert {
  margin-top: 10px;
}

:deep(.el-form-item) {
  margin-bottom: 20px;
}
</style>
