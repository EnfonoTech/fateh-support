<script setup lang="ts">
import { computed, onMounted, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { usePrefsStore } from "@/stores/prefs";
import { useApprovalsStore } from "@/stores/approvals";
import { setLocale } from "@/i18n";
import { isNative } from "@/utils/platform";
import AppShell from "@/components/AppShell.vue";
import ToastLayer from "@/components/ToastLayer.vue";

const auth = useAuthStore();
const prefs = usePrefsStore();
const approvals = useApprovalsStore();
const route = useRoute();
const router = useRouter();

onMounted(async () => {
  if (!auth.initialized) await auth.refresh();
  if (auth.isLoggedIn) {
    void approvals.refreshPending();
  }

  if (isNative()) {
    const { App: CapApp } = await import("@capacitor/app");
    CapApp.addListener("backButton", () => {
      if (route.name === "item-detail") {
        router.push({ name: "items" });
      } else if (route.name === "approval-detail") {
        router.push({ name: "approvals" });
      } else {
        CapApp.exitApp();
      }
    });
  }
});

watch(
  () => prefs.locale,
  (v) => setLocale(v),
  { immediate: true }
);

watch(
  () => auth.isLoggedIn,
  (loggedIn) => {
    if (loggedIn) void approvals.refreshPending();
  }
);

const showShell = computed(
  () => auth.isLoggedIn && route.meta.public !== true
);
</script>

<template>
  <div id="fateh-root">
    <AppShell v-if="showShell">
      <router-view />
    </AppShell>
    <template v-else>
      <router-view />
    </template>
    <ToastLayer />
  </div>
</template>

<style>
#fateh-root { min-height: 100vh; display: contents; }
</style>
