frappe.listview_settings['SaaS Tenant'] = {
	add_fields: ["admin_username", "admin_password", "site_url", "status", "access_url", "site_folder"],
	get_indicator: function(doc) {
		if (doc.status === "Active") {
			return [t("Active", "نشط"), "green", "status,=,Active"];
		} else if (doc.status === "Draft") {
			return [t("Draft", "مسودة"), "grey", "status,=,Draft"];
		} else if (doc.status === "Provisioning") {
			return [t("Provisioning", "جارٍ التجهيز"), "orange", "status,=,Provisioning"];
		} else if (doc.status === "Suspended") {
			return [t("Suspended", "موقوف"), "red", "status,=,Suspended"];
		} else if (doc.status === "Archived") {
			return [t("Archived", "مؤرشف"), "darkgrey", "status,=,Archived"];
		}
	},
	onload: function(listview) {
		// Add custom button for copying admin password
		listview.page.add_menu_item(t("Copy Admin Password", "نسخ كلمة مرور المدير"), function() {
			let selected_docs = listview.get_checked_items();
			if (selected_docs.length === 0) {
				frappe.msgprint(t("Please select at least one tenant", "يرجى تحديد مستأجر واحد على الأقل"));
				return;
			}
			if (selected_docs.length > 1) {
				frappe.msgprint(t("Please select only one tenant to copy password", "يرجى تحديد مستأجر واحد فقط لنسخ كلمة المرور"));
				return;
			}
			let doc = selected_docs[0];
			if (doc.admin_password) {
				navigator.clipboard.writeText(doc.admin_password).then(function() {
					frappe.msgprint(t("Password copied to clipboard", "تم نسخ كلمة المرور إلى الحافظة"));
				}, function() {
					frappe.msgprint(t("Failed to copy password", "فشل نسخ كلمة المرور"));
				});
			} else {
				frappe.msgprint(t("No password available for this tenant", "لا توجد كلمة مرور متاحة لهذا المستأجر"));
			}
		}, true);

		// Add custom button for installing core apps
		listview.page.add_menu_item(t("Install Core Apps", "تثبيت التطبيقات الأساسية"), function() {
			let selected_docs = listview.get_checked_items();
			if (selected_docs.length === 0) {
				frappe.msgprint(t("Please select at least one tenant", "يرجى تحديد مستأجر واحد على الأقل"));
				return;
			}
			if (selected_docs.length > 1) {
				frappe.msgprint(t("Please select only one tenant", "يرجى تحديد مستأجر واحد فقط"));
				return;
			}
			let doc = selected_docs[0];
			if (!doc.site_folder) {
				frappe.msgprint(t("Site folder not available for this tenant", "مجلد الموقع غير متاح لهذا المستأجر"));
				return;
			}
			frappe.confirm(
				t("Are you sure you want to install core apps for {0}?", "هل أنت متأكد أنك تريد تثبيت التطبيقات الأساسية لـ {0}?").replace("{0}", doc.name),
				function() {
					frappe.call({
						method: 'erpgenex_saas.services.provisioning.install_core_apps',
						args: {
							site_folder: doc.site_folder
						},
						callback: function(r) {
							if (r.message) {
								frappe.msgprint(r.message);
								listview.refresh();
							}
						}
					});
				}
			);
		}, true);

		// Add custom button for deleting tenant with cleanup
		listview.page.add_menu_item(t("Delete Tenant (with Cleanup)", "حذف المستأجر (مع التنظيف)"), function() {
			let selected_docs = listview.get_checked_items();
			if (selected_docs.length === 0) {
				frappe.msgprint(t("Please select at least one tenant to delete", "يرجى تحديد مستأجر واحد على الأقل للحذف"));
				return;
			}

			let warning_message = t(
				"Are you sure you want to delete {0} tenant(s)? This will also delete the site folder, database, and all related subscriptions. This action cannot be undone.",
				"هل أنت متأكد أنك تريد حذف {0} مستأجر(ين)؟ سيتم أيضًا حذف مجلد الموقع وقاعدة البيانات وكل الاشتراكات المرتبطة. لا يمكن التراجع عن هذا الإجراء."
			).replace("{0}", selected_docs.length);

			frappe.confirm(
				warning_message,
				function() {
					selected_docs.forEach(function(doc) {
						frappe.model.delete_doc('SaaS Tenant', doc.name, function() {
							frappe.msgprint(t("Tenant {0} deleted successfully with cleanup", "تم حذف المستأجر {0} بنجاح مع التنظيف").replace("{0}", doc.name));
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
