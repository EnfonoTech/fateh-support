<script setup lang="ts">
import type { PriceResult } from "@/types";
import Money from "@/components/Money.vue";

defineProps<{ prices: PriceResult }>();
</script>

<template>
  <div class="price-block">
    <div class="header row between">
      <span class="label-xs">{{ $t("items.prices") }}</span>
      <span class="mono count">{{ prices.rows.length }}</span>
    </div>
    <div v-if="prices.rows.length === 0" class="empty label-xs">
      {{ $t("items.no_results") }}
    </div>
    <div v-else class="price-list">
      <div v-for="row in prices.rows" :key="row.price_list" class="price-row">
        <div class="left">
          <div class="pl-name">{{ row.price_list_label }}</div>
          <div class="label-xs" v-if="row.valid_from">
            {{ $t("prices.valid_from") }} {{ row.valid_from }}
          </div>
          <div class="label-xs uom" v-if="row.uom">{{ row.uom }}</div>
        </div>
        <div class="right">
          <Money :value="row.price_list_rate" :currency="row.currency" bold />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.price-block {
  background: var(--paper-2);
  border: 1px solid var(--rule);
  border-radius: var(--radius);
}

.header {
  padding: 14px 16px 10px;
  border-bottom: 1px solid var(--rule);
}

.count {
  color: var(--ink-3);
  font-size: 12px;
}

.empty {
  padding: 20px 16px;
  text-align: center;
  color: var(--ink-3);
}

.price-list {
  display: flex;
  flex-direction: column;
}

.price-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  padding: 14px 16px;
  border-bottom: 1px solid var(--rule);
}

.price-row:last-child {
  border-bottom: none;
}

.pl-name {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 500;
  letter-spacing: var(--tracking-tight);
}

.left .uom {
  margin-top: 2px;
}

.right :deep(.amount) {
  font-size: 20px;
  color: var(--ink);
}
</style>
