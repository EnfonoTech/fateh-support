import { createRouter, createWebHashHistory, type RouteRecordRaw } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const routes: RouteRecordRaw[] = [
  { path: "/", redirect: "/items" },
  {
    path: "/login",
    name: "login",
    component: () => import("@/views/LoginView.vue"),
    meta: { public: true },
  },
  {
    path: "/items",
    name: "items",
    component: () => import("@/views/ItemsView.vue"),
    meta: { role: "viewer" },
  },
  {
    path: "/items/search",
    name: "items-search",
    component: () => import("@/views/ItemSearchView.vue"),
    meta: { role: "viewer" },
  },
  {
    path: "/items/:code",
    name: "item-detail",
    component: () => import("@/views/ItemDetailView.vue"),
    props: true,
    meta: { role: "viewer" },
  },
  {
    path: "/approvals",
    name: "approvals",
    component: () => import("@/views/ApprovalsView.vue"),
    meta: { role: "approver" },
  },
  {
    path: "/approvals/:name",
    name: "approval-detail",
    component: () => import("@/views/ApprovalDetailView.vue"),
    props: true,
    meta: { role: "approver" },
  },
  {
    path: "/my-requests",
    name: "my-requests",
    component: () => import("@/views/MyRequestsView.vue"),
    meta: { role: "viewer" },
  },
  {
    path: "/settings",
    name: "settings",
    component: () => import("@/views/SettingsView.vue"),
    meta: { role: "viewer" },
  },
  { path: "/:pathMatch(.*)*", redirect: "/items" },
];

export const router = createRouter({
  history: createWebHashHistory("/fateh/"),
  routes,
});

router.beforeEach(async (to) => {
  const auth = useAuthStore();
  if (!auth.initialized) {
    await auth.refresh();
  }
  if (to.meta.public) return true;
  if (!auth.isLoggedIn) {
    return { name: "login", query: { next: to.fullPath } };
  }
  if (to.meta.role === "approver" && !auth.isApprover) {
    return { name: "items" };
  }
  return true;
});

export default router;
