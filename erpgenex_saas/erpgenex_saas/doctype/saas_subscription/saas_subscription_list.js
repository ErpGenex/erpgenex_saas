// i18n:managed-catalog — bilingual/regional catalog; UI via ar.csv
frappe.listview_settings['SaaS Subscription'] = {
	add_fields: ["tenant", "plan", "status", "starts_on", "ends_on"],
	get_indicator: function(doc) {
		if (doc.status === "Active") {
			return [t("Active", "نشط"), "green", "status,=,Active"];
		} else if (doc.status === "Trial") {
			return [t("Trial", "تجريبي"), "blue", "status,=,Trial"];
		} else if (doc.status === "Draft") {
			return [t("Draft", "مسودة"), "grey", "status,=,Draft"];
		} else if (doc.status === "Grace Period") {
			return [t("Grace Period", "فترة سماح"), "orange", "status,=,Grace Period"];
		} else if (doc.status === "Cancelled") {
			return [t("Cancelled", "ملغي"), "red", "status,=,Cancelled"];
		} else if (doc.status === "Expired") {
			return [t("Expired", "منتهي"), "darkgrey", "status,=,Expired"];
		}
	},
	onload: function(listview) {
		// Add custom button for deleting subscription with cleanup
		listview.page.add_menu_item(t("Delete Subscription (with Cleanup)", "حذف الاشتراك (مع التنظيف)"), function() {
			let selected_docs = listview.get_checked_items();
			if (selected_docs.length === 0) {
				frappe.msgprint(t("Please select at least one subscription to delete", "يرجى تحديد اشتراك واحد على الأقل للحذف"));
				return;
			}

			let warning_message = t(
				"Are you sure you want to delete {0} subscription(s)? This will also delete related provisioning requests. This action cannot be undone.",
				"هل أنت متأكد أنك تريد حذف {0} اشتراك(ات)؟ سيتم أيضًا حذف طلبات التجهيز المرتبطة. لا يمكن التراجع عن هذا الإجراء."
			).replace("{0}", selected_docs.length);

			frappe.confirm(
				warning_message,
				function() {
					selected_docs.forEach(function(doc) {
						frappe.model.delete_doc('SaaS Subscription', doc.name, function() {
							frappe.msgprint(t("Subscription {0} deleted successfully with cleanup", "تم حذف الاشتراك {0} بنجاح مع التنظيف").replace("{0}", doc.name));
							listview.refresh();
						});
					});
				}
			);
		}, true);
	}
};

function is_arabic_language() {
	const lang = (frappe.boot?.lang || frappe.user?.language || "").toLowerCase();
	return lang.startsWith("ar");
}

function t(en, ar) {
	return is_arabic_language() ? ar : en;
}
