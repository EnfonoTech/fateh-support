<script setup lang="ts">
import type { ApprovalListRow } from "@/types";
import { formatAge } from "@/utils/format";
import { usePrefsStore } from "@/stores/prefs";
import Money from "@/components/Money.vue";

const prefs = usePrefsStore();
defineProps<{ row: ApprovalListRow }>();

function statusClass(status: string) {
  if (status === "Pending") return "pending";
  if (status === "Approved") return "approved";
  return "rejected";
}
</script>

<template>
  <router-link :to="`/approvals/${row.name}`" class="card" style="display:block; text-decoration:none; color:inherit">
    <div class="row between">
      <div>
        <div><strong>{{ row.customer || row.source_name }}</strong></div>
        <small class="text-muted">{{ row.requester_full_name }} • {{ row.source_doctype }} {{ row.source_name }}</small>
      </div>
      <span class="badge" :class="statusClass(row.status)">{{ row.status }}</span>
    </div>
    <div class="row between" style="margin-top: var(--space-3)">
      <div>
        <div class="text-muted" style="font-size: 12px">{{ $t("approvals.variance") }}</div>
        <div class="row tight">
          <strong :class="{ 'text-danger': (row.variance_pct || 0) < 0 }">
            {{ (row.variance_pct || 0).toFixed(1) }}%
          </strong>
          <Money class="text-muted var-amt" :value="row.variance_amount || 0" :currency="row.currency" />
        </div>
      </div>
      <div class="text-right">
        <div class="text-muted" style="font-size: 12px">{{ $t("approvals.age") }}</div>
        <div>{{ formatAge(row.age_seconds, prefs.locale) }}</div>
      </div>
    </div>
  </router-link>
</template>

<style scoped>
.var-amt :deep(.amount) {
  font-size: 13px;
}
.var-amt :deep(.code) {
  font-size: 10px;
}
</style>
