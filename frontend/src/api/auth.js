import api from "./request";

export const authApi = {
  login(payload) {
    // payload: { username, password }
    return api.post("/api/login", payload);
  },
  logout() {
    return api.post("/api/logout");
  },
  me() {
    return api.get("/api/me");
  },
};
