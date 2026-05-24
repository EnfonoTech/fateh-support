<script setup lang="ts">
import { ref } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { useBrandingStore } from "@/stores/branding";
import LangToggle from "@/components/LangToggle.vue";

const email = ref("");
const password = ref("");
const submitting = ref(false);
const error = ref("");
const auth = useAuthStore();
const branding = useBrandingStore();
const router = useRouter();
const route = useRoute();

async function onSubmit() {
  error.value = "";
  submitting.value = true;
  try {
    await auth.login(email.value.trim(), password.value);
    const next = (route.query.next as string) || "/items";
    router.replace(next);
  } catch (err) {
    error.value = (err as Error).message || "Sign-in failed";
  } finally {
    submitting.value = false;
  }
}
</script>

<template>
  <div class="login-page">
    <div class="top-bar">
      <LangToggle />
    </div>

    <div class="login-card">
      <h1 class="brand">{{ branding.config.brand_name }}</h1>
      <p class="tagline" v-if="branding.config.login_tagline">{{ branding.config.login_tagline }}</p>

      <form class="form" @submit.prevent="onSubmit">
        <label class="field">
          <span>{{ $t("login.email") }}</span>
          <input v-model="email" type="text" required autocomplete="email" />
        </label>
        <label class="field">
          <span>{{ $t("login.password") }}</span>
          <input v-model="password" type="password" required autocomplete="current-password" />
        </label>
        <div class="error" v-if="error">{{ error }}</div>
        <button class="primary" type="submit" :disabled="submitting">
          <span v-if="submitting">{{ $t("common.loading") }}</span>
          <span v-else>{{ $t("login.submit") }}</span>
        </button>
      </form>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--paper);
  padding: 24px 20px;
}

.top-bar {
  display: flex;
  justify-content: flex-end;
}

.login-card {
  max-width: 380px;
  width: 100%;
  margin: auto;
  padding: 20px 0;
}

.brand {
  font-size: 28px;
  font-weight: 600;
  letter-spacing: var(--tracking-tight);
  margin: 0 0 8px;
  color: var(--ink);
}

.tagline {
  color: var(--ink-3);
  margin: 0 0 28px;
  font-size: 14px;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field > span {
  font-size: 13px;
  font-weight: 500;
  color: var(--ink-2);
}

.error {
  color: var(--danger);
  font-size: 13px;
  background: #FEE2E2;
  border: 1px solid #FECACA;
  padding: 8px 12px;
  border-radius: var(--radius);
}

.primary {
  margin-top: 8px;
}
</style>
