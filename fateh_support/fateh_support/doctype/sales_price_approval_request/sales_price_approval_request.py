"""Sales Price Approval Request controller.

Server-authoritative approval record for below-cost sales rates. Created by the
`before_submit` gate on Quotation and Sales Order, decided via the mobile app.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


class SalesPriceApprovalRequest(Document):
    def before_insert(self) -> None:
        if not self.requester:
            self.requester = frappe.session.user
        if not self.requested_at:
            self.requested_at = now_datetime()
        if not self.status:
            self.status = "Pending"

    def validate(self) -> None:
        self._recalculate_totals()
        if self.status == "Rejected" and not (self.decision_note or "").strip():
            frappe.throw(_("A rejection note is required."))

    def on_update(self) -> None:
        """Publish realtime + push on status transition."""
        # Only fire on genuine status changes (Frappe passes old doc via flags)
        old_status = (self.get_doc_before_save() or {}).get("status") if self.get_doc_before_save() else None
        if old_status == self.status:
            return

        from fateh_support.notifications import realtime, push, email

        if self.status == "Pending" and old_status in (None, ""):
            realtime.publish_approval_created(self)
            push.fanout_to_approvers(self)
            email.notify_approvers(self)
        elif self.status in ("Approved", "Rejected"):
            realtime.publish_approval_decided(self)
            push.notify_requester(self)
            email.notify_requester(self)

    def _recalculate_totals(self) -> None:
        total_proposed = 0.0
        total_floor = 0.0
        line_impact = 0.0
        for line in self.lines or []:
            qty = float(line.qty or 0)
            proposed = float(line.proposed_rate or 0)
            floor = float(line.cost_floor_rate or 0)
            line.variance_amount = proposed - floor
            line.variance_pct = ((proposed - floor) / floor * 100.0) if floor else 0.0
            line.line_total = qty * proposed
            total_proposed += qty * proposed
            total_floor += qty * floor
            line_impact += qty * (proposed - floor)

        self.total_proposed = total_proposed
        self.total_cost_floor = total_floor
        self.variance_amount = total_proposed - total_floor
        self.variance_pct = (
            ((total_proposed - total_floor) / total_floor * 100.0) if total_floor else 0.0
        )
        self.line_total_impact = line_impact
