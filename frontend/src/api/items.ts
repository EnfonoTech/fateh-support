import { call } from "./client";
import type { ItemSummary, PriceResult, StockResult } from "@/types";

export interface Warehouse {
  name: string;
  label: string;
  company: string;
  parent?: string | null;
}

export interface Company {
  name: string;
  abbr?: string;
  country?: string;
  default_currency?: string;
}

export interface ItemsFiltersResponse {
  companies: Company[];
  warehouses: Warehouse[];
}

export interface ItemListRow {
  item_code: string;
  item_name: string;
  item_name_ar?: string | null;
  stock_uom?: string | null;
  item_group?: string | null;
  image?: string | null;
  actual_qty: number;
  reserved_qty: number;
  projected_qty: number;
  ordered_qty: number;
}

export interface ItemsListResponse {
  rows: ItemListRow[];
  total: number;
  offset: number;
  limit: number;
  max_qty: number;
  scope: {
    warehouse: string | null;
    company: string | null;
    warehouse_count: number;
  };
}

export function searchItems(q: string, limit = 20): Promise<ItemSummary[]> {
  return call<ItemSummary[]>("fateh_support.api.items.search", {
    method: "GET",
    params: { q, limit },
  });
}

export function itemStock(itemCode: string): Promise<StockResult> {
  return call<StockResult>("fateh_support.api.items.stock", {
    method: "GET",
    params: { item_code: itemCode },
  });
}

export function itemPrices(itemCode: string): Promise<PriceResult> {
  return call<PriceResult>("fateh_support.api.items.prices", {
    method: "GET",
    params: { item_code: itemCode },
  });
}

export function itemFilters(): Promise<ItemsFiltersResponse> {
  return call<ItemsFiltersResponse>("fateh_support.api.items.filters", { method: "GET" });
}

export function listItems(params: {
  warehouse?: string;
  company?: string;
  search?: string;
  item_group?: string;
  sort?: "name" | "qty_desc" | "qty_asc";
  limit?: number;
  offset?: number;
}): Promise<ItemsListResponse> {
  return call<ItemsListResponse>("fateh_support.api.items.list_items", {
    method: "GET",
    params,
  });
}
