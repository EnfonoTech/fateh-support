<script setup lang="ts">
import { computed, ref } from "vue";
import { useItemsStore } from "@/stores/items";

const items = useItemsStore();
const searchOpen = ref(false);
const searchRef = ref<HTMLInputElement | null>(null);

function toggleSearch() {
  searchOpen.value = !searchOpen.value;
  if (searchOpen.value) {
    requestAnimationFrame(() => searchRef.value?.focus());
  } else {
    items.setListSearch("");
  }
}

const warehouseOptions = computed(() => items.warehousesForCompany);

function onCompanyChange(e: Event) {
  const v = (e.target as HTMLSelectElement).value || null;
  items.setCompany(v);
}

function pickWarehouse(name: string | null) {
  items.setWarehouse(name);
}

function onSearchInput(e: Event) {
  const v = (e.target as HTMLInputElement).value;
  items.setListSearch(v);
}
</script>

<template>
  <div class="filter-bar">
    <div class="line-a">
      <select
        :value="items.selectedCompany ?? ''"
        @change="onCompanyChange"
        class="company-select"
      >
        <option value="">{{ $t("filters.all_companies") }}</option>
        <option v-for="c in items.companies" :key="c.name" :value="c.name">
          {{ c.name }}
        </option>
      </select>
      <button class="icon-btn" type="button" @click="toggleSearch" :aria-pressed="searchOpen">
        <svg v-if="!searchOpen" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
        <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>
      </button>
    </div>

    <div v-if="searchOpen" class="search-line">
      <input
        ref="searchRef"
        :value="items.listSearch"
        @input="onSearchInput"
        class="search-input"
        :placeholder="$t('items.search_placeholder')"
      />
    </div>

    <div class="warehouse-scroll">
      <button
        type="button"
        class="pill"
        :class="{ active: items.selectedWarehouse === null }"
        @click="pickWarehouse(null)"
      >
        {{ $t("filters.all_warehouses") }}
      </button>
      <button
        v-for="w in warehouseOptions"
        :key="w.name"
        type="button"
        class="pill"
        :class="{ active: items.selectedWarehouse === w.name }"
        @click="pickWarehouse(w.name)"
      >
        {{ w.label }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.filter-bar {
  position: sticky;
  top: var(--header-h);
  z-index: 15;
  background: var(--paper);
  border-bottom: 1px solid var(--rule);
  padding: 10px 16px;
}

.line-a {
  display: flex;
  gap: 8px;
  align-items: center;
}

.company-select {
  font-size: 14px;
  font-weight: 500;
  min-height: 38px;
  flex: 1;
}

.icon-btn {
  min-height: 38px;
  min-width: 38px;
  padding: 0;
  border: 1px solid var(--rule);
  border-radius: var(--radius);
  background: var(--paper);
  color: var(--ink-2);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.icon-btn:hover {
  background: var(--paper-3);
}

.icon-btn[aria-pressed="true"] {
  background: var(--ink);
  color: var(--paper);
  border-color: var(--ink);
}

.search-line {
  padding-top: 8px;
}

.warehouse-scroll {
  display: flex;
  gap: 6px;
  padding-top: 10px;
  overflow-x: auto;
  scrollbar-width: none;
  -webkit-overflow-scrolling: touch;
}

.warehouse-scroll::-webkit-scrollbar { display: none; }

.warehouse-scroll .pill {
  flex-shrink: 0;
  border-color: var(--rule);
  background: var(--paper);
}

.warehouse-scroll .pill.active {
  background: var(--brand-primary);
  color: var(--brand-primary-contrast);
  border-color: var(--brand-primary);
}
</style>
