import { defineStore } from "pinia";
import {
  decideApproval,
  getApproval,
  listApprovals,
  pendingCount,
  setJustification,
} from "@/api/approvals";
import type { ApprovalListRow, ApprovalRequest } from "@/types";

type Filter = "Pending" | "Approved" | "Rejected" | "All" | "Mine";

interface State {
  rows: ApprovalListRow[];
  total: number;
  filter: Filter;
  search: string;
  loading: boolean;
  error: string | null;
  pending: number;
  detail: ApprovalRequest | null;
  detailLoading: boolean;
}

export const useApprovalsStore = defineStore("approvals", {
  state: (): State => ({
    rows: [],
    total: 0,
    filter: "Pending",
    search: "",
    loading: false,
    error: null,
    pending: 0,
    detail: null,
    detailLoading: false,
  }),
  actions: {
    async load(reset = true) {
      this.loading = true;
      this.error = null;
      try {
        const offset = reset ? 0 : this.rows.length;
        const params: Parameters<typeof listApprovals>[0] = {
          status: this.filter === "All" || this.filter === "Mine" ? "" : this.filter,
          mine: this.filter === "Mine" ? 1 : 0,
          limit: 20,
          offset,
          search: this.search,
        };
        const result = await listApprovals(params);
        this.rows = reset ? result.rows : [...this.rows, ...result.rows];
        this.total = result.total;
      } catch (err) {
        this.error = (err as Error).message;
      } finally {
        this.loading = false;
      }
    },
    setFilter(filter: Filter) {
      this.filter = filter;
      void this.load(true);
    },
    setSearch(q: string) {
      this.search = q;
      void this.load(true);
    },
    async refreshPending() {
      try {
        const res = await pendingCount();
        this.pending = res.count;
      } catch {
        /* ignore */
      }
    },
    async loadDetail(name: string) {
      this.detailLoading = true;
      try {
        this.detail = await getApproval(name);
      } catch (err) {
        this.error = (err as Error).message;
      } finally {
        this.detailLoading = false;
      }
    },
    async decide(action: "approve" | "reject", note: string) {
      if (!this.detail) throw new Error("No request loaded");
      const name = this.detail.name;
      const expected = action === "approve" ? "Approved" : "Rejected";
      let apiError: Error | null = null;
      try {
        await decideApproval(name, action, note);
      } catch (err) {
        apiError = err as Error;
      }
      // Always refresh so the UI matches reality — the POST may have
      // succeeded on the server even when the fetch raised (flaky mobile
      // network, service-worker race, CORS preflight glitch, etc).
      await this.loadDetail(name);
      await this.load(true);
      await this.refreshPending();

      const finalStatus = this.detail?.status;
      if (finalStatus === expected) return; // success (despite any fetch hiccup)
      if (apiError) throw apiError;
      if (finalStatus && finalStatus !== "Pending") {
        throw new Error(`Request is already ${finalStatus}.`);
      }
      throw new Error("Decision could not be recorded. Please try again.");
    },
    async attachJustification(name: string, justification: string) {
      await setJustification(name, justification);
      if (this.detail?.name === name) await this.loadDetail(name);
    },
    applyRealtime(payload: { name: string; status: string }) {
      const idx = this.rows.findIndex((r) => r.name === payload.name);
      if (idx >= 0) {
        this.rows[idx] = { ...this.rows[idx], status: payload.status as ApprovalListRow["status"] };
      } else if (payload.status === "Pending") {
        void this.load(true);
      }
      if (this.detail?.name === payload.name) {
        void this.loadDetail(payload.name);
      }
      void this.refreshPending();
    },
  },
});
