frappe.listview_settings['SaaS Subscription'] = {
	add_fields: ["tenant", "plan", "status", "starts_on", "ends_on"],
	get_indicator: function(doc) {
		if (doc.status === "Active") {
			return [__("Active"), "green", "status,=,Active"];
		} else if (doc.status === "Trial") {
			return [__("Trial"), "blue", "status,=,Trial"];
		} else if (doc.status === "Draft") {
			return [__("Draft"), "grey", "status,=,Draft"];
		} else if (doc.status === "Grace Period") {
			return [__("Grace Period"), "orange", "status,=,Grace Period"];
		} else if (doc.status === "Cancelled") {
			return [__("Cancelled"), "red", "status,=,Cancelled"];
		} else if (doc.status === "Expired") {
			return [__("Expired"), "darkgrey", "status,=,Expired"];
		}
	},
	onload: function(listview) {
		// Add custom button for deleting subscription with cleanup
		listview.page.add_menu_item(__('Delete Subscription (with Cleanup)'), function() {
			let selected_docs = listview.get_checked_items();
			if (selected_docs.length === 0) {
				frappe.msgprint(__('Please select at least one subscription to delete'));
				return;
			}

			let warning_message = __('Are you sure you want to delete {0} subscription(s)? This will also delete related provisioning requests. This action cannot be undone.', [selected_docs.length]);

			frappe.confirm(
				warning_message,
				function() {
					selected_docs.forEach(function(doc) {
						frappe.model.delete_doc('SaaS Subscription', doc.name, function() {
							frappe.msgprint(__('Subscription {0} deleted successfully with cleanup', [doc.name]));
							listview.refresh();
						});
					});
				}
			);
		}, true);
	}
};
