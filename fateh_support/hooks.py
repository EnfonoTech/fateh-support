app_name = "fateh_support"
app_title = "Fateh Trading"
app_publisher = "Enfono Technologies"
app_description = "ERPNext Support App for stock visibility and below-cost approval workflow."
app_email = "hello@enfono.com"
app_license = "Proprietary"

required_apps = ["frappe", "erpnext"]

app_include_js = []
app_include_css = []

doctype_js = {
    "Quotation": "public/js/approval_banner.js",
    "Sales Order": "public/js/approval_banner.js",
    "Sales Invoice": "public/js/approval_banner.js",
}

website_route_rules = [
    {"from_route": "/fateh/<path:app_path>", "to_route": "fateh"},
    # No rules for the service worker or the manifest: `to_route` cannot
    # dispatch to `api/method/...`, so both 404'd. They are plain static files
    # in `www/` now, which also gets them the right MIME type — a worker
    # served as octet-stream is refused by the browser outright.
]

_APPROVAL_GATE = {
    "before_submit": "fateh_support.approvals.gate.check_cost_floor",
    # Raises the request for a document the gate had to save as a draft,
    # because before_submit runs before the row exists.
    "after_insert": "fateh_support.approvals.gate.raise_request_for_saved_draft",
}

doc_events = {
    "Quotation": _APPROVAL_GATE,
    "Sales Order": _APPROVAL_GATE,
    "Sales Invoice": _APPROVAL_GATE,
}

after_migrate = [
    "fateh_support.install.ensure_capacitor_cors",
    "fateh_support.install.seed_settings",
]

after_install = "fateh_support.install.after_install"

fixtures = [
    {"dt": "Role", "filters": [["name", "in", ["Fateh Viewer", "Price Approver"]]]},
    {
        "dt": "Custom Field",
        "filters": [
            [
                "name",
                "in",
                [
                    "Quotation-custom_approval_status",
                    "Quotation-custom_approval_request",
                    "Quotation-custom_approval_approver",
                    "Quotation-custom_approval_decision_note",
                    "Sales Order-custom_approval_status",
                    "Sales Order-custom_approval_request",
                    "Sales Order-custom_approval_approver",
                    "Sales Order-custom_approval_decision_note",
                    "Sales Invoice-custom_approval_status",
                    "Sales Invoice-custom_approval_request",
                    "Sales Invoice-custom_approval_approver",
                    "Sales Invoice-custom_approval_decision_note",
                    "Item-item_name_ar",
                ],
            ]
        ],
    },
]

permission_query_conditions = {
    "Sales Price Approval Request": "fateh_support.approvals.permissions.get_permission_query_conditions",
}

has_permission = {
    "Sales Price Approval Request": "fateh_support.approvals.permissions.has_permission",
}

scheduler_events = {
    "hourly": [
        "fateh_support.notifications.push.cleanup_dead_subscriptions",
    ],
}
