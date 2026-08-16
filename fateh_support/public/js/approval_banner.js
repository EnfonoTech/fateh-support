// Fateh Support — source-doc banner for Quotation / Sales Order / Sales Invoice.
//
// Renders a prominent indicator when `custom_approval_status` is set, plus
// quick actions: reload the request, clear the flag, or jump to the
// Approval Request record.

(function () {
  const TARGETS = ["Quotation", "Sales Order", "Sales Invoice"];

  function indicatorColor(status) {
    if (status === "Pending Approval") return "orange";
    if (status === "Approved") return "green";
    if (status === "Rejected") return "red";
    return "gray";
  }

  function bannerIntent(status) {
    if (status === "Rejected") return "red";
    if (status === "Pending Approval") return "orange";
    if (status === "Approved") return "green";
    return "blue";
  }

  function banner_html(status, note, approver, requestName) {
    const color = bannerIntent(status);
    const bg = { red: "#FEE2E2", orange: "#FEF3C7", green: "#D1FAE5", blue: "#DBEAFE" }[color];
    const border = { red: "#FCA5A5", orange: "#FDE68A", green: "#A7F3D0", blue: "#BFDBFE" }[color];
    const ink = { red: "#991B1B", orange: "#92400E", green: "#065F46", blue: "#1E40AF" }[color];
    const label = {
      "Pending Approval": "Waiting for approval",
      "Approved": "Approval granted",
      "Rejected": "Price approval rejected",
    }[status] || status;

    const noteHtml = note
      ? `<div style="margin-top:6px;font-size:13px;color:${ink};"><b>Note:</b> ${frappe.utils.escape_html(note)}</div>`
      : "";
    const approverHtml = approver
      ? `<div style="margin-top:4px;font-size:12px;color:${ink};opacity:0.8;">Decided by ${frappe.utils.escape_html(approver)}</div>`
      : "";
    const link = requestName
      ? `<a href="/app/sales-price-approval-request/${encodeURIComponent(requestName)}" style="margin-inline-start:12px;font-weight:600;color:${ink};text-decoration:underline;">${frappe.utils.escape_html(requestName)}</a>`
      : "";

    return `
      <div class="fateh-approval-banner" style="
        background:${bg};
        border:1px solid ${border};
        border-radius:8px;
        padding:14px 16px;
        margin-bottom:12px;
        color:${ink};
        font-family:inherit;
      ">
        <div style="display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;">
          <div>
            <div style="font-weight:600;font-size:14px;">${label}${link}</div>
            ${approverHtml}
            ${noteHtml}
          </div>
          <div style="font-size:12px;opacity:0.85;">
            ${
              status === "Rejected"
                ? "Raise rates to the minimum selling price, save, and submit again to raise a new approval."
                : status === "Pending Approval"
                ? "An approver will decide in the mobile app or from the request in desk."
                : ""
            }
          </div>
        </div>
      </div>
    `;
  }

  function render(frm) {
    if (!frm || !frm.layout || !frm.layout.wrapper) return;
    const wrapper = frm.layout.wrapper;
    // Remove any existing banner
    wrapper.find(".fateh-approval-banner-host").remove();

    const status = frm.doc && frm.doc.custom_approval_status;
    if (!status) return;

    const host = $(
      `<div class="fateh-approval-banner-host" style="padding:0 var(--padding-md, 15px);"></div>`
    );
    host.html(
      banner_html(
        status,
        frm.doc.custom_approval_decision_note,
        frm.doc.custom_approval_approver,
        frm.doc.custom_approval_request
      )
    );
    // Insert at top of form body
    const body = wrapper.find(".form-layout").first();
    if (body.length) {
      body.prepend(host);
    } else {
      wrapper.prepend(host);
    }
  }

  function setIndicator(frm) {
    const status = frm.doc && frm.doc.custom_approval_status;
    if (!status) return;
    frm.dashboard.set_headline(
      `<span class="indicator ${indicatorColor(status)}">Price Approval: ${frappe.utils.escape_html(
        status
      )}</span>`
    );
  }

  TARGETS.forEach((dt) => {
    frappe.ui.form.on(dt, {
      refresh(frm) {
        render(frm);
        setIndicator(frm);
        addActions(frm);
      },
      custom_approval_status(frm) {
        render(frm);
        setIndicator(frm);
      },
    });
  });

  function addActions(frm) {
    if (!frm.doc || !frm.doc.custom_approval_request) return;
    frm.add_custom_button(
      "Open Approval Request",
      function () {
        frappe.set_route("Form", "Sales Price Approval Request", frm.doc.custom_approval_request);
      },
      "Price Approval"
    );
    if (frm.doc.custom_approval_status === "Rejected" && frm.doc.docstatus === 0) {
      frm.add_custom_button(
        "Clear Rejection Flag",
        function () {
          frappe.confirm(
            "Clear the rejected flag and allow a fresh approval on next submit?",
            function () {
              frm.set_value("custom_approval_status", "");
              frm.set_value("custom_approval_request", null);
              frm.set_value("custom_approval_decision_note", null);
              frm.set_value("custom_approval_approver", null);
              frm.save().then(function () {
                frappe.show_alert({
                  message: "Flag cleared. Adjust rates and submit again.",
                  indicator: "green",
                });
              });
            }
          );
        },
        "Price Approval"
      );
    }
  }
})();
