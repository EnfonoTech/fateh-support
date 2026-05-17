import { ref } from "vue";

const online = ref(typeof navigator !== "undefined" ? navigator.onLine : true);
let attached = false;

function attach() {
  if (attached || typeof window === "undefined") return;
  attached = true;
  window.addEventListener("online", () => (online.value = true));
  window.addEventListener("offline", () => (online.value = false));
}

export function useOnline() {
  attach();
  return online;
}
