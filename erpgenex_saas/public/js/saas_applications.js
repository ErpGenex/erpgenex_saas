(function() {
  const STR = window.__SAAS_APPLICATIONS__ || {};

  function t(key, fallback) {
    return STR[key] || fallback || key;
  }

  function qs(sel, root) {
    return (root || document).querySelector(sel);
  }

  function qsa(sel, root) {
    return Array.from((root || document).querySelectorAll(sel));
  }

  function showFeedback(message, kind) {
    const feedback = qs('#marketplace-feedback');
    if (!feedback) return;
    feedback.textContent = message || '';
    feedback.classList.remove('is-success', 'is-error');
    if (kind === 'success') feedback.classList.add('is-success');
    if (kind === 'error') feedback.classList.add('is-error');
    feedback.style.display = message ? 'block' : 'none';
  }

  function getReadableError(err) {
    if (!err) return '';
    if (typeof err === 'string') return err;
    if (err.message) return err.message;
    if (err._server_messages) {
      try {
        const messages = JSON.parse(err._server_messages);
        if (Array.isArray(messages) && messages.length) {
          return messages.map((item) => String(item).replace(/<[^>]+>/g, '')).join(' ');
        }
      } catch (e) {
        return String(err._server_messages).replace(/<[^>]+>/g, '');
      }
    }
    return String(err.exception || err.exc || '');
  }

  function callMethod(method, args) {
    return new Promise((resolve, reject) => {
      if (!window.frappe || !frappe.call) {
        reject(new Error('Frappe client is not available'));
        return;
      }
      frappe.call({
        method,
        args,
        callback: (response) => resolve(response.message || {}),
        error: (err) => reject(err),
      });
    });
  }

  const state = {
    portal: null,
    currentFilter: 'all',
    currentCategory: 'all',
    searchTerm: '',
    modal: null,
  };

  function tenantOptions() {
    return (state.portal?.tenants || []).map((tenant) => ({
      value: tenant.name,
      label: tenant.tenant_name || tenant.name,
      status: tenant.status,
    }));
  }

  function defaultTenant() {
    const options = tenantOptions();
    return options.length ? options[0].value : '';
  }

  function renderInstalledApps() {
    const panel = qs('#installed-apps-panel');
    const body = qs('#installed-apps-body');
    const loginHint = qs('#installed-apps-login');
    if (!panel || !body) return;

    if (!state.portal?.logged_in) {
      panel.style.display = 'block';
      body.innerHTML = '';
      if (loginHint) loginHint.style.display = 'block';
      return;
    }
    if (loginHint) loginHint.style.display = 'none';

    const rows = state.portal.installed_summary || [];
    if (!rows.length) {
      body.innerHTML = `<tr><td colspan="6">${t('no_installed', 'No applications installed yet. Use the marketplace below to add apps.')}</td></tr>`;
      panel.style.display = 'block';
      return;
    }

    body.innerHTML = rows.map((row) => {
      const sub = row.subscription || {};
      const license = row.license || {};
      const scenarioLabel = {
        included: t('included', 'Included'),
        free: t('free', 'Free'),
        subscription: t('subscription', 'Subscription'),
        source: t('source', 'Source Code'),
      }[row.scenario] || row.scenario;
      const billing = sub.billing_cycle ? `${sub.billing_cycle} · ${sub.status || ''}` : '—';
      return `<tr>
        <td><strong>${row.display_name || row.app_slug}</strong><div class="egx-muted">${row.app_slug}</div></td>
        <td>${row.tenant || '—'}</td>
        <td><span class="badge badge--info">${scenarioLabel}</span></td>
        <td>${billing}</td>
        <td>${license.license_key_masked || '—'}</td>
        <td class="installed-actions">
          ${license.license_key_masked ? `<button class="btn btn--sm btn--secondary" data-reveal-key="${row.tenant}|${row.app_slug}">${t('show_key', 'Show Key')}</button>` : ''}
          ${row.installed ? `<span class="badge badge--success">${t('installed', 'Installed')}</span>` : `<button class="btn btn--sm btn--primary" data-install="${row.tenant}|${row.app_slug}">${t('install', 'Install')}</button>`}
        </td>
      </tr>`;
    }).join('');

    qsa('[data-reveal-key]', body).forEach((btn) => {
      btn.addEventListener('click', () => {
        const [tenant, application] = btn.dataset.revealKey.split('|');
        revealLicenseKey(tenant, application);
      });
    });
    qsa('[data-install]', body).forEach((btn) => {
      btn.addEventListener('click', () => {
        const [tenant, application] = btn.dataset.install.split('|');
        installApplication(tenant, application);
      });
    });

    panel.style.display = 'block';
  }

  function renderScenarioCards() {
    const wrap = qs('#scenario-cards');
    if (!wrap || !state.portal?.scenarios) return;
    wrap.innerHTML = state.portal.scenarios.map((scenario, index) => `
      <article class="scenario-card">
        <span class="scenario-card__step">${index + 1}</span>
        <h3>${scenario.title}</h3>
        <p>${scenario.description}</p>
        ${scenario.billing_cycles ? `<div class="scenario-card__chips">${scenario.billing_cycles.map((cycle) => `<span class="badge badge--category">${cycle}</span>`).join('')}</div>` : ''}
      </article>
    `).join('');
  }

  function markInstalledCards() {
    const statusMap = {};
    (state.portal?.marketplace || []).forEach((app) => {
      const slug = app.app_slug || app.name;
      statusMap[slug] = app.portal_status || {};
    });

    qsa('.app-card').forEach((card) => {
      const slug = card.dataset.slug;
      const status = statusMap[slug] || {};
      const badgeHost = card.querySelector('.app-card__meta-row');
      if (!badgeHost) return;
      qsa('.badge--installed', badgeHost).forEach((node) => node.remove());
      if ((status.installed_on || []).length) {
        const badge = document.createElement('span');
        badge.className = 'badge badge--success badge--installed';
        badge.textContent = t('installed_on_sites', 'Installed');
        badgeHost.appendChild(badge);
      }
    });
  }

  async function loadPortalState() {
    try {
      state.portal = await callMethod('erpgenex_saas.api.portal.get_applications_portal_state', {});
      renderScenarioCards();
      renderInstalledApps();
      markInstalledCards();
    } catch (err) {
      renderScenarioCards();
    }
  }

  function openModal(title, bodyHtml) {
    const modal = qs('#saas-app-modal');
    if (!modal) return;
    qs('.saas-modal__title', modal).textContent = title;
    qs('.saas-modal__body', modal).innerHTML = bodyHtml;
    modal.hidden = false;
    state.modal = modal;
  }

  function closeModal() {
    const modal = qs('#saas-app-modal');
    if (modal) modal.hidden = true;
    state.modal = null;
  }

  function billingAmount(card, cycle) {
    if (cycle === 'Annual') return parseFloat(card.dataset.annualPrice || 0);
    return parseFloat(card.dataset.price || 0);
  }

  function subscriptionModal(card) {
    const appName = card.dataset.name;
    const tenants = tenantOptions();
    if (!tenants.length) {
      showFeedback(t('need_site', 'Create a site from the dashboard before subscribing.'), 'error');
      return;
    }
    const tenantOptionsHtml = tenants.map((tenant) => `<option value="${tenant.value}">${tenant.label} (${tenant.status})</option>`).join('');
    openModal(t('subscribe_title', 'Subscribe to Application'), `
      <div class="saas-flow">
        <ol class="saas-flow__steps">
          <li>${t('flow_pick_plan', 'Choose Monthly or Annual billing')}</li>
          <li>${t('flow_pay', 'Pay via PayPal on the platform account')}</li>
          <li>${t('flow_key', 'Receive the EGX activation key')}</li>
          <li>${t('flow_install', 'Install the app on your tenant site')}</li>
        </ol>
        <label class="saas-field"><span>${t('tenant', 'Tenant site')}</span>
          <select id="modal-tenant">${tenantOptionsHtml}</select>
        </label>
        <div class="saas-cycle-toggle">
          <button type="button" class="saas-cycle-btn is-active" data-cycle="Monthly">${t('monthly', 'Monthly')} · $${card.dataset.price}</button>
          <button type="button" class="saas-cycle-btn" data-cycle="Annual">${t('annual', 'Annual')} · $${card.dataset.annualPrice}</button>
        </div>
        <p class="saas-modal__hint">${t('paypal_hint', 'Payment is registered against the configured PayPal business account.')}</p>
        <div class="saas-modal__actions">
          <button type="button" class="btn btn--secondary" data-close-modal>${t('cancel', 'Cancel')}</button>
          <button type="button" class="btn btn--primary" id="modal-subscribe-confirm">${t('continue_payment', 'Continue to Payment')}</button>
        </div>
      </div>
    `);

    let selectedCycle = 'Monthly';
    qsa('.saas-cycle-btn', state.modal).forEach((btn) => {
      btn.addEventListener('click', () => {
        qsa('.saas-cycle-btn', state.modal).forEach((node) => node.classList.remove('is-active'));
        btn.classList.add('is-active');
        selectedCycle = btn.dataset.cycle;
      });
    });
    qs('[data-close-modal]', state.modal)?.addEventListener('click', closeModal);
    qs('#modal-subscribe-confirm', state.modal)?.addEventListener('click', async () => {
      const tenant = qs('#modal-tenant', state.modal)?.value;
      const button = qs('#modal-subscribe-confirm', state.modal);
      button.disabled = true;
      button.textContent = t('processing', 'Processing…');
      try {
        const result = await callMethod('erpgenex_saas.api.portal.subscribe_to_application', {
          tenant,
          application: card.dataset.slug,
          billing_cycle: selectedCycle,
        });
        await callMethod('erpgenex_saas.api.portal.register_invoice_payment', {
          invoice: result.invoice,
          provider: 'PayPal',
          transaction_id: 'PP-' + Date.now(),
          amount: result.amount_due || billingAmount(card, selectedCycle),
        });
        await callMethod('erpgenex_saas.api.portal.install_application', {
          tenant,
          application: card.dataset.slug,
        });
        const licenseKey = result.license_key || '';
        openModal(t('subscription_success', 'Subscription Activated'), `
          <div class="saas-success">
            <p>${t('subscription_done', 'Payment recorded, license generated, and installation started.')}</p>
            <div class="license-box">
              <span>${t('activation_key', 'Activation Key')}</span>
              <code id="generated-license-key">${licenseKey || '—'}</code>
              <button type="button" class="btn btn--sm btn--secondary" id="copy-license-key">${t('copy', 'Copy')}</button>
            </div>
            <p class="saas-modal__hint">${t('activation_hint', 'You can also paste this key in ErpGenEx Marketplace on your tenant site.')}</p>
            <button type="button" class="btn btn--primary" data-close-modal>${t('close', 'Close')}</button>
          </div>
        `);
        qs('#copy-license-key', state.modal)?.addEventListener('click', () => {
          navigator.clipboard?.writeText(licenseKey || '');
          showFeedback(t('copied', 'Activation key copied.'), 'success');
        });
        qs('[data-close-modal]', state.modal)?.addEventListener('click', closeModal);
        showFeedback(t('subscription_success_short', 'Subscription completed successfully.'), 'success');
        loadPortalState();
      } catch (err) {
        showFeedback(getReadableError(err) || t('subscription_failed', 'Unable to complete subscription.'), 'error');
        closeModal();
      }
    });
  }

  function sourceModal(card) {
    const tenants = tenantOptions();
    const tenantOptionsHtml = [`<option value="">${t('optional', 'Optional')}</option>`]
      .concat(tenants.map((tenant) => `<option value="${tenant.value}">${tenant.label}</option>`)).join('');
    openModal(t('source_title', 'Buy Source Code'), `
      <div class="saas-flow">
        <ol class="saas-flow__steps">
          <li>${t('source_flow_pay', 'Pay the one-time source-code price')}</li>
          <li>${t('source_flow_license', 'Receive a lifetime EGX license key')}</li>
          <li>${t('source_flow_download', 'Download via the secure link generated for your account')}</li>
        </ol>
        <label class="saas-field"><span>${t('customer_email', 'Customer email')}</span>
          <input type="email" id="modal-source-email" value="${frappe.session?.user || ''}">
        </label>
        <label class="saas-field"><span>${t('tenant', 'Tenant site')}</span>
          <select id="modal-source-tenant">${tenantOptionsHtml}</select>
        </label>
        <p class="saas-price-line">${t('source_price', 'Source price')}: <strong>$${card.dataset.sourcePrice}</strong></p>
        <div class="saas-modal__actions">
          <button type="button" class="btn btn--secondary" data-close-modal>${t('cancel', 'Cancel')}</button>
          <button type="button" class="btn btn--primary" id="modal-source-confirm">${t('buy_source', 'Buy Source Code')}</button>
        </div>
      </div>
    `);
    qs('[data-close-modal]', state.modal)?.addEventListener('click', closeModal);
    qs('#modal-source-confirm', state.modal)?.addEventListener('click', async () => {
      const email = qs('#modal-source-email', state.modal)?.value?.trim();
      const tenant = qs('#modal-source-tenant', state.modal)?.value || null;
      if (!email) {
        showFeedback(t('email_required', 'Customer email is required.'), 'error');
        return;
      }
      const button = qs('#modal-source-confirm', state.modal);
      button.disabled = true;
      button.textContent = t('processing', 'Processing…');
      try {
        const result = await callMethod('erpgenex_saas.api.portal.buy_source_code', {
          application: card.dataset.slug,
          customer_email: email,
          tenant,
        });
        await callMethod('erpgenex_saas.api.portal.register_invoice_payment', {
          invoice: result.invoice,
          provider: 'PayPal',
          transaction_id: 'PP-' + Date.now(),
          amount: result.amount_due || parseFloat(card.dataset.sourcePrice || 0),
        });
        const fulfilled = await callMethod('erpgenex_saas.api.portal.fulfill_source_purchase', {
          source_purchase: result.source_purchase,
          grant_github_access: 0,
        });
        openModal(t('source_success', 'Source Code Purchase Complete'), `
          <div class="saas-success">
            <p>${t('source_done', 'Lifetime license created and download link generated.')}</p>
            ${fulfilled.download_url ? `<p><a href="${fulfilled.download_url}" target="_blank" rel="noopener">${t('download_link', 'Open download link')}</a></p>` : ''}
            <button type="button" class="btn btn--primary" data-close-modal>${t('close', 'Close')}</button>
          </div>
        `);
        qs('[data-close-modal]', state.modal)?.addEventListener('click', closeModal);
        showFeedback(t('source_success_short', 'Source-code purchase completed.'), 'success');
        loadPortalState();
      } catch (err) {
        showFeedback(getReadableError(err) || t('source_failed', 'Unable to complete source-code purchase.'), 'error');
        closeModal();
      }
    });
  }

  function installModal(card) {
    const tenants = tenantOptions();
    if (!tenants.length) {
      showFeedback(t('need_site', 'Create a site from the dashboard before installing.'), 'error');
      return;
    }
    const tenantOptionsHtml = tenants.map((tenant) => `<option value="${tenant.value}">${tenant.label}</option>`).join('');
    openModal(t('install_title', 'Install Application'), `
      <label class="saas-field"><span>${t('tenant', 'Tenant site')}</span>
        <select id="modal-install-tenant">${tenantOptionsHtml}</select>
      </label>
      <div class="saas-modal__actions">
        <button type="button" class="btn btn--secondary" data-close-modal>${t('cancel', 'Cancel')}</button>
        <button type="button" class="btn btn--primary" id="modal-install-confirm">${t('install', 'Install')}</button>
      </div>
    `);
    qs('[data-close-modal]', state.modal)?.addEventListener('click', closeModal);
    qs('#modal-install-confirm', state.modal)?.addEventListener('click', async () => {
      const tenant = qs('#modal-install-tenant', state.modal)?.value;
      await installApplication(tenant, card.dataset.slug);
      closeModal();
    });
  }

  async function installApplication(tenant, application) {
    try {
      await callMethod('erpgenex_saas.api.portal.install_application', { tenant, application });
      showFeedback(t('install_success', 'Application installation started successfully.'), 'success');
      loadPortalState();
    } catch (err) {
      showFeedback(getReadableError(err) || t('install_failed', 'Unable to install application.'), 'error');
    }
  }

  async function revealLicenseKey(tenant, application) {
    try {
      const result = await callMethod('erpgenex_saas.api.portal.reveal_application_license_key', {
        tenant,
        application,
      });
      openModal(t('activation_key', 'Activation Key'), `
        <div class="saas-success">
          <code id="generated-license-key">${result.license_key || '—'}</code>
          <p class="saas-modal__hint">${result.activation_hint || ''}</p>
          <button type="button" class="btn btn--sm btn--secondary" id="copy-license-key">${t('copy', 'Copy')}</button>
          <button type="button" class="btn btn--primary" data-close-modal>${t('close', 'Close')}</button>
        </div>
      `);
      qs('#copy-license-key', state.modal)?.addEventListener('click', () => {
        navigator.clipboard?.writeText(result.license_key || '');
        showFeedback(t('copied', 'Activation key copied.'), 'success');
      });
      qs('[data-close-modal]', state.modal)?.addEventListener('click', closeModal);
    } catch (err) {
      showFeedback(getReadableError(err) || t('key_failed', 'Unable to reveal license key.'), 'error');
    }
  }

  function filterApps() {
    const appCards = qsa('.app-card');
    const emptyState = qs('#empty-state');
    const appGrid = qs('#app-grid');
    let visibleCount = 0;

    appCards.forEach((card) => {
      const cardCategory = card.dataset.category;
      const pricingType = card.dataset.pricingType || 'free';
      const isPaid = pricingType === 'paid';
      const cardName = (card.dataset.name || '').toLowerCase();
      const cardDesc = (card.querySelector('.app-card__desc')?.textContent || '').toLowerCase();
      const categoryMatch = state.currentCategory === 'all' || cardCategory === state.currentCategory;
      let priceMatch = true;
      if (state.currentFilter === 'free') priceMatch = pricingType !== 'paid';
      if (state.currentFilter === 'paid') priceMatch = isPaid;
      const searchMatch = !state.searchTerm || cardName.includes(state.searchTerm) || cardDesc.includes(state.searchTerm);
      if (categoryMatch && priceMatch && searchMatch) {
        card.style.display = 'flex';
        visibleCount += 1;
      } else {
        card.style.display = 'none';
      }
    });

    if (emptyState && appGrid) {
      emptyState.style.display = visibleCount === 0 ? 'block' : 'none';
      appGrid.style.display = visibleCount === 0 ? 'none' : 'grid';
    }
  }

  function bindFilters() {
    qs('#search-input')?.addEventListener('input', (event) => {
      state.searchTerm = event.target.value.toLowerCase();
      filterApps();
    });
    qsa('.filter-chip').forEach((chip) => {
      chip.addEventListener('click', function() {
        qsa('.filter-chip').forEach((node) => node.classList.remove('filter-chip--active'));
        this.classList.add('filter-chip--active');
        state.currentFilter = this.dataset.filter;
        filterApps();
      });
    });
    qsa('.category-btn').forEach((btn) => {
      btn.addEventListener('click', function() {
        qsa('.category-btn').forEach((node) => node.classList.remove('category-btn--active'));
        this.classList.add('category-btn--active');
        state.currentCategory = this.dataset.category;
        filterApps();
      });
    });
  }

  function bindCards() {
    qsa('.app-card').forEach((card) => {
      qsa('[data-action]', card).forEach((button) => {
        button.addEventListener('click', () => {
          const action = button.dataset.action;
          if (action === 'subscribe') subscriptionModal(card);
          if (action === 'source') sourceModal(card);
          if (action === 'install') installModal(card);
        });
      });
    });
  }

  function bindModalShell() {
    qs('[data-close-modal-root]')?.addEventListener('click', closeModal);
    qs('.saas-modal__backdrop')?.addEventListener('click', closeModal);
  }

  document.addEventListener('DOMContentLoaded', () => {
    bindFilters();
    bindCards();
    bindModalShell();
    filterApps();
    loadPortalState();
  });
})();
