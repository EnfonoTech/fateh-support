<script setup lang="ts">
import { ref, watch } from "vue";
import { useI18n } from "vue-i18n";

const props = defineProps<{
  open: boolean;
  action: "approve" | "reject";
  submitting?: boolean;
}>();
const emit = defineEmits<{
  (e: "confirm", note: string): void;
  (e: "cancel"): void;
}>();

const note = ref("");
const error = ref("");
const { t } = useI18n();

watch(
  () => props.open,
  (v) => {
    if (!v) {
      note.value = "";
      error.value = "";
    }
  }
);

function onConfirm() {
  if (props.action === "reject" && !note.value.trim()) {
    error.value = t("approvals.note_required_reject");
    return;
  }
  emit("confirm", note.value.trim());
}
</script>

<template>
  <teleport to="body">
    <div v-if="open" class="sheet-scrim" @click.self="emit('cancel')">
      <div class="sheet stack" role="dialog" aria-modal="true">
        <h3>{{ action === "approve" ? $t("approvals.confirm_approve") : $t("approvals.confirm_reject") }}</h3>
        <label>
          <span>{{ $t("approvals.decision_note") }}</span>
          <textarea
            v-model="note"
            rows="3"
            :placeholder="action === 'reject' ? $t('approvals.note_required_reject') : $t('approvals.note_optional')"
          />
          <small class="text-danger" v-if="error">{{ error }}</small>
        </label>
        <div class="row" style="justify-content: flex-end">
          <button class="ghost" @click="emit('cancel')" :disabled="submitting">{{ $t("common.cancel") }}</button>
          <button
            :class="action === 'approve' ? 'primary' : 'danger'"
            :disabled="submitting"
            @click="onConfirm"
          >
            {{ action === "approve" ? $t("approvals.approve") : $t("approvals.reject") }}
          </button>
        </div>
      </div>
    </div>
  </teleport>
</template>
