frappe.listview_settings['Provisioning Request'] = {
	add_fields: ["tenant", "subscription", "request_type", "status", "requested_by"],
	get_indicator: function(doc) {
		if (doc.status === "Completed") {
			return [__("Completed"), "green", "status,=,Completed"];
		} else if (doc.status === "Running") {
			return [__("Running"), "blue", "status,=,Running"];
		} else if (doc.status === "Queued") {
			return [__("Queued"), "grey", "status,=,Queued"];
		} else if (doc.status === "Failed") {
			return [__("Failed"), "red", "status,=,Failed"];
		}
	},
	onload: function(listview) {
		// Add custom button for deleting provisioning request with cleanup
		listview.page.add_menu_item(__('Delete Request (with Cleanup)'), function() {
			let selected_docs = listview.get_checked_items();
			if (selected_docs.length === 0) {
				frappe.msgprint(__('Please select at least one request to delete'));
				return;
			}

			let warning_message = __('Are you sure you want to delete {0} provisioning request(s)? This will also update linked subscriptions. This action cannot be undone.', [selected_docs.length]);

			frappe.confirm(
				warning_message,
				function() {
					selected_docs.forEach(function(doc) {
						frappe.model.delete_doc('Provisioning Request', doc.name, function() {
							frappe.msgprint(__('Provisioning Request {0} deleted successfully with cleanup', [doc.name]));
							listview.refresh();
						});
					});
				}
			);
		}, true);
	}
};
