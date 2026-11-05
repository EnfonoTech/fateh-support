"""Tick "Show in Fateh App" on the price lists the app shows today.

The app now lists only ticked price lists. Ticking the current set on
upgrade means nothing disappears from anyone's item screen until a price
list is unticked on purpose.

Runs before fixtures are synced, so it creates the field itself first; the
fixture sync later finds it in place.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	create_custom_fields(
		{
			"Price List": [
				{
					"fieldname": "custom_show_in_fateh_app",
					"fieldtype": "Check",
					"label": "Show in Fateh App",
					"insert_after": "enabled",
					"default": "0",
				}
			]
		},
		update=False,
	)
	# Same rule the app applied before the tick existed: selling lists, never
	# an inter-company list.
	for name in frappe.get_all("Price List", filters={"selling": 1}, pluck="name"):
		if "inter" in (name or "").lower():
			continue
		frappe.db.set_value("Price List", name, "custom_show_in_fateh_app", 1, update_modified=False)
