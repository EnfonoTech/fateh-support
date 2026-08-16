<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";
import { useApprovalsStore } from "@/stores/approvals";
import { useApprovalSocket } from "@/composables/useSocket";
import RequestCard from "@/components/RequestCard.vue";

const approvals = useApprovalsStore();
useApprovalSocket();

const query = ref(approvals.search);
let debounce: ReturnType<typeof setTimeout> | undefined;

// Approvers work from a quotation number the salesperson quotes at them, so
// searching has to be cheap — fire as they type, but only once they stop.
function onInput(): void {
  if (debounce) clearTimeout(debounce);
  debounce = setTimeout(() => approvals.setSearch(query.value.trim()), 300);
}

function clearSearch(): void {
  if (debounce) clearTimeout(debounce);
  query.value = "";
  approvals.setSearch("");
}

onMounted(() => {
  void approvals.load(true);
  void approvals.refreshPending();
});

onBeforeUnmount(() => {
  if (debounce) clearTimeout(debounce);
});

const filters: Array<{ key: "Pending" | "Approved" | "Rejected" | "All" | "Mine"; labelKey: string }> = [
  { key: "Pending", labelKey: "approvals.filter_pending" },
  { key: "Approved", labelKey: "approvals.filter_approved" },
  { key: "Rejected", labelKey: "approvals.filter_rejected" },
  { key: "All", labelKey: "approvals.filter_all" },
  { key: "Mine", labelKey: "approvals.filter_mine" },
];
</script>

<template>
  <div class="stack">
    <div class="search-row">
      <input
        v-model="query"
        type="search"
        inputmode="search"
        autocomplete="off"
        :placeholder="$t('approvals.search_placeholder')"
        :aria-label="$t('approvals.search_placeholder')"
        @input="onInput"
        @keyup.enter="onInput"
      />
      <button v-if="query" class="ghost" type="button" @click="clearSearch">
        {{ $t("common.clear") }}
      </button>
    </div>

    <div class="row wrap">
      <button
        v-for="f in filters"
        :key="f.key"
        :class="approvals.filter === f.key ? 'primary' : 'ghost'"
        @click="approvals.setFilter(f.key)"
      >
        {{ $t(f.labelKey) }}
      </button>
    </div>

    <div v-if="approvals.loading && approvals.rows.length === 0" class="skeleton" style="height:100px" />
    <div v-else-if="approvals.rows.length === 0" class="card text-muted">
      {{ approvals.search ? $t("approvals.empty_search", { q: approvals.search }) : $t("approvals.empty_state") }}
    </div>
    <div v-else class="stack">
      <RequestCard v-for="row in approvals.rows" :key="row.name" :row="row" />
      <button
        v-if="approvals.rows.length < approvals.total"
        class="ghost"
        :disabled="approvals.loading"
        @click="approvals.load(false)"
      >
        {{ $t("common.loading") }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.search-row {
  display: flex;
  gap: 8px;
  align-items: center;
}
.search-row input {
  flex: 1;
  min-width: 0;
}
</style>
