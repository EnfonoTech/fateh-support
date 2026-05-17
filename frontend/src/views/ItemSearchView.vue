<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import { useItemsStore } from "@/stores/items";
import { useRouter } from "vue-router";

const items = useItemsStore();
const router = useRouter();
const q = ref("");
let timer: ReturnType<typeof setTimeout> | null = null;

watch(q, (val) => {
  if (timer) clearTimeout(timer);
  timer = setTimeout(() => {
    void items.search(val);
  }, 300);
});

onMounted(() => items.loadRecent());

function choose(code: string) {
  router.push(`/items/${encodeURIComponent(code)}`);
}

function useRecent(val: string) {
  q.value = val;
}
</script>

<template>
  <div class="stack">
    <input v-model="q" type="search" :placeholder="$t('items.search_placeholder')" autofocus />
    <div v-if="items.loading" class="skeleton" style="height: 72px" />
    <div v-if="items.error" class="card text-danger">{{ items.error }}</div>

    <div v-if="q.length === 0 && items.recent.length" class="card stack">
      <strong>{{ $t("items.recent") }}</strong>
      <div class="row wrap">
        <button
          v-for="r in items.recent"
          :key="r"
          class="ghost"
          type="button"
          @click="useRecent(r)"
        >
          {{ r }}
        </button>
      </div>
    </div>

    <div class="stack" v-if="items.results.length">
      <button
        v-for="i in items.results"
        :key="i.item_code"
        class="card"
        style="text-align:start"
        @click="choose(i.item_code)"
      >
        <div><strong>{{ i.item_name || i.item_code }}</strong></div>
        <small class="text-muted">{{ i.item_code }} • {{ i.stock_uom || "" }}</small>
        <div v-if="i.item_name_ar" dir="rtl" class="text-muted">{{ i.item_name_ar }}</div>
      </button>
    </div>

    <div v-else-if="q.length > 0 && !items.loading" class="card text-muted">
      {{ $t("items.no_results") }}
    </div>
  </div>
</template>
