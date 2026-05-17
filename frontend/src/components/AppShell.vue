<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";
import { useBrandingStore } from "@/stores/branding";
import { useAuthStore } from "@/stores/auth";
import { useApprovalsStore } from "@/stores/approvals";
import BadgeCount from "@/components/BadgeCount.vue";

const route = useRoute();
const branding = useBrandingStore();
const auth = useAuthStore();
const approvals = useApprovalsStore();

const title = computed(() => branding.config.brand_name);

const navItems = computed(() => {
  const items: Array<{ name: string; labelKey: string; path: string; show: boolean; badge?: number; icon: string }> = [
    {
      name: "items",
      labelKey: "nav.items",
      path: "/items",
      show: auth.isViewer,
      icon: "M4 6h16M4 12h16M4 18h10",
    },
    {
      name: "approvals",
      labelKey: "nav.approvals",
      path: "/approvals",
      show: auth.isApprover,
      badge: approvals.pending,
      icon: "M20 6 9 17l-5-5",
    },
    {
      name: "my-requests",
      labelKey: "nav.my_requests",
      path: "/my-requests",
      show: auth.isViewer,
      icon: "M9 5h6v4H9zM9 13h6v6H9zM20 5h-3v4h3zM20 13h-3v6h3zM4 5h3v4H4zM4 13h3v6H4z",
    },
    {
      name: "settings",
      labelKey: "nav.settings",
      path: "/settings",
      show: true,
      icon: "M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Zm7.4-3a7.4 7.4 0 0 0-.1-1.3l2.1-1.6-2-3.5-2.5 1a7.3 7.3 0 0 0-2.2-1.3L14.3 2h-4l-.5 2.5a7.3 7.3 0 0 0-2.2 1.3l-2.5-1-2 3.5 2.1 1.6a7.4 7.4 0 0 0 0 2.6l-2.1 1.6 2 3.5 2.5-1c.66.5 1.4.95 2.2 1.3L10.3 22h4l.5-2.5a7.3 7.3 0 0 0 2.2-1.3l2.5 1 2-3.5-2.1-1.6c.07-.43.1-.86.1-1.3Z",
    },
  ];
  return items.filter((i) => i.show);
});

function isActive(path: string) {
  return route.path.startsWith(path);
}
</script>

<template>
  <div class="app-shell">
    <header class="app-header">
      <h1>{{ title }}</h1>
      <div class="row tight">
        <slot name="header-right" />
      </div>
    </header>
    <main>
      <slot />
    </main>
    <nav class="bottom-nav">
      <router-link
        v-for="item in navItems"
        :key="item.name"
        :to="item.path"
        :class="{ active: isActive(item.path) }"
      >
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
          <path :d="item.icon" />
        </svg>
        <span>{{ $t(item.labelKey) }}</span>
        <BadgeCount v-if="item.badge" :value="item.badge" class="badge-overlay" />
      </router-link>
    </nav>
  </div>
</template>
