<script setup lang="ts">
import { usePrefsStore } from "@/stores/prefs";
const prefs = usePrefsStore();
</script>

<template>
  <button class="ghost" @click="prefs.toggle()">
    {{ prefs.locale === "ar" ? "EN" : "عربي" }}
  </button>
</template>
