export interface BrandConfig {
  brand_name: string;
  brand_logo?: string | null;
  brand_icon_192?: string | null;
  brand_icon_512?: string | null;
  brand_primary_color: string;
  brand_secondary_color: string;
  login_tagline?: string | null;
  vapid_public_key?: string;
  default_currency?: string;
}

export interface Profile {
  user: string;
  full_name?: string;
  email?: string;
  language?: string;
  roles: string[];
  is_approver: boolean;
  is_viewer: boolean;
  branding: BrandConfig;
  /** Token for the session the server sees right now — rotates on login. */
  csrf_token?: string;
}

export interface ItemSummary {
  item_code: string;
  item_name?: string;
  item_name_ar?: string;
  stock_uom?: string;
  image?: string | null;
  item_group?: string;
}

export interface StockBin {
  warehouse: string;
  warehouse_name: string;
  company: string;
  actual_qty: number;
  reserved_qty: number;
  ordered_qty: number;
  projected_qty: number;
  stock_uom: string;
}

export interface StockResult {
  item_code: string;
  item: ItemSummary;
  bins: StockBin[];
  totals: {
    actual: number;
    reserved: number;
    ordered: number;
    projected: number;
  };
}

export interface PriceRow {
  price_list: string;
  price_list_label: string;
  price_list_rate: number;
  currency: string;
  uom?: string;
  valid_from?: string | null;
  valid_upto?: string | null;
}

export interface PriceResult {
  item_code: string;
  rows: PriceRow[];
  is_approver: boolean;
  valuation_rate?: number;
  last_purchase_rate?: number;
}

export interface ApprovalLine {
  item_code: string;
  item_name: string;
  item_name_ar?: string;
  uom?: string;
  qty: number;
  proposed_rate: number;
  cost_floor_rate: number;
  variance_amount: number;
  variance_pct: number;
  line_total: number;
  valuation_rate?: number;
  last_purchase_rate?: number;
}

export interface ApprovalRequest {
  name: string;
  status: "Pending" | "Approved" | "Rejected";
  requester: string;
  requester_full_name?: string;
  requested_at: string;
  customer?: string;
  customer_name?: string;
  source_doctype: string;
  source_name: string;
  source_url?: string;
  currency?: string;
  total_proposed: number;
  total_cost_floor: number;
  variance_amount: number;
  variance_pct: number;
  line_total_impact: number;
  justification?: string;
  lines: ApprovalLine[];
  approver?: string;
  approver_full_name?: string;
  decided_at?: string;
  decision_note?: string;
  can_decide: boolean;
}

export interface ApprovalListRow {
  name: string;
  status: "Pending" | "Approved" | "Rejected";
  requester: string;
  requester_full_name?: string;
  requested_at: string;
  customer?: string;
  source_doctype: string;
  source_name: string;
  currency?: string;
  variance_amount: number;
  variance_pct: number;
  line_total_impact: number;
  age_seconds?: number;
  line_preview: Array<Pick<ApprovalLine, "item_code" | "item_name" | "qty" | "proposed_rate" | "cost_floor_rate" | "variance_pct">>;
}

export interface FatehGlobal {
  csrf_token?: string;
  vapid_public_key?: string;
  brand?: { name: string; primary: string };
  asset_base?: string;
}

declare global {
  interface Window {
    __FATEH__?: FatehGlobal;
    Capacitor?: { isNativePlatform?: () => boolean };
  }
}
