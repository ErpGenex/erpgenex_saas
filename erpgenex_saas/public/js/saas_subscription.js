frappe.ui.form.on("SaaS Subscription", {
	refresh(frm) {
		localize_subscription_labels(frm);
		localize_subscription_select_options(frm);
	},
});

function is_arabic_language() {
	const lang = (frappe.boot?.lang || frappe.user?.language || "").toLowerCase();
	return lang.startsWith("ar");
}

function t(en, ar) {
	return is_arabic_language() ? ar : en;
}

function localize_subscription_labels(frm) {
	const labels = {
		tenant: t("Tenant", "المستأجر"),
		plan: t("Plan", "الخطة"),
		application: t("Application", "التطبيق"),
		billing_cycle: t("Billing Cycle", "دورة الفوترة"),
		status: t("Status", "الحالة"),
		starts_on: t("Starts On", "يبدأ في"),
		ends_on: t("Ends On", "ينتهي في"),
		trial_ends_on: t("Trial Ends On", "تنتهي الفترة التجريبية في"),
		grace_period_days: t("Grace Period Days", "أيام فترة السماح"),
		features_enabled: t("Features Enabled", "تفعيل الخصائص"),
		disabled_reason: t("Disabled Reason", "سبب التعطيل"),
		provisioned: t("Provisioned", "تم التجهيز"),
		provisioning_request: t("Provisioning Request", "طلب التجهيز"),
		pricing_section: t("Pricing", "التسعير"),
		base_amount: t("Base Amount", "المبلغ الأساسي"),
		apps_amount: t("Applications Amount", "مبلغ التطبيقات"),
		extra_users_amount: t("Extra Users Amount", "مبلغ المستخدمين الإضافيين"),
		extra_storage_amount: t("Extra Storage Amount", "مبلغ التخزين الإضافي"),
		extra_services_amount: t("Extra Services Amount", "مبلغ الخدمات الإضافية"),
		total_amount: t("Total Amount", "المبلغ الإجمالي"),
	};

	Object.entries(labels).forEach(([fieldname, label]) => frm.set_df_property(fieldname, "label", label));

	frm.set_df_property("application", "description", t("Optional when the subscription is for a single paid app.", "اختياري عندما يكون الاشتراك لتطبيق مدفوع واحد."));
	frm.set_df_property("grace_period_days", "description", t("Extra days before the subscription is fully disabled.", "أيام إضافية قبل تعطيل الاشتراك بالكامل."));
	frm.set_df_property("disabled_reason", "description", t("Shown when the subscription is not active.", "يظهر عندما لا يكون الاشتراك نشطًا."));
}

function localize_subscription_select_options(frm) {
	localize_select_options(frm, "billing_cycle", {
		Monthly: t("Monthly", "شهري"),
		Quarterly: t("Quarterly", "ربع سنوي"),
		"Semi Annual": t("Semi Annual", "نصف سنوي"),
		Annual: t("Annual", "سنوي"),
		Lifetime: t("Lifetime", "مدى الحياة"),
		Trial: t("Trial", "تجريبي"),
	});
	localize_select_options(frm, "status", {
		Draft: t("Draft", "مسودة"),
		Trial: t("Trial", "تجريبي"),
		Active: t("Active", "نشط"),
		"Grace Period": t("Grace Period", "فترة سماح"),
		Paused: t("Paused", "موقوف مؤقتًا"),
		Cancelled: t("Cancelled", "ملغي"),
		Expired: t("Expired", "منتهي"),
	});
}

function localize_select_options(frm, fieldname, translations) {
	const field = frm.get_field(fieldname);
	if (!field || !field.$input || !field.$input.length) {
		return;
	}

	field.$input.find("option").each(function () {
		const value = (this.value || this.textContent || "").trim();
		if (translations[value]) {
			this.textContent = translations[value];
		}
	});
}
