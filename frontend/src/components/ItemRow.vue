<script setup lang="ts">
import { computed } from "vue";
import type { ItemListRow } from "@/api/items";
import StockMiniBar from "@/components/StockMiniBar.vue";
import { usePrefsStore } from "@/stores/prefs";
import { formatNumber } from "@/utils/format";

const props = defineProps<{
  row: ItemListRow;
  max: number;
  index: number;
}>();

const prefs = usePrefsStore();

const primaryName = computed(() => {
  if (prefs.locale === "ar" && props.row.item_name_ar) return props.row.item_name_ar;
  return props.row.item_name || props.row.item_code;
});

const qtyTierClass = computed(() => {
  if (!props.max || props.max <= 0) return "qty-empty";
  const p = props.row.actual_qty / props.max;
  if (p <= 0) return "qty-empty";
  if (p < 0.2) return "qty-low";
  return "";
});
</script>

<template>
  <router-link :to="`/items/${encodeURIComponent(row.item_code)}`" class="item-row list-row">
    <div class="body">
      <div class="name">{{ primaryName }}</div>
      <div class="meta">
        <span class="code">{{ row.item_code }}</span>
        <span v-if="row.stock_uom" class="dot">·</span>
        <span v-if="row.stock_uom" class="uom">{{ row.stock_uom }}</span>
      </div>
      <StockMiniBar :value="row.actual_qty" :max="max" :reserved="row.reserved_qty" />
    </div>
    <div class="qty" :class="qtyTierClass">
      <div class="mono num">{{ formatNumber(row.actual_qty, prefs.locale, 0) }}</div>
      <div v-if="row.reserved_qty > 0" class="reserved mono">
        &minus;{{ formatNumber(row.reserved_qty, prefs.locale, 0) }}
      </div>
    </div>
  </router-link>
</template>

<style scoped>
.item-row {
  padding: 14px 16px;
}

.body {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.name {
  font-size: 15px;
  font-weight: 500;
  color: var(--ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.meta {
  display: flex;
  gap: 6px;
  font-size: 12px;
  color: var(--ink-3);
}

.dot { color: var(--ink-4); }

.qty {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  justify-content: center;
  gap: 2px;
  min-width: 64px;
}

.qty .num {
  font-size: 18px;
  font-weight: 600;
  color: var(--ink);
  line-height: 1;
}

.qty .reserved {
  font-size: 11px;
  color: var(--warning);
}

.qty.qty-empty .num { color: var(--ink-4); }
.qty.qty-low .num { color: var(--warning); }
</style>
