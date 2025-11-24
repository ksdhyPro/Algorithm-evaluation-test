<template>
  <div class="login-page">
    <div class="login-left">
      <video autoplay muted loop class="login-video">
        <source :src="mp4" type="video/mp4" />
        您的浏览器不支持视频播放。
      </video>
      <div class="login-left-content">
        <h2 class="left-title">AlignEval</h2>
        <p class="left-desc">
          AlignEval 是一个评估人工智能的最新技术平台，
          用于评估和在规模上比较机器学习（ML）和人工智能（AI）算法。
        </p>
      </div>
    </div>
    <div class="login-right">
      <img :src="logo" alt="Logo" class="login-logo" />
      <div class="login-card">
        <el-form :model="form" label-width="0px">
          <el-form-item label="">
            <input
              class="cus-input"
              v-model="form.username"
              placeholder="ID 或 用户名" />
          </el-form-item>
          <el-form-item label="">
            <input
              v-model="form.password"
              type="password"
              placeholder="密码"
              class="cus-input" />
          </el-form-item>
          <el-form-item>
            <button
              class="login-btn"
              type="button"
              @click="doLogin"
              :loading="loading">
              登录
            </button>
          </el-form-item>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { authApi } from "../api/auth";
import mp4 from "../assets/1080.mp4";
import logo from "../assets/logo.png";
const router = useRouter();
const loading = ref(false);
const form = ref({ username: "", password: "" });

const doLogin = async () => {
  if (!form.value.username || !form.value.password) {
    ElMessage.error("请输入账号和密码");
    return;
  }
  loading.value = true;
  try {
    const res = await authApi.login({
      username: form.value.username,
      password: form.value.password,
    });
    if (res && res.code === 0) {
      localStorage.setItem("user", JSON.stringify(res.user || {}));
      try {
        window.dispatchEvent(new Event("auth-changed"));
      } catch (e) {}
      ElMessage.success("登录成功");
      router.push("/");
    } else {
      ElMessage.error(res.desc || "登录失败");
    }
  } catch (err) {
    ElMessage.error(err?.desc || err?.message || "登录请求失败");
    console.error(err);
  } finally {
    loading.value = false;
  }
};

const reset = () => {
  form.value.username = "";
  form.value.password = "";
};
</script>

<style scoped>
.login-page {
  display: flex;
  height: 100vh;
}

.login-left {
  flex: 1;
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
}

.login-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.login-left-content {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  color: #fff;
  background: rgba(0, 0, 0, 0.35);
  padding: 32px 24px;
  border-radius: 16px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.18);
}
.left-title {
  font-size: 64px;
  font-weight: 700;
  margin-bottom: 36px;
}
.left-desc {
  font-size: 16px;
  line-height: 1.7;
}

.login-right {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 40px;
  background-color: #242424;
}

.login-logo {
  width: 120px;
  margin-bottom: 60px;
}

.login-card {
  width: 100%;
  max-width: 400px;
}
.cus-input {
  border: none !important;
  box-shadow: none !important;
  box-sizing: border-box !important;
  width: 100%;
  padding: 14px 15px;
  border-radius: 10px;
  background-color: #2a2a2a;
  border: none;
  color: white;
  outline: none;
}
.login-btn {
  width: 100%;
  padding: 8px 10px;
  border: none;
  color: #fff;
  font-size: 16px;
  border-radius: 20px;
  background: linear-gradient(to right, #ff6a00, #ff9d00);
  cursor: pointer;
  margin-top: 10px;
}
</style>
