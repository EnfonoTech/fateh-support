<script setup lang="ts">
import { useToastStore } from "@/stores/toast";

const toast = useToastStore();
</script>

<template>
  <teleport to="body">
    <div class="toast-layer" aria-live="polite">
      <transition-group name="toast">
        <div
          v-for="t in toast.toasts"
          :key="t.id"
          class="toast"
          :class="t.variant"
          role="status"
          @click="toast.dismiss(t.id)"
        >
          <span class="dot" />
          <span class="msg">{{ t.message }}</span>
        </div>
      </transition-group>
    </div>
  </teleport>
</template>

<style scoped>
.toast-layer {
  position: fixed;
  top: calc(var(--header-h) + 12px);
  left: 50%;
  transform: translateX(-50%);
  z-index: 80;
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: min(92vw, 420px);
  pointer-events: none;
}

.toast {
  pointer-events: auto;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  background: var(--paper);
  border: 1px solid var(--rule);
  border-radius: var(--radius);
  box-shadow: var(--shadow-lg);
  font-size: 14px;
  cursor: pointer;
}

.toast .dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  flex-shrink: 0;
}

.toast.success .dot { background: var(--success); }
.toast.error .dot { background: var(--danger); }
.toast.info .dot { background: var(--brand-primary); }

.toast.error {
  border-color: #FECACA;
  background: #FEF2F2;
  color: #991B1B;
}

.toast.success {
  border-color: #A7F3D0;
  background: #ECFDF5;
  color: #065F46;
}

.msg {
  flex: 1;
  line-height: 1.35;
}

.toast-enter-from, .toast-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
.toast-enter-active, .toast-leave-active {
  transition: opacity 180ms var(--ease), transform 180ms var(--ease);
}
</style>
