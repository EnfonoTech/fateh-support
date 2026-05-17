<script setup lang="ts">
import type { StockResult } from "@/types";
import { formatNumber } from "@/utils/format";
import { usePrefsStore } from "@/stores/prefs";

const prefs = usePrefsStore();
defineProps<{ stock: StockResult }>();
</script>

<template>
  <div class="stock-block">
    <div class="header row between">
      <span class="label-xs">{{ $t("items.stock") }}</span>
      <span class="mono count">{{ stock.bins.length }}</span>
    </div>
    <table class="data">
      <thead>
        <tr>
          <th>{{ $t("stock.warehouse") }}</th>
          <th class="text-right">{{ $t("stock.actual") }}</th>
          <th class="text-right">{{ $t("stock.reserved") }}</th>
          <th class="text-right">{{ $t("stock.projected") }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="stock.bins.length === 0">
          <td colspan="4" class="text-muted">{{ $t("common.loading") }}</td>
        </tr>
        <tr v-for="bin in stock.bins" :key="bin.warehouse">
          <td>
            <div class="wh-name">{{ bin.warehouse_name }}</div>
            <div class="label-xs">{{ bin.company }}</div>
          </td>
          <td class="text-right mono">{{ formatNumber(bin.actual_qty, prefs.locale, 0) }}</td>
          <td class="text-right mono text-muted">{{ formatNumber(bin.reserved_qty, prefs.locale, 0) }}</td>
          <td class="text-right mono">{{ formatNumber(bin.projected_qty, prefs.locale, 0) }}</td>
        </tr>
        <tr class="total">
          <td>{{ $t("items.stock_totals") }}</td>
          <td class="text-right mono">{{ formatNumber(stock.totals.actual, prefs.locale, 0) }}</td>
          <td class="text-right mono">{{ formatNumber(stock.totals.reserved, prefs.locale, 0) }}</td>
          <td class="text-right mono">{{ formatNumber(stock.totals.projected, prefs.locale, 0) }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.stock-block {
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

.wh-name {
  font-weight: 500;
  margin-bottom: 2px;
}
</style>
