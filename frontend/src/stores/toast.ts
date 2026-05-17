import { defineStore } from "pinia";

type Variant = "success" | "error" | "info";

interface Toast {
  id: number;
  message: string;
  variant: Variant;
}

interface State {
  toasts: Toast[];
}

let _seq = 0;

export const useToastStore = defineStore("toast", {
  state: (): State => ({ toasts: [] }),
  actions: {
    push(message: string, variant: Variant = "info", ttlMs = 3500) {
      const id = ++_seq;
      this.toasts.push({ id, message, variant });
      setTimeout(() => {
        this.toasts = this.toasts.filter((t) => t.id !== id);
      }, ttlMs);
    },
    success(message: string, ttlMs?: number) {
      this.push(message, "success", ttlMs);
    },
    error(message: string, ttlMs = 5500) {
      this.push(message, "error", ttlMs);
    },
    info(message: string, ttlMs?: number) {
      this.push(message, "info", ttlMs);
    },
    dismiss(id: number) {
      this.toasts = this.toasts.filter((t) => t.id !== id);
    },
  },
});
