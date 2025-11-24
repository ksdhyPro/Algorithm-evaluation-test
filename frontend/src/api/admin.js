import api from "./request";

export const adminApi = {
  getUsers() {
    return api.get("/api/users");
  },
  addUser(payload) {
    // payload: { name, password, role }
    return api.post("/api/users/add", payload);
  },
  deleteUser(id) {
    return api.post("/api/users/delete", { id });
  },
};
