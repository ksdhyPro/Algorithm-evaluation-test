import axios from "axios";

const API_BASE =
  import.meta.env.MODE === "development" ? "http://localhost:5000" : "/";

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
  // allow sending cookies for session-based auth
  withCredentials: true,
});

// 响应拦截：统一返回 backend 的 response.data，方便上层直接使用 {code, desc, ...}
api.interceptors.response.use(
  response => {
    // 有些后端会把结果放在 response.data
    return response.data;
  },
  error => {
    // 如果后端返回了 JSON 错误体，优先返回它，便于前端读取 code/desc
    if (error.response && error.response.data) {
      return Promise.reject(error.response.data);
    }
    return Promise.reject({ message: error.message || "Network Error" });
  }
);

export default api;
