<script setup lang="ts">
import { computed } from "vue";
import Money from "@/components/Money.vue";

const props = defineProps<{
  variancePct: number;
  varianceAmount: number;
  currency?: string | null;
}>();

const band = computed<"low" | "mid" | "high">(() => {
  const pct = Math.abs(props.variancePct || 0);
  if (pct >= 15) return "high";
  if (pct >= 5) return "mid";
  return "low";
});
</script>

<template>
  <div class="variance-banner" :class="band">
    <div class="row between">
      <span>{{ $t("approvals.variance") }}</span>
      <strong>{{ (variancePct || 0).toFixed(1) }}%</strong>
    </div>
    <div class="text-right amt">
      <Money :value="varianceAmount" :currency="currency" />
    </div>
  </div>
</template>

<style scoped>
.amt {
  font-size: 13px;
  opacity: 0.9;
  margin-top: 4px;
}
.amt :deep(.code) {
  color: inherit;
  opacity: 0.75;
}
</style>
