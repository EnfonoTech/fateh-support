import { call } from "./client";
import type { ApprovalListRow, ApprovalRequest } from "@/types";

export interface ApprovalListResponse {
  rows: ApprovalListRow[];
  total: number;
  offset: number;
  limit: number;
}

export function listApprovals(params: {
  status?: string;
  mine?: 0 | 1;
  limit?: number;
  offset?: number;
  search?: string;
}): Promise<ApprovalListResponse> {
  return call<ApprovalListResponse>("fateh_support.api.approvals.list", {
    method: "GET",
    params,
  });
}

export function getApproval(name: string): Promise<ApprovalRequest> {
  return call<ApprovalRequest>("fateh_support.api.approvals.get", {
    method: "GET",
    params: { name },
  });
}

export function decideApproval(
  name: string,
  action: "approve" | "reject",
  note: string
): Promise<{ name: string; status: string }> {
  return call("fateh_support.api.approvals.decide", {
    body: { name, action, note },
  });
}

export function setJustification(name: string, justification: string): Promise<{ ok: true }> {
  return call("fateh_support.api.approvals.set_justification", {
    body: { name, justification },
  });
}

export function myRequests(limit = 20, offset = 0, search = ""): Promise<ApprovalListResponse> {
  return call("fateh_support.api.approvals.mine", {
    method: "GET",
    params: { limit, offset, search },
  });
}

export function pendingCount(): Promise<{ count: number }> {
  return call("fateh_support.api.approvals.pending_count", { method: "GET" });
}
