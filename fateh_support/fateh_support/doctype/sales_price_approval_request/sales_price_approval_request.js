// Desk approval UI for Sales Price Approval Request.
//
// Same server path as the mobile app (`api.approvals.decide`), so the two
// surfaces can never drift: the endpoint owns the role check, the "already
// decided" guard, the source-doc write-back and the notifications.

frappe.ui.form.on("Sales Price Approval Request", {
  refresh(frm) {
    set_headline(frm);
    add_decision_buttons(frm);
    add_source_button(frm);
  },
});

function is_approver() {
  return frappe.user.has_role("Price Approver") || frappe.user.has_role("System Manager");
}

function set_headline(frm) {
  const colors = { Pending: "orange", Approved: "green", Rejected: "red" };
  const variance = flt(frm.doc.variance_pct || 0);
  const parts = [
    `<span class="indicator ${colors[frm.doc.status] || "gray"}">${__(frm.doc.status)}</span>`,
  ];
  if (variance) {
    parts.push(
      `<span style="margin-inline-start:12px;">${__("Variance")}: <b>${format_number(
        variance,
        null,
        2
      )}%</b></span>`
    );
  }
  if (frm.doc.line_total_impact) {
    parts.push(
      `<span style="margin-inline-start:12px;">${__("Impact")}: <b>${format_currency(
        frm.doc.line_total_impact,
        frm.doc.currency
      )}</b></span>`
    );
  }
  frm.dashboard.set_headline(parts.join(""));
}

function add_source_button(frm) {
  if (!frm.doc.source_doctype || !frm.doc.source_name) return;
  frm.add_custom_button(__("Open {0}", [__(frm.doc.source_doctype)]), () => {
    frappe.set_route("Form", frm.doc.source_doctype, frm.doc.source_name);
  });
}

function add_decision_buttons(frm) {
  if (frm.is_new() || frm.doc.status !== "Pending" || !is_approver()) return;

  frm.page.set_primary_action(__("Approve"), () => prompt_decision(frm, "approve"));
  frm.add_custom_button(__("Reject"), () => prompt_decision(frm, "reject")).addClass(
    "btn-danger"
  );
}

function prompt_decision(frm, action) {
  const approving = action === "approve";
  const d = new frappe.ui.Dialog({
    title: approving ? __("Approve this request?") : __("Reject this request?"),
    fields: [
      {
        fieldname: "note",
        fieldtype: "Small Text",
        label: __("Decision note"),
        reqd: approving ? 0 : 1,
        description: approving
          ? __("Optional note for the requester.")
          : __("Required — tell the requester why."),
      },
    ],
    primary_action_label: approving ? __("Approve") : __("Reject"),
    primary_action(values) {
      d.hide();
      frappe.call({
        method: "fateh_support.api.approvals.decide",
        type: "POST",
        args: { name: frm.doc.name, action, note: values.note || "" },
        freeze: true,
        freeze_message: approving ? __("Approving...") : __("Rejecting..."),
        callback() {
          frappe.show_alert({
            message: approving ? __("Approved") : __("Rejected"),
            indicator: approving ? "green" : "red",
          });
          frm.reload_doc();
        },
      });
    },
  });
  d.show();
}
