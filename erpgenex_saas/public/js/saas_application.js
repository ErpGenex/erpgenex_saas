// i18n:managed-catalog — bilingual/regional catalog; UI via ar.csv
frappe.ui.form.on("SaaS Application", {
	refresh(frm) {
		localize_application_labels(frm);
		show_live_pricing_hint(frm);
	},
	after_save(frm) {
		frappe.show_alert({
			message: is_arabic_language()
				? "تم حفظ التغييرات وسيتم تحديث سوق التطبيقات مباشرة."
				: "Changes were saved and the marketplace will refresh immediately.",
			indicator: "green",
		});
		window.setTimeout(() => {
			if (frm && !frm.is_new()) {
				frm.reload_doc();
			}
		}, 300);
	},
});

function is_arabic_language() {
	const lang = (frappe.boot?.lang || frappe.user?.language || "").toLowerCase();
	return lang.startsWith("ar");
}

function t(en, ar) {
	return is_arabic_language() ? ar : en;
}

function localize_application_labels(frm) {
	const labels = {
		application_name: t("Application Name", "اسم التطبيق"),
		display_name: t("Display Name", "اسم العرض"),
		app_slug: t("App Slug", "الرابط المختصر"),
		category: t("Category", "الفئة"),
		distribution_section: t("Distribution", "التوزيع"),
		distribution_type: t("Distribution Type", "نوع التوزيع"),
		is_core: t("Core Free Application", "تطبيق أساسي مجاني"),
		repository_url: t("Repository URL", "رابط المستودع"),
		repository_provider: t("Repository Provider", "مزود المستودع"),
		repository_is_private: t("Repository Is Private", "المستودع خاص"),
		current_version: t("Current Version", "الإصدار الحالي"),
		latest_version: t("Latest Version", "أحدث إصدار"),
		update_available: t("Update Available", "تحديث متاح"),
		monthly_price: t("Monthly Price", "السعر الشهري"),
		annual_price: t("Annual Price", "السعر السنوي"),
		trial_days: t("Trial Days", "أيام التجربة"),
		source_code_section: t("Source Code Sale", "بيع الشيفرة"),
		source_code_available: t("Buy Source Code Available", "إتاحة شراء الشيفرة"),
		source_code_price: t("Source Code Price", "سعر الشيفرة"),
		source_license_terms: t("Source License Terms", "شروط ترخيص الشيفرة"),
		store_section: t("App Store", "متجر التطبيقات"),
		rating: t("Rating", "التقييم"),
		screenshots: t("Screenshots", "الصور"),
		release_history: t("Release History", "سجل الإصدارات"),
		changelog: t("Changelog", "سجل التغييرات"),
		is_active: t("Is Active", "نشط"),
		description: t("Description", "الوصف"),
	};

	Object.entries(labels).forEach(([fieldname, label]) => frm.set_df_property(fieldname, "label", label));

	frm.set_df_property(
		"monthly_price",
		"description",
		t("Updates appear in the marketplace immediately after saving.", "تظهر التحديثات في سوق التطبيقات فور الحفظ."),
	);
	frm.set_df_property(
		"annual_price",
		"description",
		t("Annual pricing is shown live to customers.", "السعر السنوي يظهر مباشرة للعملاء."),
	);
	frm.set_df_property(
		"source_code_price",
		"description",
		t("Source code price is reflected instantly in the marketplace.", "سعر الشيفرة ينعكس مباشرة في السوق."),
	);
}

function show_live_pricing_hint(frm) {
	if (!frm || frm.is_new()) {
		return;
	}

	frm.dashboard.clear_headline();
	frm.dashboard.set_headline(
		t(
			"Marketplace pricing refreshes automatically after save.",
			"سوق التطبيقات يتحدث تلقائيًا بعد الحفظ.",
		),
	);
}
