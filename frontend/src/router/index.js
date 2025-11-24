import { createRouter, createWebHistory } from "vue-router";
import Home from "../views/Home.vue";
import CreateContest from "../views/CreateContest.vue";
import ContestList from "../views/ContestList.vue";
import SubmitTask from "../views/SubmitTask.vue";
import Login from "../views/Login.vue";

const routes = [
  {
    path: "/",
    name: "Home",
    component: Home,
  },
  {
    path: "/create",
    name: "CreateContest",
    component: CreateContest,
  },
  {
    path: "/list",
    name: "ContestList",
    component: ContestList,
  },
  {
    path: "/submit",
    name: "SubmitTask",
    component: SubmitTask,
  },
  {
    path: "/login",
    name: "Login",
    component: Login,
  },
  {
    path: "/admin",
    name: "Admin",
    component: () => import("../views/Admin.vue"),
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

// 全局路由守卫：未登录则重定向到登录页面
router.beforeEach((to, from, next) => {
  try {
    const publicPaths = ["/login"];
    const userRaw = localStorage.getItem("user");
    const logged = !!userRaw;
    if (!logged && !publicPaths.includes(to.path)) {
      return next({ path: "/login" });
    }
    next();
  } catch (error) {
    next();
  }
});

export default router;
