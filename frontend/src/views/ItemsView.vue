<script setup lang="ts">
import { computed, onMounted } from "vue";
import { useItemsStore } from "@/stores/items";
import FilterBar from "@/components/FilterBar.vue";
import ItemRow from "@/components/ItemRow.vue";

const items = useItemsStore();

onMounted(async () => {
  await items.loadFilters();
  await items.loadList(true);
});

const canLoadMore = computed(() => items.list.length < items.listTotal && !items.listLoading);

function loadMore() {
  void items.loadList(false);
}
</script>

<template>
  <div class="items-view">
    <FilterBar />

    <div class="sort-row">
      <span class="count label-xs">
        {{ items.listTotal }} {{ $t("items.items_label") }}
      </span>
      <div class="sort-buttons">
        <button
          v-for="s in [
            { key: 'qty_desc', label: $t('filters.sort_qty_desc') },
            { key: 'name', label: $t('filters.sort_name') },
            { key: 'qty_asc', label: $t('filters.sort_qty_asc') },
          ]"
          :key="s.key"
          type="button"
          class="sort-btn"
          :class="{ active: items.sort === s.key }"
          @click="items.setSort(s.key as any)"
        >
          {{ s.label }}
        </button>
      </div>
    </div>

    <section class="list">
      <div v-if="items.listLoading && items.list.length === 0" class="list-skeleton">
        <div v-for="i in 6" :key="i" class="skeleton-row" />
      </div>

      <div v-else-if="items.listError" class="empty text-danger">{{ items.listError }}</div>

      <div v-else-if="items.list.length === 0" class="empty">
        <h3>{{ $t("items.empty_title") }}</h3>
        <p class="text-muted">{{ $t("items.empty_body") }}</p>
      </div>

      <template v-else>
        <ItemRow
          v-for="(row, idx) in items.list"
          :key="row.item_code"
          :row="row"
          :max="items.maxQty"
          :index="idx"
        />
        <div class="load-more-wrap" v-if="canLoadMore || items.listLoading">
          <button type="button" class="ghost" :disabled="items.listLoading" @click="loadMore">
            <span v-if="items.listLoading">{{ $t("common.loading") }}</span>
            <span v-else>{{ $t("items.load_more") }}</span>
          </button>
        </div>
      </template>
    </section>
  </div>
</template>

<style scoped>
.sort-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--rule);
}

.count { color: var(--ink-3); }

.sort-buttons {
  display: flex;
  gap: 4px;
  background: var(--paper-2);
  border-radius: var(--radius);
  padding: 3px;
}

.sort-btn {
  min-height: 28px;
  padding: 4px 10px;
  font-size: 12px;
  font-weight: 500;
  border: 0;
  background: transparent;
  color: var(--ink-3);
  border-radius: calc(var(--radius) - 3px);
}

.sort-btn.active {
  background: var(--paper);
  color: var(--ink);
  box-shadow: var(--shadow-sm);
}

.list-skeleton {
  padding: 4px 0;
}

.skeleton-row {
  height: 64px;
  margin: 2px 16px;
  border-radius: var(--radius);
}

.empty {
  text-align: center;
  padding: var(--space-8) var(--space-5);
}

.empty h3 {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 4px;
}

.empty p {
  margin: 0;
  font-size: 14px;
}

.load-more-wrap {
  display: flex;
  justify-content: center;
  padding: var(--space-5);
}
</style>
