import { defineStore } from "pinia";
import {
  itemPrices,
  itemStock,
  searchItems,
  itemFilters,
  listItems,
  type Company,
  type Warehouse,
  type ItemListRow,
} from "@/api/items";
import type { ItemSummary, PriceResult, StockResult } from "@/types";
import { recentSearches, rememberSearch } from "@/utils/db";

type SortMode = "name" | "qty_desc" | "qty_asc";

interface State {
  // Legacy search state (kept for /items/search)
  query: string;
  results: ItemSummary[];
  recent: string[];

  // Home-page list state
  list: ItemListRow[];
  listTotal: number;
  listLoading: boolean;
  listError: string | null;
  maxQty: number;

  // Filters
  companies: Company[];
  warehouses: Warehouse[];
  selectedCompany: string | null;
  selectedWarehouse: string | null;
  sort: SortMode;
  listSearch: string;
  filtersLoaded: boolean;

  // Detail state
  detailItem: ItemSummary | null;
  stock: StockResult | null;
  prices: PriceResult | null;
  detailLoading: boolean;

  loading: boolean;
  error: string | null;
}

const FILTER_STORE_KEY = "fateh.filters.v1";

function loadPersisted(): Partial<State> {
  try {
    const raw = localStorage.getItem(FILTER_STORE_KEY);
    if (!raw) return {};
    return JSON.parse(raw);
  } catch {
    return {};
  }
}

function persist(state: State) {
  try {
    localStorage.setItem(
      FILTER_STORE_KEY,
      JSON.stringify({
        selectedCompany: state.selectedCompany,
        selectedWarehouse: state.selectedWarehouse,
        sort: state.sort,
      })
    );
  } catch {
    /* ignore */
  }
}

export const useItemsStore = defineStore("items", {
  state: (): State => {
    const persisted = loadPersisted();
    return {
      query: "",
      results: [],
      recent: [],

      list: [],
      listTotal: 0,
      listLoading: false,
      listError: null,
      maxQty: 0,

      companies: [],
      warehouses: [],
      selectedCompany: (persisted.selectedCompany as string | null) ?? null,
      selectedWarehouse: (persisted.selectedWarehouse as string | null) ?? null,
      sort: (persisted.sort as SortMode | undefined) ?? "qty_desc",
      listSearch: "",
      filtersLoaded: false,

      detailItem: null,
      stock: null,
      prices: null,
      detailLoading: false,

      loading: false,
      error: null,
    };
  },
  getters: {
    warehousesForCompany(state): Warehouse[] {
      if (!state.selectedCompany) return state.warehouses;
      return state.warehouses.filter((w) => w.company === state.selectedCompany);
    },
    companyLabel(state): string {
      if (!state.selectedCompany) return "All companies";
      const c = state.companies.find((x) => x.name === state.selectedCompany);
      return c?.name ?? state.selectedCompany;
    },
    warehouseLabel(state): string {
      if (!state.selectedWarehouse) return "All warehouses";
      const w = state.warehouses.find((x) => x.name === state.selectedWarehouse);
      return w?.label ?? state.selectedWarehouse;
    },
  },
  actions: {
    async loadFilters(force = false) {
      if (this.filtersLoaded && !force) return;
      try {
        const result = await itemFilters();
        this.companies = result.companies;
        this.warehouses = result.warehouses;
        this.filtersLoaded = true;
        // If the persisted selection is no longer valid, drop it
        if (
          this.selectedWarehouse &&
          !this.warehouses.some((w) => w.name === this.selectedWarehouse)
        ) {
          this.selectedWarehouse = null;
        }
        if (
          this.selectedCompany &&
          !this.companies.some((c) => c.name === this.selectedCompany)
        ) {
          this.selectedCompany = null;
        }
        // If a single company, auto-select it
        if (!this.selectedCompany && this.companies.length === 1) {
          this.selectedCompany = this.companies[0].name;
        }
      } catch (err) {
        this.error = (err as Error).message;
      }
    },
    setCompany(company: string | null) {
      this.selectedCompany = company;
      // Reset warehouse if it no longer belongs to this company
      if (
        this.selectedWarehouse &&
        !this.warehouses.some(
          (w) => w.name === this.selectedWarehouse && (!company || w.company === company)
        )
      ) {
        this.selectedWarehouse = null;
      }
      persist(this.$state);
      void this.loadList(true);
    },
    setWarehouse(warehouse: string | null) {
      this.selectedWarehouse = warehouse;
      if (warehouse) {
        const wh = this.warehouses.find((w) => w.name === warehouse);
        if (wh && wh.company !== this.selectedCompany) {
          this.selectedCompany = wh.company;
        }
      }
      persist(this.$state);
      void this.loadList(true);
    },
    setSort(sort: SortMode) {
      this.sort = sort;
      persist(this.$state);
      void this.loadList(true);
    },
    setListSearch(q: string) {
      this.listSearch = q;
      void this.loadList(true);
    },
    async loadList(reset = true) {
      this.listLoading = true;
      this.listError = null;
      try {
        const offset = reset ? 0 : this.list.length;
        const response = await listItems({
          warehouse: this.selectedWarehouse ?? undefined,
          company: this.selectedCompany ?? undefined,
          search: this.listSearch || undefined,
          sort: this.sort,
          limit: 50,
          offset,
        });
        this.list = reset ? response.rows : [...this.list, ...response.rows];
        this.listTotal = response.total;
        this.maxQty = Math.max(this.maxQty, response.max_qty);
        if (reset) this.maxQty = response.max_qty;
      } catch (err) {
        this.listError = (err as Error).message;
      } finally {
        this.listLoading = false;
      }
    },

    // Legacy search APIs
    async loadRecent() {
      this.recent = await recentSearches();
    },
    async search(q: string) {
      this.query = q;
      if (!q.trim()) {
        this.results = [];
        return;
      }
      this.loading = true;
      this.error = null;
      try {
        this.results = await searchItems(q);
      } catch (err) {
        this.error = (err as Error).message;
      } finally {
        this.loading = false;
      }
      await rememberSearch(q);
      await this.loadRecent();
    },
    async loadDetail(itemCode: string) {
      this.detailLoading = true;
      this.stock = null;
      this.prices = null;
      try {
        const [stock, prices] = await Promise.all([itemStock(itemCode), itemPrices(itemCode)]);
        this.stock = stock;
        this.prices = prices;
        this.detailItem = stock.item;
      } catch (err) {
        this.error = (err as Error).message;
      } finally {
        this.detailLoading = false;
      }
    },
  },
});
