<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useApprovalsStore } from "@/stores/approvals";
import { useApprovalSocket } from "@/composables/useSocket";
import VarianceBanner from "@/components/VarianceBanner.vue";
import DecisionSheet from "@/components/DecisionSheet.vue";
import { formatDateTime } from "@/utils/format";
import { usePrefsStore } from "@/stores/prefs";
import { useToastStore } from "@/stores/toast";
import { useI18n } from "vue-i18n";
import Money from "@/components/Money.vue";

const props = defineProps<{ name: string }>();
const approvals = useApprovalsStore();
const prefs = usePrefsStore();
const toast = useToastStore();
const { t } = useI18n();

useApprovalSocket();

onMounted(() => approvals.loadDetail(props.name));
watch(() => props.name, (v) => approvals.loadDetail(v));

const sheetOpen = ref(false);
const sheetAction = ref<"approve" | "reject">("approve");
const submitting = ref(false);

const detail = computed(() => approvals.detail);

function open(action: "approve" | "reject") {
  sheetAction.value = action;
  sheetOpen.value = true;
}

async function confirm(note: string) {
  submitting.value = true;
  try {
    await approvals.decide(sheetAction.value, note);
    sheetOpen.value = false;
    const key = sheetAction.value === "approve" ? "approvals.toast_approved" : "approvals.toast_rejected";
    toast.success(t(key));
  } catch (err) {
    const msg = (err as Error)?.message || "Request failed";
    toast.error(msg);
  } finally {
    submitting.value = false;
  }
}
</script>

<template>
  <div class="stack" v-if="detail">
    <div class="card stack">
      <div class="row between">
        <div>
          <strong>{{ detail.customer_name || detail.customer || detail.source_name }}</strong>
          <div class="text-muted">{{ detail.source_doctype }} {{ detail.source_name }}</div>
        </div>
        <span class="badge" :class="detail.status.toLowerCase()">{{ detail.status }}</span>
      </div>
      <VarianceBanner
        :variance-pct="detail.variance_pct"
        :variance-amount="detail.variance_amount"
        :currency="detail.currency"
      />
      <div class="row between">
        <div>
          <div class="text-muted" style="font-size:12px">{{ $t("approvals.requester") }}</div>
          <div>{{ detail.requester_full_name }}</div>
        </div>
        <div class="text-right">
          <div class="text-muted" style="font-size:12px">{{ $t("approvals.decided_at") }}</div>
          <div>{{ detail.decided_at ? formatDateTime(detail.decided_at, prefs.locale) : "-" }}</div>
        </div>
      </div>
      <a v-if="detail.source_url" :href="detail.source_url" target="_blank" rel="noopener">
        {{ $t("approvals.open_source") }} ↗
      </a>
    </div>

    <div class="card" v-if="detail.justification">
      <strong>{{ $t("approvals.justification") }}</strong>
      <p>{{ detail.justification }}</p>
    </div>
    <div class="card text-muted" v-else>{{ $t("approvals.no_justification") }}</div>

    <div class="card stack">
      <strong>{{ $t("approvals.lines") }}</strong>
      <table class="data">
        <thead>
          <tr>
            <th>{{ $t("approvals.item") }}</th>
            <th class="text-right">{{ $t("approvals.qty") }}</th>
            <th class="text-right">{{ $t("approvals.proposed_rate") }}</th>
            <th class="text-right">{{ $t("approvals.cost_floor_rate") }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="line in detail.lines" :key="line.item_code">
            <td>
              <div>{{ line.item_name || line.item_code }}</div>
              <small class="text-muted">{{ line.item_code }}</small>
            </td>
            <td class="text-right">{{ line.qty }}</td>
            <td class="text-right"><Money :value="line.proposed_rate" :currency="detail.currency" /></td>
            <td class="text-right"><Money :value="line.cost_floor_rate" :currency="detail.currency" /></td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="card row" style="justify-content: flex-end; position: sticky; bottom: 64px; background: var(--surface-0)">
      <template v-if="detail.can_decide">
        <button class="danger" @click="open('reject')">{{ $t("approvals.reject") }}</button>
        <button class="primary" @click="open('approve')">{{ $t("approvals.approve") }}</button>
      </template>
      <template v-else>
        <span class="text-muted">{{ detail.decision_note || "" }}</span>
      </template>
    </div>

    <DecisionSheet
      :open="sheetOpen"
      :action="sheetAction"
      :submitting="submitting"
      @cancel="sheetOpen = false"
      @confirm="confirm"
    />
  </div>
  <div v-else class="skeleton" style="height: 320px" />
</template>
