import api from "./request";

// 算法评测 API
export const contestApi = {
  // 创建评测
  createContest(formData) {
    return api.post("/create", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
  },

  // 获取评测列表
  getContests() {
    return api.get("/api/contests");
  },

  // 获取上传相关的服务端配置（允许后缀与大小限制）
  getUploadConfig() {
    return api.get("/api/upload-config");
  },

  // 获取磁盘信息
  getDiskInfo() {
    return api.get("/api/disk-info");
  },

  // 提交任务
  submitTask(formData) {
    return api.post("/submit", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
      timeout: 600000, // 10分钟超时
    });
  },

  // 获取某个评测的提交列表（参赛者、主办方结果）
  getContestSubmissions(contestId) {
    return api.get(`/api/contests/${contestId}/submissions`);
  },
  deleteContest(id) {
    return api.post("/api/contests/delete", { id });
  },
};
