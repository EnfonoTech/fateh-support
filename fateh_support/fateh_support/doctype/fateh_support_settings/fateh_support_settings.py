import frappe
from frappe.model.document import Document


class FatehSupportSettings(Document):
    def validate(self) -> None:
        if self.enable_push and not (self.vapid_public_key and self.vapid_private_key):
            frappe.msgprint(
                frappe._("Push enabled but VAPID keys missing — push will be skipped until keys are set."),
                alert=True,
                indicator="orange",
            )
