import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "../stores/auth";

// 路由表：公开页 + 需要登录的 /app 子路由
const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      name: "landing",
      component: () => import("../views/Landing.vue"),
    },
    {
      path: "/login",
      name: "login",
      component: () => import("../views/Login.vue"),
    },
    {
      path: "/register",
      name: "register",
      component: () => import("../views/Register.vue"),
    },
    {
      path: "/forgot-password",
      name: "forgotPassword",
      component: () => import("../views/ForgotPassword.vue"),
    },
    {
      path: "/app",
      component: () => import("../layouts/AppShell.vue"),
      meta: { requiresAuth: true },
      children: [
        { path: "", redirect: { name: "recommend" } },
        {
          path: "recommend",
          name: "recommend",
          component: () => import("../views/dashboard/RecommendView.vue"),
        },
        {
          path: "profile",
          name: "profile",
          component: () => import("../views/dashboard/ProfileView.vue"),
        },
        {
          path: "privacy",
          name: "privacy",
          component: () => import("../views/dashboard/PrivacyView.vue"),
        },
        {
          path: "friends",
          name: "friends",
          component: () => import("../views/dashboard/FriendsView.vue"),
        },
        {
          path: "history",
          name: "history",
          component: () => import("../views/dashboard/HistoryView.vue"),
        },
        {
          path: "chat/:peerId",
          name: "chat",
          component: () => import("../views/dashboard/ChatView.vue"),
          props: true,
        },
        {
          path: "user/:id",
          name: "userPublic",
          component: () => import("../views/dashboard/UserPublicView.vue"),
          props: true,
        },
      ],
    },
  ],
});

router.beforeEach(async (to) => {
  const auth = useAuthStore();
  // 首次路由跳转前尝试恢复登录态
  if (!auth.ready) {
    await auth.fetchMe();
  }
  if (to.meta.requiresAuth && !auth.user) {
    return { name: "login", query: { redirect: to.fullPath } };
  }
  return true;
});

export default router;
