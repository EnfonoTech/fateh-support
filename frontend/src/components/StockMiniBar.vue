<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  value: number;
  max: number;
  reserved?: number;
}>();

const pct = computed(() => {
  if (!props.max || props.max <= 0) return 0;
  return Math.min(100, Math.max(0, (props.value / props.max) * 100));
});

const reservedPct = computed(() => {
  if (!props.reserved || !props.max || props.max <= 0) return 0;
  return Math.min(100, Math.max(0, (props.reserved / props.max) * 100));
});

const tier = computed<"empty" | "low" | "ok" | "high">(() => {
  const p = pct.value;
  if (p <= 0) return "empty";
  if (p < 20) return "low";
  if (p < 60) return "ok";
  return "high";
});
</script>

<template>
  <div class="mini-bar" :class="`tier-${tier}`" :aria-label="`Stock level ${pct.toFixed(0)}%`">
    <div class="track">
      <div class="fill" :style="{ width: pct + '%' }" />
      <div
        v-if="reserved && reserved > 0"
        class="reserved-mark"
        :style="{ insetInlineStart: (pct - reservedPct) + '%', width: reservedPct + '%' }"
      />
    </div>
  </div>
</template>

<style scoped>
.mini-bar {
  width: 100%;
}

.track {
  position: relative;
  height: 4px;
  background: var(--rule);
  border-radius: var(--radius-pill);
  overflow: hidden;
}

.fill {
  position: absolute;
  top: 0;
  bottom: 0;
  inset-inline-start: 0;
  background: var(--stock-high);
  border-radius: var(--radius-pill);
  transition: width var(--dur-slow) var(--ease-out);
}

.tier-empty .fill { background: var(--stock-empty); }
.tier-low .fill   { background: var(--stock-low); }
.tier-ok .fill    { background: var(--stock-ok); }
.tier-high .fill  { background: var(--stock-high); }

.reserved-mark {
  position: absolute;
  top: 0;
  bottom: 0;
  background: repeating-linear-gradient(
    45deg,
    rgba(14, 14, 16, 0.45) 0 2px,
    transparent 2px 4px
  );
  mix-blend-mode: multiply;
}
</style>
