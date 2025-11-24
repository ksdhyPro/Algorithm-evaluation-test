<template>
  <el-container style="height: 100vh">
    <template v-if="route.path !== '/login'">
      <el-header
        style="
          background: #0b1729;
          color: #e8ecf5;
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0 24px;
          border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        ">
        <div style="font-size: 22px; font-weight: 600; letter-spacing: 1px">
          🩺 Align Eval
        </div>
        <el-menu
          :default-active="activeMenu"
          mode="horizontal"
          router
          style="
            background-color: transparent;
            border: none;
            flex: 1;
            margin-left: 50px;
          ">
          <el-menu-item index="/" route="/">首页</el-menu-item>
          <el-menu-item index="/create" route="/create">创建评测</el-menu-item>
          <el-menu-item index="/list" route="/list">评测列表</el-menu-item>
          <el-menu-item index="/submit" route="/submit">提交任务</el-menu-item>
          <template v-if="user && user.role === 'admin'">
            <el-menu-item index="/admin" route="/admin">管理</el-menu-item>
          </template>
        </el-menu>

        <div
          style="
            margin-left: 20px;
            display: flex;
            align-items: center;
            gap: 12px;
          ">
          <template v-if="user">
            <el-dropdown trigger="click">
              <span
                class="el-dropdown-link"
                style="color: white; cursor: pointer">
                {{ user.name }}
                <i class="el-icon-arrow-down el-icon--right"></i>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click.prevent="doLogout"
                    >退出登录</el-dropdown-item
                  >
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
          <template v-else>
            <el-button type="primary" @click="$router.push('/login')"
              >登录</el-button
            >
          </template>
        </div>
      </el-header>
    </template>
    <el-main style="padding: 0">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { authApi } from "./api/auth";
import { contestApi } from "./api/contest";

const route = useRoute();
const router = useRouter();
const activeMenu = ref("/");
const user = ref(null);

watch(
  () => route.path,
  newPath => {
    activeMenu.value = newPath;
  },
  { immediate: true }
);

onMounted(async () => {
  try {
    const raw = localStorage.getItem("user");
    if (raw) {
      user.value = JSON.parse(raw);
    } else {
      // optional: try to get from backend
      // const res = await authApi.me()
      // if (res && res.code === 0) user.value = res.user
    }
  } catch (e) {
    user.value = null;
  }
});

const doLogout = async () => {
  try {
    await authApi.logout();
  } catch (e) {
    // ignore error
  }
  localStorage.removeItem("user");
  user.value = null;
  try {
    window.dispatchEvent(new Event("auth-changed"));
  } catch (e) {}
  ElMessage.success("已退出登录");
  router.push("/login");
};
</script>
<style>
html,
body {
  margin: 0;
  padding: 0;
}
</style>
<style scoped>
:deep(.el-menu) {
  background-color: transparent !important;
}

:deep(.el-menu-item) {
  color: #dce3f2 !important;
  font-weight: 500;
}

:deep(.el-menu-item:hover) {
  background-color: rgba(255, 255, 255, 0.06) !important;
}

:deep(.el-menu-item.is-active) {
  background-color: rgba(255, 255, 255, 0.12) !important;
  border-bottom-color: #50a6ff !important;
}
</style>
