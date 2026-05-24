"""Item search, stock, and price endpoints."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import cint


def _require_viewer() -> None:
    roles = set(frappe.get_roles(frappe.session.user))
    if roles.isdisjoint({"Fateh Viewer", "Price Approver", "System Manager"}):
        frappe.throw(_("Not authorised"), frappe.PermissionError)


@frappe.whitelist()
def filters() -> dict[str, Any]:
    """Return companies and warehouses visible to the current user.

    Used by the home screen to populate the company + warehouse pickers.
    """
    _require_viewer()

    companies = frappe.get_all(
        "Company",
        fields=["name", "abbr", "country", "default_currency"],
        order_by="name",
    )

    warehouses_raw = frappe.get_all(
        "Warehouse",
        filters={"disabled": 0, "is_group": 0},
        fields=["name", "warehouse_name", "company", "parent_warehouse"],
        order_by="company asc, warehouse_name asc",
    )
    # `get_all` already honours Frappe's permission query; no extra gate.
    warehouses = [
        {
            "name": w.name,
            "label": w.warehouse_name or w.name,
            "company": w.company,
            "parent": w.parent_warehouse,
        }
        for w in warehouses_raw
    ]
    return {"companies": companies, "warehouses": warehouses}


@frappe.whitelist()
def list_items(
    warehouse: str = "",
    company: str = "",
    search: str = "",
    item_group: str = "",
    sort: str = "name",
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    """List items with qty aggregated for the selected warehouse or company.

    - If `warehouse` is given, qty = `Bin.actual_qty` in that warehouse.
    - Else if `company` is given, qty = sum across all warehouses of that company.
    - Else, qty = sum across every warehouse the user can read.
    """
    _require_viewer()
    limit = max(1, min(int(limit or 50), 200))
    offset = max(0, int(offset or 0))
    search = (search or "").strip()

    # Build the warehouse set we'll aggregate over
    wh_filters: dict[str, Any] = {"disabled": 0, "is_group": 0}
    if warehouse:
        wh_filters["name"] = warehouse
    elif company:
        wh_filters["company"] = company

    wh_rows = frappe.get_all("Warehouse", filters=wh_filters, fields=["name", "company"])
    visible_wh = [w.name for w in wh_rows]

    # Base Item filter
    item_filters: list[Any] = ["i.disabled = 0", "i.has_variants = 0"]
    params: dict[str, Any] = {}
    if item_group:
        item_filters.append("i.item_group = %(item_group)s")
        params["item_group"] = item_group
    if search:
        item_filters.append(
            "(i.name LIKE %(q)s OR i.item_name LIKE %(q)s OR i.item_name_ar LIKE %(q)s)"
        )
        params["q"] = f"%{search}%"

    # Aggregate qty via LEFT JOIN so items with no Bin still show (qty = 0)
    if visible_wh:
        placeholders = ", ".join(f"%(wh_{idx})s" for idx in range(len(visible_wh)))
        for idx, wh in enumerate(visible_wh):
            params[f"wh_{idx}"] = wh
        qty_join = f"""
            LEFT JOIN (
                SELECT item_code,
                       SUM(actual_qty)    AS total_actual,
                       SUM(reserved_qty)  AS total_reserved,
                       SUM(projected_qty) AS total_projected,
                       SUM(ordered_qty)   AS total_ordered
                FROM `tabBin`
                WHERE warehouse IN ({placeholders})
                GROUP BY item_code
            ) b ON b.item_code = i.name
        """
    else:
        # No visible warehouses → qty columns are null
        qty_join = "LEFT JOIN (SELECT NULL AS item_code) b ON b.item_code = i.name"

    sort_sql = {
        "qty_desc": "COALESCE(b.total_actual, 0) DESC, i.name ASC",
        "qty_asc": "COALESCE(b.total_actual, 0) ASC, i.name ASC",
        "name": "i.name ASC",
    }.get(sort, "i.name ASC")

    where_sql = " AND ".join(item_filters)
    params.update({"limit": limit, "offset": offset})

    rows = frappe.db.sql(
        f"""
        SELECT
            i.name             AS item_code,
            i.item_name        AS item_name,
            i.item_name_ar     AS item_name_ar,
            i.stock_uom        AS stock_uom,
            i.item_group       AS item_group,
            i.image            AS image,
            COALESCE(b.total_actual, 0)    AS actual_qty,
            COALESCE(b.total_reserved, 0)  AS reserved_qty,
            COALESCE(b.total_projected, 0) AS projected_qty,
            COALESCE(b.total_ordered, 0)   AS ordered_qty
        FROM `tabItem` i
        {qty_join}
        WHERE {where_sql}
        ORDER BY {sort_sql}
        LIMIT %(limit)s OFFSET %(offset)s
        """,
        params,
        as_dict=True,
    )

    count_row = frappe.db.sql(
        f"SELECT COUNT(*) AS n FROM `tabItem` i WHERE {where_sql}",
        {k: v for k, v in params.items() if k in {"q", "item_group"}},
        as_dict=True,
    )
    total = int(count_row[0]["n"]) if count_row else 0

    # Find max qty for scaling mini-bars client-side
    max_qty = max((float(r["actual_qty"] or 0) for r in rows), default=0.0)

    return {
        "rows": [
            {
                "item_code": r["item_code"],
                "item_name": r["item_name"],
                "item_name_ar": r["item_name_ar"],
                "stock_uom": r["stock_uom"],
                "item_group": r["item_group"],
                "image": r["image"],
                "actual_qty": float(r["actual_qty"] or 0),
                "reserved_qty": float(r["reserved_qty"] or 0),
                "projected_qty": float(r["projected_qty"] or 0),
                "ordered_qty": float(r["ordered_qty"] or 0),
            }
            for r in rows
        ],
        "total": total,
        "offset": offset,
        "limit": limit,
        "max_qty": max_qty,
        "scope": {
            "warehouse": warehouse or None,
            "company": company or None,
            "warehouse_count": len(visible_wh),
        },
    }


@frappe.whitelist()
def search(q: str = "", limit: int = 20) -> list[dict[str, Any]]:
    _require_viewer()
    q = (q or "").strip()
    limit = max(1, min(int(limit or 20), 50))
    if not q:
        return []

    like = f"%{q}%"
    # Barcode exact match first
    rows: list[dict[str, Any]] = []
    barcode_item = frappe.db.get_value("Item Barcode", {"barcode": q}, "parent")
    if barcode_item:
        rows.append(_item_summary(barcode_item))

    existing_codes = {r["item_code"] for r in rows}
    codes = frappe.db.sql(
        """
        SELECT name AS item_code
        FROM `tabItem`
        WHERE disabled = 0
          AND has_variants = 0
          AND (name LIKE %(q)s OR item_name LIKE %(q)s OR item_name_ar LIKE %(q)s)
        ORDER BY
          CASE WHEN name = %(exact)s THEN 0 ELSE 1 END,
          name
        LIMIT %(limit)s
        """,
        {"q": like, "exact": q, "limit": limit},
        as_dict=True,
    )
    for r in codes:
        if r["item_code"] in existing_codes:
            continue
        rows.append(_item_summary(r["item_code"]))
        if len(rows) >= limit:
            break
    return rows


def _item_summary(item_code: str) -> dict[str, Any]:
    item = frappe.db.get_value(
        "Item",
        item_code,
        ["name", "item_name", "item_name_ar", "stock_uom", "image", "item_group", "disabled"],
        as_dict=True,
    )
    if not item:
        return {"item_code": item_code}
    return {
        "item_code": item.name,
        "item_name": item.item_name,
        "item_name_ar": item.item_name_ar,
        "stock_uom": item.stock_uom,
        "image": item.image,
        "item_group": item.item_group,
    }


@frappe.whitelist()
def stock(item_code: str) -> dict[str, Any]:
    _require_viewer()
    if not item_code:
        frappe.throw(_("item_code is required"))
    if not frappe.db.exists("Item", item_code):
        frappe.throw(_("Item {0} not found").format(item_code), frappe.DoesNotExistError)

    # Load bins the user has read permission on via Frappe's permission query.
    bins = frappe.get_all(
        "Bin",
        filters={"item_code": item_code},
        fields=[
            "warehouse",
            "actual_qty",
            "reserved_qty",
            "ordered_qty",
            "projected_qty",
            "stock_uom",
        ],
        order_by="warehouse asc",
    )

    # Strip bins whose warehouse is disabled. Permission is already enforced
    # by the ERPNext Bin permission query; do not double-gate.
    visible: list[dict[str, Any]] = []
    total = {"actual": 0.0, "reserved": 0.0, "ordered": 0.0, "projected": 0.0}
    for row in bins:
        wh = frappe.db.get_value(
            "Warehouse", row.warehouse, ["warehouse_name", "disabled", "company"], as_dict=True
        )
        if not wh or wh.disabled:
            continue
        visible.append(
            {
                "warehouse": row.warehouse,
                "warehouse_name": wh.warehouse_name or row.warehouse,
                "company": wh.company,
                "actual_qty": float(row.actual_qty or 0),
                "reserved_qty": float(row.reserved_qty or 0),
                "ordered_qty": float(row.ordered_qty or 0),
                "projected_qty": float(row.projected_qty or 0),
                "stock_uom": row.stock_uom,
            }
        )
        total["actual"] += float(row.actual_qty or 0)
        total["reserved"] += float(row.reserved_qty or 0)
        total["ordered"] += float(row.ordered_qty or 0)
        total["projected"] += float(row.projected_qty or 0)

    return {
        "item_code": item_code,
        "item": _item_summary(item_code),
        "bins": visible,
        "totals": total,
    }


@frappe.whitelist()
def prices(item_code: str) -> dict[str, Any]:
    _require_viewer()
    if not item_code:
        frappe.throw(_("item_code is required"))

    settings = frappe.get_cached_doc("Fateh Support Settings")
    cost_floor_list = (settings.get("cost_floor_price_list") or "").strip()

    roles = set(frappe.get_roles(frappe.session.user))
    is_approver = bool(roles & {"Price Approver", "System Manager"})

    raw = frappe.get_all(
        "Item Price",
        filters={"item_code": item_code, "selling": 1},
        fields=[
            "name",
            "price_list",
            "price_list_rate",
            "currency",
            "uom",
            "valid_from",
            "valid_upto",
        ],
        order_by="price_list",
    )

    # Drop cost-floor Price List rows for non-approvers.
    # Always drop inter-company price lists.
    rows: list[dict[str, Any]] = []
    for r in raw:
        if (
            not is_approver
            and cost_floor_list
            and r.price_list
            and r.price_list.lower() == cost_floor_list.lower()
        ):
            continue
        if r.price_list and "inter" in r.price_list.lower():
            continue
        if not frappe.has_permission("Price List", ptype="read", doc=r.price_list):
            continue
        rows.append(
            {
                "price_list": r.price_list,
                "price_list_label": frappe.db.get_value("Price List", r.price_list, "price_list_name")
                or r.price_list,
                "price_list_rate": float(r.price_list_rate or 0),
                "currency": r.currency,
                "uom": r.uom,
                "valid_from": r.valid_from,
                "valid_upto": r.valid_upto,
            }
        )

    result: dict[str, Any] = {
        "item_code": item_code,
        "rows": rows,
        "is_approver": is_approver,
    }
    if is_approver and cint(settings.get("show_valuation_to_approvers")):
        result["valuation_rate"] = float(
            frappe.db.get_value("Item", item_code, "valuation_rate") or 0
        )
        result["last_purchase_rate"] = float(
            frappe.db.get_value("Item", item_code, "last_purchase_rate") or 0
        )
    return result
