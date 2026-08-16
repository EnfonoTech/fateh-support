// List view for Sales Price Approval Request: status colours plus bulk
// Approve / Reject, so a backlog can be cleared without opening every record.

frappe.listview_settings["Sales Price Approval Request"] = {
  add_fields: ["status", "variance_pct", "source_doctype", "source_name"],

  get_indicator(doc) {
    const map = {
      Pending: ["Pending", "orange", "status,=,Pending"],
      Approved: ["Approved", "green", "status,=,Approved"],
      Rejected: ["Rejected", "red", "status,=,Rejected"],
    };
    return map[doc.status] || [__(doc.status), "gray", "status,=," + doc.status];
  },

  onload(listview) {
    if (!frappe.user.has_role("Price Approver") && !frappe.user.has_role("System Manager")) return;

    listview.page.add_actions_menu_item(__("Approve"), () => bulk_decide(listview, "approve"), false);
    listview.page.add_actions_menu_item(__("Reject"), () => bulk_decide(listview, "reject"), false);
  },
};

function bulk_decide(listview, action) {
  const approving = action === "approve";
  const selected = listview.get_checked_items();
  const pending = selected.filter((d) => d.status === "Pending");

  if (!pending.length) {
    frappe.msgprint(__("Select at least one Pending request."));
    return;
  }

  const skipped = selected.length - pending.length;
  const d = new frappe.ui.Dialog({
    title: approving
      ? __("Approve {0} request(s)?", [pending.length])
      : __("Reject {0} request(s)?", [pending.length]),
    fields: [
      {
        fieldtype: "HTML",
        options: skipped
          ? `<p class="text-muted">${__(
              "{0} selected request(s) are already decided and will be skipped.",
              [skipped]
            )}</p>`
          : "",
      },
      {
        fieldname: "note",
        fieldtype: "Small Text",
        label: __("Decision note"),
        reqd: approving ? 0 : 1,
        description: __("Applied to every selected request."),
      },
    ],
    primary_action_label: approving ? __("Approve") : __("Reject"),
    primary_action(values) {
      d.hide();
      frappe.call({
        method: "fateh_support.api.approvals.decide_bulk",
        type: "POST",
        args: {
          names: pending.map((row) => row.name),
          action,
          note: values.note || "",
        },
        freeze: true,
        freeze_message: approving ? __("Approving...") : __("Rejecting..."),
        callback(r) {
          const res = r.message || { done: [], failed: [] };
          frappe.show_alert({
            message: __("{0} done, {1} failed", [res.done.length, res.failed.length]),
            indicator: res.failed.length ? "orange" : "green",
          });
          if (res.failed.length) {
            frappe.msgprint({
              title: __("Some requests were not decided"),
              indicator: "red",
              message: res.failed
                .map((f) => `<b>${frappe.utils.escape_html(f.name)}</b>: ${frappe.utils.escape_html(f.error)}`)
                .join("<br>"),
            });
          }
          listview.refresh();
        },
      });
    },
  });
  d.show();
}
