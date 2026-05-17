<script setup lang="ts">
import { computed, onMounted, watch } from "vue";
import { useRouter } from "vue-router";
import { useItemsStore } from "@/stores/items";
import { usePrefsStore } from "@/stores/prefs";
import StockTable from "@/components/StockTable.vue";
import PriceTable from "@/components/PriceTable.vue";

const props = defineProps<{ code: string }>();
const items = useItemsStore();
const prefs = usePrefsStore();
const router = useRouter();

onMounted(() => items.loadDetail(props.code));
watch(() => props.code, (v) => items.loadDetail(v));

const primaryName = computed(() => {
  if (!items.detailItem) return props.code;
  if (prefs.locale === "ar" && items.detailItem.item_name_ar) return items.detailItem.item_name_ar;
  return items.detailItem.item_name || props.code;
});
</script>

<template>
  <div class="detail-view">
    <button type="button" class="back-btn" @click="router.back()">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="m15 18-6-6 6-6" />
      </svg>
      <span>{{ $t("nav.items") }}</span>
    </button>

    <div v-if="items.detailLoading" class="stack-4 body">
      <div class="skeleton" style="height: 28px; width: 60%" />
      <div class="skeleton" style="height: 160px" />
    </div>

    <template v-else-if="items.stock && items.prices">
      <header class="detail-header">
        <h1>{{ primaryName }}</h1>
        <div class="meta">
          <span class="code">{{ items.detailItem?.item_code || code }}</span>
          <span v-if="items.detailItem?.stock_uom" class="dot">·</span>
          <span v-if="items.detailItem?.stock_uom">{{ items.detailItem.stock_uom }}</span>
          <span v-if="items.detailItem?.item_group" class="dot">·</span>
          <span v-if="items.detailItem?.item_group">{{ items.detailItem.item_group }}</span>
        </div>
      </header>

      <section class="block">
        <StockTable :stock="items.stock" />
      </section>

      <section class="block">
        <PriceTable :prices="items.prices" />
      </section>
    </template>

    <div v-else-if="items.error" class="body">
      <div class="card text-danger">{{ items.error }}</div>
    </div>
  </div>
</template>

<style scoped>
.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin: 12px 16px 0;
  padding: 6px 12px;
  border: 1px solid var(--rule);
  background: var(--paper);
  min-height: 32px;
  font-size: 13px;
  color: var(--ink-2);
  border-radius: var(--radius);
}

.back-btn:hover {
  background: var(--paper-3);
}

.detail-header {
  padding: 14px 16px 16px;
  border-bottom: 1px solid var(--rule);
}

.detail-header h1 {
  font-size: 20px;
  font-weight: 600;
  margin: 0 0 4px;
  letter-spacing: var(--tracking-tight);
}

.meta {
  display: flex;
  gap: 6px;
  font-size: 13px;
  color: var(--ink-3);
}

.dot { color: var(--ink-4); }

.block {
  padding: 16px;
}

.body {
  padding: 16px;
}
</style>
