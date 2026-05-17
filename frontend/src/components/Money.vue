<script setup lang="ts">
import { computed } from "vue";
import { splitCurrency } from "@/utils/format";
import { usePrefsStore } from "@/stores/prefs";

const props = withDefaults(
  defineProps<{
    value: number | null | undefined;
    currency?: string | null;
    digits?: number;
    bold?: boolean;
  }>(),
  { digits: 2, bold: false }
);

const prefs = usePrefsStore();

const parts = computed(() => splitCurrency(props.value, props.currency, prefs.locale, props.digits));
</script>

<template>
  <span class="money" :class="{ bold: bold, sar: parts.isSar }">
    <template v-if="parts.isSar">
      <span class="sar-symbol" aria-label="SAR"></span>
    </template>
    <template v-else>
      <span class="code">{{ parts.code }}</span>
    </template>
    <span class="amount mono">{{ parts.amount }}</span>
  </span>
</template>

<style scoped>
.money {
  display: inline-flex;
  align-items: baseline;
  gap: 4px;
  white-space: nowrap;
}

.money.bold .amount {
  font-weight: 600;
}

.code {
  font-size: 0.78em;
  font-weight: 500;
  color: var(--ink-3);
  letter-spacing: 0.04em;
}

.amount {
  font-variant-numeric: tabular-nums;
}
</style>
