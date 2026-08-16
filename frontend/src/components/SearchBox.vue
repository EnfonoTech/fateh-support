<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from "vue";

const props = withDefaults(
  defineProps<{
    modelValue: string;
    placeholder: string;
    /** Milliseconds of quiet before the search fires. */
    delay?: number;
  }>(),
  { delay: 300 }
);

const emit = defineEmits<{
  (e: "update:modelValue", value: string): void;
  (e: "search", value: string): void;
}>();

const query = ref(props.modelValue);
let timer: ReturnType<typeof setTimeout> | undefined;

// Keep in step if the parent resets the term (filter change, route change).
watch(
  () => props.modelValue,
  (value) => {
    if (value !== query.value.trim()) query.value = value;
  }
);

function fire(): void {
  if (timer) clearTimeout(timer);
  const value = query.value.trim();
  emit("update:modelValue", value);
  emit("search", value);
}

function onInput(): void {
  if (timer) clearTimeout(timer);
  timer = setTimeout(fire, props.delay);
}

function clear(): void {
  query.value = "";
  fire();
}

onBeforeUnmount(() => {
  if (timer) clearTimeout(timer);
});
</script>

<template>
  <div class="search-box">
    <input
      v-model="query"
      type="search"
      inputmode="search"
      autocomplete="off"
      autocapitalize="characters"
      spellcheck="false"
      :placeholder="placeholder"
      :aria-label="placeholder"
      @input="onInput"
      @keyup.enter="fire"
    />
    <button v-if="query" class="ghost" type="button" @click="clear">
      {{ $t("common.clear") }}
    </button>
  </div>
</template>

<style scoped>
.search-box {
  display: flex;
  gap: 8px;
  align-items: center;
}
.search-box input {
  flex: 1;
  min-width: 0;
}
</style>
