<template>
  <div class="list-container">
    <el-card style="margin-bottom: 20px">
      <template #header>
        <div class="card-header">
          <span>📋 算法评测列表</span>
          <div style="display: flex; gap: 8px; align-items: center">
            <el-button-group>
              <el-button
                :type="viewMode === 'card' ? 'primary' : 'default'"
                @click="viewMode = 'card'"
                >卡片</el-button
              >
              <el-button
                :type="viewMode === 'table' ? 'primary' : 'default'"
                @click="viewMode = 'table'"
                >表格</el-button
              >
            </el-button-group>
            <el-button type="primary" @click="$router.push('/create')"
              >+ 发起评测</el-button
            >
          </div>
        </div>
      </template>

      <el-row :gutter="20" style="margin-bottom: 20px">
        <el-col :xs="24" :sm="12" :md="8">
          <el-input
            v-model="searchText"
            placeholder="搜索评测标题..."
            clearable
            @input="filterContests">
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
      </el-row>

      <el-empty
        v-if="contests.length === 0 && !loading"
        description="暂无算法评测" />

      <el-skeleton v-if="loading" :rows="5" animated />

      <!-- 卡片视图 -->
      <el-row
        :gutter="20"
        v-if="!loading && filteredContests.length > 0 && viewMode === 'card'">
        <el-col
          :xs="24"
          :sm="12"
          :md="8"
          :lg="6"
          :xl="4"
          style="margin-bottom: 20px"
          v-for="contest in paginatedContests"
          :key="contest.id">
          <el-card class="contest-card" @click="showDetail(contest)">
            <template #header>
              <div class="contest-card-header">
                <span class="contest-id">ID: {{ contest.id }}</span>
              </div>
            </template>

            <el-image
              :src="contest.cover_image"
              style="
                width: 100%;
                /* height: 150px; */
                object-fit: cover;
                margin-bottom: 10px;
              "
              fit="cover"
              :alt="contest.title" />
            <div class="contest-title">{{ contest.title }}</div>
            <div class="contest-owner">创建人: {{ contest.owner_name }}</div>
            <div class="contest-time">
              创建时间: {{ new Date(contest.createTime).toLocaleString() }}
            </div>

            <div
              style="
                margin-top: 15px;
                padding-top: 15px;
                border-top: 1px solid #ebeef5;
              ">
              <el-row :gutter="10">
                <el-col :span="12">
                  <el-button
                    text
                    type="primary"
                    @click.stop="gotoSubmit(contest.id)">
                    提交任务
                  </el-button>
                </el-col>
                <el-col :span="12">
                  <el-button text type="info" @click.stop="showDetail(contest)">
                    查看详情
                  </el-button>
                </el-col>
              </el-row>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 表格视图 -->
      <div
        v-if="!loading && filteredContests.length > 0 && viewMode === 'table'">
        <el-table :data="paginatedContests" stripe style="width: 100%">
          <el-table-column label="封面" width="150">
            <template #default="{ row }">
              <el-image
                :src="row.cover_image"
                style="width: 100px; height: 60px; object-fit: cover"
                :alt="row.title" />
            </template>
          </el-table-column>
          <el-table-column prop="title" label="标题" />
          <el-table-column prop="owner_name" label="主办方" width="140" />
          <el-table-column prop="createTime" label="创建时间" width="160">
            <template #default="{ row }">
              {{ new Date(row.createTime).toLocaleString() }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="220">
            <template #default="{ row }">
              <el-button
                text
                type="primary"
                size="small"
                @click.stop="gotoSubmit(row.id)"
                >提交任务</el-button
              >
              <el-button
                text
                type="info"
                size="small"
                @click.stop="showDetail(row)"
                >查看详情</el-button
              >
            </template>
          </el-table-column>
        </el-table>

        <el-pagination
          style="margin-top: 20px; text-align: right"
          :page-size="pageSize"
          :pager-count="5"
          :current-page="currentPage"
          layout="prev, pager, next"
          :total="filteredContests.length"
          @current-change="currentPage = $event" />
      </div>
    </el-card>

    <!-- 详情对话框 -->
    <el-dialog
      v-model="detailVisible"
      :title="selectedContest?.title"
      width="70%">
      <div v-if="selectedContest">
        <el-descriptions :column="1" border style="margin-bottom: 20px">
          <el-descriptions-item label="评测 ID">
            {{ selectedContest.id }}
          </el-descriptions-item>
          <el-descriptions-item label="举办方">
            {{
              selectedContest.owner_name || selectedContest.owner_id || "系统"
            }}
          </el-descriptions-item>
          <el-descriptions-item label="标题">
            {{ selectedContest.title }}
          </el-descriptions-item>
          <el-descriptions-item label="评测描述">
            <div class="contest-description-text">
              {{ selectedContest.description }}
            </div>
          </el-descriptions-item>
        </el-descriptions>

        <!-- 提交列表 -->
        <el-divider />
        <div style="font-weight: bold; margin-bottom: 12px">
          📊 算法提交列表
        </div>
        <el-skeleton v-if="submissionsLoading" :rows="3" animated />
        <el-empty v-else-if="submissions.length === 0" description="暂无提交" />
        <el-table v-else :data="submissions" stripe style="width: 100%">
          <el-table-column prop="participant_id" label="用户ID" width="100" />
          <el-table-column prop="participant_name" label="用户名" width="100" />
          <el-table-column prop="submission_time" label="提交时间" width="180">
            <template #default="{ row }">
              {{ formatSubmissionTime(row.submission_time) }}
            </template>
          </el-table-column>
          <el-table-column label="评测状态" width="140">
            <template #default="{ row }">
              <el-tag :type="statusTagType(row.status_code)" effect="plain">
                {{ statusText(row.status_code) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="评测结果" show-overflow-tooltip>
            <template #default="{ row }">
              <el-button
                text
                type="primary"
                size="small"
                @click="viewSubmissionResult(row)">
                {{ row.organizer_results ? "查看" : "暂无结果" }}
              </el-button>
              <el-button
                v-if="row.organizer_results"
                text
                type="primary"
                size="small"
                @click="exportPDF(row)">
                导出报告
              </el-button>
              <el-loading v-if="exportLoading"></el-loading>
            </template>
          </el-table-column>
          <el-table-column label="参赛者镜像日志" width="160">
            <template #default="{ row }">
              <el-popover
                trigger="click"
                :width="400"
                v-if="row.participant_logs">
                <template #reference>
                  <el-button text type="primary" size="small">查看</el-button>
                </template>
                <pre
                  style="
                    background: #f5f5f5;
                    padding: 12px;
                    border-radius: 4px;
                    max-height: 300px;
                    overflow-y: auto;
                    font-size: 12px;
                    font-family: 'Courier New', monospace;
                  "
                  >{{ row.participant_logs }}</pre
                >
              </el-popover>
              <span v-else>暂无</span>
            </template>
          </el-table-column>
          <el-table-column label="主办方镜像日志" width="160">
            <template #default="{ row }">
              <el-popover
                trigger="click"
                :width="400"
                v-if="row.organizer_logs">
                <template #reference>
                  <el-button text type="success" size="small">查看</el-button>
                </template>
                <pre
                  style="
                    background: #f5f5f5;
                    padding: 12px;
                    border-radius: 4px;
                    max-height: 300px;
                    overflow-y: auto;
                    font-size: 12px;
                    font-family: 'Courier New', monospace;
                  "
                  >{{ row.organizer_logs }}</pre
                >
              </el-popover>
              <span v-else>暂无</span>
            </template>
          </el-table-column>
          <el-table-column label="参赛者镜像输出" width="220">
            <template #default="{ row }">
              <el-popover
                trigger="click"
                :width="400"
                v-if="
                  row.participant_output_results || row.participant_output_path
                ">
                <template #reference>
                  <el-button text type="warning" size="small">查看</el-button>
                </template>
                <!-- <div style="margin-bottom: 8px" v-if="row.participant_output_path">
                  <el-tag type="info" effect="plain">
                    {{ row.participant_output_path }}
                  </el-tag>
                </div> -->
                <pre
                  v-if="row.participant_output_results"
                  style="
                    background: #fff7e6;
                    padding: 12px;
                    border-radius: 4px;
                    max-height: 300px;
                    overflow-y: auto;
                    font-size: 12px;
                    font-family: 'Courier New', monospace;
                  "
                  >{{
                    typeof row.participant_output_results === "string"
                      ? row.participant_output_results
                      : JSON.stringify(row.participant_output_results, null, 2)
                  }}</pre
                >
                <div v-else>未找到 results.json</div>
              </el-popover>
              <span v-else>暂无输出</span>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
        <el-button type="primary" @click="gotoSubmit(selectedContest.id)"
          >提交任务</el-button
        >
      </template>
    </el-dialog>

    <!-- 评测结果详情对话框 -->
    <el-dialog v-model="resultDialogVisible" title="评测结果详情" width="80%">
      <div v-if="currentResult">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="评测名称">
            {{ selectedContest.title }}
          </el-descriptions-item>
          <el-descriptions-item label="评测 ID">
            {{ selectedContest.id }}
          </el-descriptions-item>
          <el-descriptions-item label="提交时间">
            {{ formatSubmissionTime(currentResult.submission_time) }}
          </el-descriptions-item>
          <el-descriptions-item label="CPU使用">
            {{ currentRunTime.cpu }}%
          </el-descriptions-item>
          <el-descriptions-item label="内存使用">
            {{ currentRunTime.memory }}MB
          </el-descriptions-item>
          <el-descriptions-item label="执行耗时">
            {{ currentRunTime.runtime }}s
          </el-descriptions-item>
        </el-descriptions>

        <el-divider></el-divider>
        <el-table :data="currentResult.indicator" style="width: 100%">
          <el-table-column prop="key" label="测试指标" width="200" />
          <el-table-column prop="value" label="值" />
        </el-table>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { useRouter } from "vue-router";
import { Search } from "@element-plus/icons-vue";
import { contestApi } from "../api/contest";
import { generateEvalReport } from "../utils/pdf";

const router = useRouter();
const loading = ref(true);
const contests = ref([]);
const searchText = ref("");
const currentPage = ref(1);
const pageSize = 9;
const viewMode = ref("card");
const detailVisible = ref(false);
const resultDialogVisible = ref(false);
const selectedContest = ref(null);
const submissions = ref([]);
const submissionsLoading = ref(false);
const currentResult = ref(null);
const currentRunTime = ref({});
const exportLoading = ref(false);
const filteredContests = computed(() => {
  if (!searchText.value) return contests.value;
  return contests.value.filter(contest =>
    contest.title.toLowerCase().includes(searchText.value.toLowerCase())
  );
});

const paginatedContests = computed(() => {
  const start = (currentPage.value - 1) * pageSize;
  const end = start + pageSize;
  return filteredContests.value.slice(start, end);
});

const loadContests = async () => {
  loading.value = true;
  try {
    const response = await contestApi.getContests();
    // request.js 已经返回 response.data，所以这里直接使用返回值
    contests.value = response || [];
  } catch (error) {
    ElMessage.error("加载评测列表失败");
    console.error(error);
  } finally {
    loading.value = false;
  }
};

const filterContests = () => {
  currentPage.value = 1;
};

const loadSubmissions = async contestId => {
  submissionsLoading.value = true;
  try {
    const response = await contestApi.getContestSubmissions(contestId);
    submissions.value = response || [];
  } catch (error) {
    ElMessage.error("加载提交列表失败");
    submissions.value = [];
  } finally {
    submissionsLoading.value = false;
  }
};

const showDetail = async contest => {
  selectedContest.value = contest;
  detailVisible.value = true;
  await loadSubmissions(contest.id);
};

const gotoSubmit = contestId => {
  router.push({ path: "/submit", query: { contestId } });
};

// 格式化提交时间戳为本地时间字符串
const formatSubmissionTime = timestamp => {
  if (!timestamp) return "-";
  try {
    const date = new Date(timestamp);
    return date.toLocaleString("zh-CN", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch (e) {
    return timestamp;
  }
};

const statusText = code => {
  const numCode = typeof code === "number" ? code : parseInt(code, 10);
  if (code === "QUEUED") return "排队中";
  if (code === "RUNNING") return "评测中";
  return (
    {
      0: "评测成功",
      1: "评测超时",
      2: "容器错误",
      3: "执行出错",
    }[numCode] || "未知状态"
  );
};

const statusTagType = code => {
  if (code === "QUEUED") return "warning";
  if (code === "RUNNING") return "info";
  const numCode = typeof code === "number" ? code : parseInt(code, 10);
  return (
    { 0: "success", 1: "warning", 2: "danger", 3: "danger" }[numCode] || "info"
  );
};

const viewSubmissionResult = async row => {
  currentResult.value = {
    submission_time: row.submission_time,
    indicator: row.organizer_results?.indicator || [],
    runtimeInfo: row.organizer_results?.runtimeInfo || [],
  };
  currentRunTime.value = row.organizer_results?.runtimeInfo;
  resultDialogVisible.value = true;
};

const exportPDF = async row => {
  exportLoading.value = true;
  currentResult.value = {
    submission_time: row.submission_time,
    indicator: row.organizer_results?.indicator || [],
    runtimeInfo: row.organizer_results?.runtimeInfo || [],
  };
  currentRunTime.value = row.organizer_results?.runtimeInfo;
  const data = {
    indicator: currentResult.value.indicator,
    runtimeInfo: currentResult.value.runtimeInfo,
    evalId: selectedContest.value.id,
    evalTime: new Date(selectedContest.value.createTime).toLocaleString(),
    evalName: selectedContest.value.title,
    organizer: selectedContest.value.owner_name || "系统",
  };
  const blob = await generateEvalReport(data);
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download =
    selectedContest.value.title +
    new Date(selectedContest.value.createTime).toLocaleString() +
    ".pdf";
  a.click();
  exportLoading.value = false;
};

onMounted(() => {
  loadContests();
});
</script>

<style scoped>
.list-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 18px;
  font-weight: bold;
}

.contest-card {
  cursor: pointer;
  transition: all 0.3s ease;
  height: 100%;
}

.contest-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
}

.contest-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.contest-id {
  display: inline-block;
  background-color: #f0f9ff;
  color: #409eff;
  padding: 4px 8px;
  border-radius: 2px;
  font-size: 12px;
  font-weight: bold;
}

.contest-title {
  font-size: 16px;
  font-weight: bold;
  color: #333;
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.contest-owner {
  font-size: 14px;
  color: #666;
  margin-bottom: 4px;
}

.contest-time {
  font-size: 12px;
  color: #999;
}

.contest-description {
  font-size: 13px;
  color: #666;
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  max-height: 40px;
  line-clamp: 2;
}

.contest-description-text {
  white-space: pre-wrap;
  line-height: 1.6;
  font-size: 13px;
  color: #333;
  min-height: 60px;
}

.contest-dataset-type {
  font-size: 13px;
  color: #606266;
}
</style>
