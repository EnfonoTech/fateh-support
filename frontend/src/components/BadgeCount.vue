<script setup lang="ts">
defineProps<{ value: number }>();
</script>

<template>
  <span v-if="value > 0">{{ value > 99 ? "99+" : value }}</span>
</template>
