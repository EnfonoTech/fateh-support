"""Shared fixture helpers for Fateh Trading test cases."""

from __future__ import annotations

from typing import Any

import frappe


def ensure_currency(name: str = "USD") -> str:
    if not frappe.db.exists("Currency", name):
        frappe.get_doc({"doctype": "Currency", "currency_name": name, "enabled": 1}).insert(
            ignore_permissions=True
        )
    return name


def ensure_uom(name: str = "Nos") -> str:
    if not frappe.db.exists("UOM", name):
        frappe.get_doc({"doctype": "UOM", "uom_name": name}).insert(ignore_permissions=True)
    return name


def ensure_company(name: str = "Fateh Test Co") -> str:
    if frappe.db.exists("Company", name):
        return name
    frappe.get_doc(
        {
            "doctype": "Company",
            "company_name": name,
            "abbr": "FTC",
            "default_currency": ensure_currency(),
            "country": "Saudi Arabia",
        }
    ).insert(ignore_permissions=True)
    return name


def ensure_warehouse(warehouse_name: str, company: str) -> str:
    """Return the full warehouse name, creating it if absent.

    Frappe autonames a Warehouse `<warehouse_name> - <company abbr>`, so the
    existence check has to use the abbr — slicing the company name instead
    looks for a document that can never exist, and the insert then collides
    with the warehouse left behind by the previous run.
    """
    abbr = frappe.get_cached_value("Company", company, "abbr")
    full_name = f"{warehouse_name} - {abbr}"
    if frappe.db.exists("Warehouse", full_name):
        return full_name
    frappe.get_doc(
        {
            "doctype": "Warehouse",
            "warehouse_name": warehouse_name,
            "company": company,
        }
    ).insert(ignore_permissions=True)
    return full_name


def ensure_item(item_code: str, valuation_rate: float = 100.0) -> str:
    if frappe.db.exists("Item", item_code):
        return item_code
    frappe.get_doc(
        {
            "doctype": "Item",
            "item_code": item_code,
            "item_name": item_code,
            "item_name_ar": item_code + " AR",
            "item_group": "All Item Groups",
            "stock_uom": ensure_uom(),
            "is_stock_item": 1,
            "valuation_rate": valuation_rate,
            "last_purchase_rate": valuation_rate,
        }
    ).insert(ignore_permissions=True)
    return item_code


def ensure_price_list(name: str, currency: str = "USD", selling: int = 1) -> str:
    if frappe.db.exists("Price List", name):
        return name
    frappe.get_doc(
        {
            "doctype": "Price List",
            "price_list_name": name,
            "currency": currency,
            "selling": selling,
            "enabled": 1,
        }
    ).insert(ignore_permissions=True)
    return name


def set_item_price(item_code: str, price_list: str, rate: float, currency: str = "USD") -> None:
    existing = frappe.db.get_value(
        "Item Price", {"item_code": item_code, "price_list": price_list}, "name"
    )
    if existing:
        frappe.db.set_value("Item Price", existing, "price_list_rate", rate)
        return
    frappe.get_doc(
        {
            "doctype": "Item Price",
            "item_code": item_code,
            "price_list": price_list,
            "price_list_rate": rate,
            "currency": currency,
            "selling": 1,
        }
    ).insert(ignore_permissions=True)


def ensure_user(email: str, roles: list[str]) -> str:
    if not frappe.db.exists("User", email):
        user = frappe.get_doc(
            {
                "doctype": "User",
                "email": email,
                "first_name": email.split("@")[0],
                "send_welcome_email": 0,
                "enabled": 1,
            }
        )
        user.insert(ignore_permissions=True)
    user = frappe.get_doc("User", email)
    existing = {r.role for r in user.roles}
    for role in roles:
        if role not in existing:
            user.append("roles", {"role": role})
    user.flags.ignore_permissions = True
    user.save(ignore_permissions=True)
    return email


def ensure_customer(name: str = "Fateh Test Customer") -> str:
    if not frappe.db.exists("Customer", name):
        frappe.get_doc(
            {
                "doctype": "Customer",
                "customer_name": name,
                "customer_type": "Company",
            }
        ).insert(ignore_permissions=True)
    return name


def ensure_quotation(company: str, item_code: str, rate: float = 150.0) -> str:
    """A draft Quotation to hang approval requests off.

    `Sales Price Approval Request.source_name` is a Dynamic Link, so it has
    to resolve to a real record — a placeholder name fails link validation on
    every insert and save. Kept in draft: the gate only fires on submit.
    """
    customer = ensure_customer()
    existing = frappe.db.get_value(
        "Quotation", {"party_name": customer, "company": company, "docstatus": 0}, "name"
    )
    if existing:
        return existing

    quotation = frappe.get_doc(
        {
            "doctype": "Quotation",
            "quotation_to": "Customer",
            "party_name": customer,
            "company": company,
            "currency": ensure_currency(),
            "conversion_rate": 1,
            "selling_price_list": "Standard Selling",
            "transaction_date": frappe.utils.nowdate(),
            "items": [
                {
                    "item_code": item_code,
                    "qty": 1,
                    "rate": rate,
                    "uom": ensure_uom(),
                    "conversion_factor": 1,
                }
            ],
        }
    )
    quotation.insert(ignore_permissions=True)
    return quotation.name


def configure_cost_floor(price_list: str, exempt: list[str] | None = None) -> None:
    settings = frappe.get_single("Fateh Support Settings")
    settings.cost_floor_price_list = price_list
    settings.enable_push = 0  # keep tests offline
    settings.set("exempt_price_lists", [])
    for name in exempt or []:
        settings.append("exempt_price_lists", {"price_list": ensure_price_list(name)})
    settings.flags.ignore_permissions = True
    settings.save(ignore_permissions=True)


def reset_test_sandbox() -> dict[str, Any]:
    """Build a self-consistent sandbox for approval-flow tests."""
    company = ensure_company()
    warehouse = ensure_warehouse("Main", company)
    ensure_price_list("Standard Selling")
    cost_floor = ensure_price_list("Fateh Cost Floor")
    item = ensure_item("FATEH-TEST-001", valuation_rate=80.0)
    set_item_price(item, "Standard Selling", 150.0)
    set_item_price(item, cost_floor, 100.0)
    viewer = ensure_user("fateh-viewer@example.com", ["Fateh Viewer"])
    approver = ensure_user("fateh-approver@example.com", ["Price Approver", "Fateh Viewer"])
    requester = ensure_user("fateh-requester@example.com", ["Fateh Viewer", "Sales User"])
    configure_cost_floor(cost_floor)
    return {
        "company": company,
        "warehouse": warehouse,
        "item": item,
        "cost_floor": cost_floor,
        "viewer": viewer,
        "approver": approver,
        "requester": requester,
        "customer": ensure_customer(),
        "quotation": ensure_quotation(company, item),
    }
