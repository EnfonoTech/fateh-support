<script setup lang="ts">
import { ref } from "vue";
import { useAuthStore } from "@/stores/auth";
import { usePrefsStore } from "@/stores/prefs";
import { requestPushPermission, cancelPushSubscription } from "@/composables/usePush";
import { disconnectSocket } from "@/composables/useSocket";
import LangToggle from "@/components/LangToggle.vue";
import { useRouter } from "vue-router";

const auth = useAuthStore();
const prefs = usePrefsStore();
const router = useRouter();
const pushSupported = ref("serviceWorker" in navigator && "PushManager" in window);
const pushEnabled = ref("Notification" in window && Notification.permission === "granted");

async function enablePush() {
  const ok = await requestPushPermission();
  pushEnabled.value = ok;
}

async function disablePush() {
  await cancelPushSubscription();
  pushEnabled.value = false;
}

async function signOut() {
  disconnectSocket();
  await auth.logout();
  router.replace("/login");
}
</script>

<template>
  <div class="stack">
    <div class="card stack">
      <strong>{{ $t("settings.language") }}</strong>
      <LangToggle />
      <small class="text-muted">Current: {{ prefs.locale.toUpperCase() }}</small>
    </div>

    <div class="card stack">
      <strong>{{ $t("settings.push_enable") }}</strong>
      <p v-if="!pushSupported" class="text-muted">{{ $t("settings.push_disabled") }}</p>
      <button v-else-if="!pushEnabled" class="primary" @click="enablePush">{{ $t("settings.push_enable") }}</button>
      <button v-else class="ghost" @click="disablePush">{{ $t("common.cancel") }}</button>
    </div>

    <div class="card stack">
      <strong>{{ auth.fullName }}</strong>
      <small class="text-muted">{{ auth.profile?.email }}</small>
      <small class="text-muted">{{ $t("settings.version") }}: 0.1.0</small>
      <button class="danger" @click="signOut">{{ $t("settings.sign_out") }}</button>
    </div>
  </div>
</template>
