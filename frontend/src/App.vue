<script setup lang="ts">
import { computed, onMounted, watch } from "vue";
import { useRoute } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { usePrefsStore } from "@/stores/prefs";
import { useApprovalsStore } from "@/stores/approvals";
import { setLocale } from "@/i18n";
import AppShell from "@/components/AppShell.vue";
import ToastLayer from "@/components/ToastLayer.vue";

const auth = useAuthStore();
const prefs = usePrefsStore();
const approvals = useApprovalsStore();
const route = useRoute();

onMounted(async () => {
  if (!auth.initialized) await auth.refresh();
  if (auth.isLoggedIn) {
    void approvals.refreshPending();
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
