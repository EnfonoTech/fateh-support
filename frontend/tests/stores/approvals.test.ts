import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";

const listMock = vi.fn();
const getMock = vi.fn();
const decideMock = vi.fn();
const pendingMock = vi.fn();
const justificationMock = vi.fn();

vi.mock("@/api/approvals", () => ({
  listApprovals: (...args: unknown[]) => listMock(...args),
  getApproval: (...args: unknown[]) => getMock(...args),
  decideApproval: (...args: unknown[]) => decideMock(...args),
  pendingCount: (...args: unknown[]) => pendingMock(...args),
  setJustification: (...args: unknown[]) => justificationMock(...args),
  myRequests: vi.fn(),
}));

import { useApprovalsStore } from "@/stores/approvals";

describe("approvals store", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    listMock.mockReset();
    getMock.mockReset();
    decideMock.mockReset();
    pendingMock.mockReset();
    justificationMock.mockReset();
  });

  it("loads the first page", async () => {
    listMock.mockResolvedValueOnce({
      rows: [{ name: "SPAR-001", status: "Pending" }],
      total: 1,
      offset: 0,
      limit: 20,
    });
    const store = useApprovalsStore();
    await store.load(true);
    expect(store.rows).toHaveLength(1);
    expect(store.total).toBe(1);
  });

  it("applyRealtime mutates an existing row status", async () => {
    listMock.mockResolvedValueOnce({
      rows: [{ name: "SPAR-001", status: "Pending" }],
      total: 1,
      offset: 0,
      limit: 20,
    });
    pendingMock.mockResolvedValue({ count: 0 });
    const store = useApprovalsStore();
    await store.load(true);
    store.applyRealtime({ name: "SPAR-001", status: "Approved" });
    expect(store.rows[0].status).toBe("Approved");
  });

  it("decide refreshes detail and list", async () => {
    getMock.mockResolvedValue({
      name: "SPAR-001",
      status: "Approved",
      lines: [],
      can_decide: false,
    });
    decideMock.mockResolvedValue({ name: "SPAR-001", status: "Approved" });
    listMock.mockResolvedValue({ rows: [], total: 0, offset: 0, limit: 20 });
    pendingMock.mockResolvedValue({ count: 0 });

    const store = useApprovalsStore();
    store.detail = { name: "SPAR-001" } as any;
    await store.decide("approve", "ok");

    expect(decideMock).toHaveBeenCalledWith("SPAR-001", "approve", "ok");
    expect(getMock).toHaveBeenCalled();
    expect(listMock).toHaveBeenCalled();
  });
});
