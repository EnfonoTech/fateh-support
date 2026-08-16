<script setup lang="ts">
import { onMounted, ref } from "vue";
import { myRequests } from "@/api/approvals";
import RequestCard from "@/components/RequestCard.vue";
import SearchBox from "@/components/SearchBox.vue";
import type { ApprovalListRow } from "@/types";

const rows = ref<ApprovalListRow[]>([]);
const loading = ref(false);
const error = ref("");
const query = ref("");

async function load() {
  loading.value = true;
  error.value = "";
  try {
    const result = await myRequests(50, 0, query.value);
    rows.value = result.rows;
  } catch (err) {
    error.value = (err as Error).message;
  } finally {
    loading.value = false;
  }
}

onMounted(load);
</script>

<template>
  <div class="stack">
    <SearchBox v-model="query" :placeholder="$t('approvals.search_placeholder')" @search="load" />

    <div v-if="loading" class="skeleton" style="height:120px" />
    <div v-else-if="error" class="card text-danger">{{ error }}</div>
    <div v-else-if="rows.length === 0" class="card text-muted">
      {{ query ? $t("approvals.empty_search", { q: query }) : $t("my_requests.empty_state") }}
    </div>
    <RequestCard v-for="row in rows" :key="row.name" :row="row" />
  </div>
</template>
