<template>
  <div class="admin-layout">
    <el-menu
      class="admin-menu"
      :default-active="activeMenu"
      @select="activeMenu = $event"
      style="width: 200px; min-width: 200px">
      <el-menu-item index="user">用户管理</el-menu-item>
      <el-menu-item index="contest">评测项目管理</el-menu-item>
      <el-menu-item index="info">服务器信息</el-menu-item>
    </el-menu>
    <div class="admin-content">
      <template v-if="activeMenu === 'user'">
        <h2>新增用户</h2>
        <el-form :model="form" label-width="80px" style="max-width: 400px">
          <el-form-item label="用户名">
            <el-input v-model="form.name" placeholder="用户名"></el-input>
          </el-form-item>
          <el-form-item label="密码">
            <el-input
              v-model="form.password"
              type="password"
              placeholder="密码"></el-input>
          </el-form-item>
          <el-form-item label="角色">
            <el-select v-model="form.role" placeholder="请选择角色">
              <el-option label="普通用户" value="user"></el-option>
              <el-option label="管理员" value="admin"></el-option>
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="addUser">添加用户</el-button>
          </el-form-item>
        </el-form>
        <el-divider></el-divider>
        <h3>用户列表</h3>
        <el-table :data="users" style="width: 100%">
          <el-table-column prop="id" label="ID" width="120" />
          <el-table-column prop="name" label="用户名" />
          <el-table-column prop="role" label="角色" />
          <el-table-column label="操作" width="100">
            <template #default="scope">
              <el-button
                type="danger"
                size="small"
                @click="deleteUser(scope.row.id)"
                >删除</el-button
              >
            </template>
          </el-table-column>
        </el-table>
      </template>
      <template v-else-if="activeMenu === 'contest'">
        <h2>评测项目管理</h2>
        <el-table :data="contests" style="width: 100%">
          <el-table-column prop="id" label="项目ID" width="180" />
          <el-table-column prop="title" label="标题" />
          <el-table-column prop="owner_name" label="主办方" />
          <el-table-column prop="created_at" label="创建时间" />
          <el-table-column label="操作" width="100">
            <template #default="scope">
              <el-button
                type="danger"
                size="small"
                @click="deleteContest(scope.row.id)"
                >删除</el-button
              >
            </template>
          </el-table-column>
        </el-table>
      </template>
      <template v-else-if="activeMenu === 'info'">
        <!-- 磁盘信息显示：可用 / 总量，右侧用 el-slider 表示剩余百分比 -->
        <div
          v-if="diskAvailable"
          style="display: flex; align-items: center; gap: 8px; color: #000">
          <div style="font-size: 12px">
            磁盘:已用: {{ diskUsedGB }} / {{ diskTotalGB }}
          </div>
          <el-progress
            :percentage="Number(diskPercent)"
            :stroke-width="10"
            :color="diskColor"
            style="width: 160px" />
        </div>
        <div v-else style="color: #cfe8ff; font-size: 12px">磁盘: N/A</div>
      </template>
    </div>
  </div>
</template>

<script setup>
const activeMenu = ref("user");
const deleteUser = async id => {
  if (!id) return;
  try {
    const res = await adminApi.deleteUser(id);
    if (res && res.code === 0) {
      ElMessage.success("删除成功");
      loadUsers();
    } else {
      ElMessage.error(res.desc || "删除失败");
    }
  } catch (e) {
    ElMessage.error("删除用户失败");
  }
};
import { ref, onMounted, computed, onBeforeUnmount } from "vue";
import { ElMessage } from "element-plus";
import { adminApi } from "../api/admin";
import { contestApi } from "../api/contest";

const form = ref({ name: "", password: "", role: "user" });
const users = ref([]);
const contests = ref([]);
// 磁盘信息
const diskFreeBytes = ref(null);
const diskTotalBytes = ref(null);
const diskPercent = ref(0);
const diskAvailable = ref(false);
let diskTimer = null;
let visibilityHandler = null;
const POLL_INTERVAL_MS = 30 * 1000; // 30 秒轮询间隔

const diskTotalGB = computed(() => {
  if (!diskTotalBytes.value) return "N/A";
  return (diskTotalBytes.value / 1024 / 1024 / 1024).toFixed(2) + " GB";
});

const diskUsedGB = computed(() => {
  if (
    diskTotalBytes.value == null ||
    diskFreeBytes.value == null ||
    !diskAvailable.value
  )
    return "N/A";
  const usedBytes = diskTotalBytes.value - diskFreeBytes.value;
  return (usedBytes / 1024 / 1024 / 1024).toFixed(2) + " GB";
});

// 动态颜色（基于已用百分比）：<=70% 绿色，(70,90] 橙色，>90% 红色
const diskColor = computed(() => {
  const p = Number(diskPercent.value || 0);
  if (p <= 70) return "#67C23A"; // green
  if (p <= 90) return "#E6A23C"; // orange
  return "#F56C6C"; // red
});

// 监听同一页面内的登录/登出事件，实时更新 header
const handler = () => {
  try {
    const raw = localStorage.getItem("user");
    user.value = raw ? JSON.parse(raw) : null;
  } catch (e) {
    user.value = null;
  }
};
window.addEventListener("auth-changed", handler);
// 在组件卸载时移除监听
onBeforeUnmount(() => {
  window.removeEventListener("auth-changed", handler);
  if (visibilityHandler) {
    document.removeEventListener("visibilitychange", visibilityHandler);
    visibilityHandler = null;
  }
  if (diskTimer) {
    clearInterval(diskTimer);
    diskTimer = null;
  }
});

const loadUsers = async () => {
  try {
    const res = await adminApi.getUsers();
    if (res && Array.isArray(res)) users.value = res;
  } catch (e) {
    ElMessage.error("获取用户列表失败");
  }
};

const addUser = async () => {
  if (!form.value.name || !form.value.password || !form.value.role) {
    ElMessage.error("请填写完整信息");
    return;
  }
  try {
    const res = await adminApi.addUser(form.value);
    if (res && res.code === 0) {
      ElMessage.success("添加成功");
      form.value = { name: "", password: "", role: "user" };
      loadUsers();
    } else {
      ElMessage.error(res.desc || "添加失败");
    }
  } catch (e) {
    ElMessage.error("添加用户失败");
  }
};

const loadContests = async () => {
  try {
    const res = await contestApi.getContests();
    if (Array.isArray(res)) {
      contests.value = res;
    } else if (res && Array.isArray(res.data)) {
      contests.value = res.data;
    }
  } catch (e) {
    ElMessage.error("获取项目列表失败");
  }
};

const deleteContest = async id => {
  if (!id) return;
  try {
    const res = await contestApi.deleteContest(id);
    if (res && res.code === 0) {
      ElMessage.success("项目已删除");
      loadContests();
    } else {
      ElMessage.error(res.desc || "删除失败");
    }
  } catch (e) {
    ElMessage.error("删除项目失败");
  }
};

// 拉取磁盘信息并周期更新
const fetchDiskInfo = async () => {
  try {
    const res = await contestApi.getDiskInfo();
    if (res) {
      const d = res;
      if (d.total_bytes != null && d.free_bytes != null) {
        diskTotalBytes.value = d.total_bytes;
        diskFreeBytes.value = d.free_bytes;
        // 计算已用百分比：优先使用后端给出的 free_percent（如果有），否则按字节计算
        if (d.free_percent != null) {
          diskPercent.value = Math.round(100 - Number(d.free_percent));
        } else {
          diskPercent.value = Math.round(
            ((d.total_bytes - d.free_bytes) / d.total_bytes) * 100
          );
        }
        diskAvailable.value = true;
      } else {
        diskAvailable.value = false;
      }
    }
  } catch (e) {
    diskAvailable.value = false;
  }
};
onMounted(() => {
  loadUsers();
  loadContests();

  // 首次拉取并开始定时
  fetchDiskInfo();
  // 在定时器回调中检查页面可见性，避免在标签页不可见时频繁请求
  diskTimer = setInterval(() => {
    try {
      if (typeof document !== "undefined" && document.hidden) return;
    } catch (e) {
      // ignore
    }
    fetchDiskInfo();
  }, POLL_INTERVAL_MS);

  // 页面从不可见切换到可见时，立即拉取一次
  visibilityHandler = () => {
    try {
      if (!document.hidden) fetchDiskInfo();
    } catch (e) {
      // ignore
    }
  };
  document.addEventListener("visibilitychange", visibilityHandler);
});
</script>

<style scoped>
.admin-menu {
  min-width: 200px;
  border-right: 1px solid #eee;
}
.admin-menu :deep(.el-menu-item) {
  color: #333 !important;
  font-weight: 500;
}
.admin-menu :deep(.el-menu-item.is-active) {
  color: #409eff !important;
  background: #f5f7fa !important;
}
.admin-menu :deep(.el-menu-item:hover) {
  color: #409eff !important;
  background: #f0f6ff !important;
}
.admin-layout {
  display: flex;
  flex-direction: row;
  gap: 0;
  padding: 32px;
}
.admin-menu {
  min-width: 200px;
  border-right: 1px solid #eee;
}
.admin-content {
  flex: 1;
  padding-left: 32px;
}
</style>
