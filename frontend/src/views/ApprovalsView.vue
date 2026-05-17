<script setup lang="ts">
import { onMounted } from "vue";
import { useApprovalsStore } from "@/stores/approvals";
import { useApprovalSocket } from "@/composables/useSocket";
import RequestCard from "@/components/RequestCard.vue";

const approvals = useApprovalsStore();
useApprovalSocket();

onMounted(() => {
  void approvals.load(true);
  void approvals.refreshPending();
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
      {{ $t("approvals.empty_state") }}
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
