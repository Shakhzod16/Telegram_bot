function t(key, fallback, params) {
  if (typeof window.feT === "function") {
    return window.feT(key, fallback, params);
  }
  return fallback;
}

function statusClass(status) {
  const map = {
    pending: "status-pending",
    confirmed: "status-confirmed",
    preparing: "status-preparing",
    on_the_way: "status-on_the_way",
    delivered: "status-delivered",
    cancelled: "status-cancelled",
    ready: "status-ready",
  };
  return map[status] || "status-confirmed";
}

function statusLabel(status) {
  const map = {
    pending: t("status_pending", "Kutilmoqda"),
    confirmed: t("status_confirmed", "Tasdiqlangan"),
    preparing: t("status_preparing", "Tayyorlanmoqda"),
    on_the_way: t("status_on_the_way", "Yo'lda"),
    delivered: t("status_delivered", "Yetkazildi"),
    cancelled: t("status_cancelled", "Bekor qilingan"),
    ready: t("status_ready", "Tayyor"),
  };
  return map[status] || status;
}

function formatMoney(value) {
  return `${Number(value || 0).toLocaleString()} UZS`;
}

function formatDate(value) {
  if (!value) return "-";
  const lang = typeof window.getAppLanguage === "function" ? window.getAppLanguage() : "uz";
  const locale = lang === "ru" ? "ru-RU" : lang === "en" ? "en-US" : "uz-UZ";
  try {
    return new Date(value).toLocaleString(locale, {
      day: "2-digit",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch (_) {
    return value;
  }
}

function orderItemsPreview(items) {
  return (items || [])
    .slice(0, 3)
    .map(function (it) {
      const snap = it.snapshot_json || {};
      const name = snap.product_name || t("order_product_unknown", "Mahsulot #{id}", { id: it.product_id });
      return `${name} x${it.quantity}`;
    })
    .join(", ");
}

async function loadOrdersList() {
  const loading = document.getElementById("state-loading");
  const empty = document.getElementById("state-empty");
  const root = document.getElementById("orders-root");

  try {
    await (window.appLangReady || Promise.resolve());
    const data = await window.apiFetch("/api/v1/orders?page=1&size=50");

    if (loading) loading.classList.add("hidden");
    if (!root) return;
    root.innerHTML = "";

    const items = data.items || [];
    if (items.length === 0) {
      if (empty) empty.classList.remove("hidden");
      return;
    }

    if (empty) empty.classList.add("hidden");
    root.classList.remove("hidden");

    items.forEach(function (o) {
      const card = document.createElement("a");
      card.href = `/webapp/orders/${o.id}`;
      card.className = "order-card";
      card.innerHTML =
        `<div class="order-card-header">` +
        `<div>` +
        `<div class="order-id">#${o.id}</div>` +
        `<div class="order-date">${formatDate(o.created_at)}</div>` +
        `</div>` +
        `<span class="status-badge ${statusClass(o.status)}">${statusLabel(o.status)}</span>` +
        `</div>` +
        `<div class="order-items-preview">${orderItemsPreview(o.items)}</div>` +
        `<div class="order-footer">` +
        `<span class="order-total">${formatMoney(o.total_amount)}</span>` +
        `<span class="menu-chevron">›</span>` +
        `</div>`;
      root.appendChild(card);
    });

    animateList(document.querySelectorAll(".order-card"), 60);
  } catch (_) {
    if (loading) loading.classList.add("hidden");
    if (empty) empty.classList.remove("hidden");
  }
}

function renderOrderItems(items) {
  if (!items || items.length === 0) {
    return `<div class="empty-desc">${t("order_products_not_found", "Mahsulotlar topilmadi")}</div>`;
  }

  return items
    .map(function (it) {
      const snap = it.snapshot_json || {};
      const name = snap.product_name || t("order_product_unknown", "Mahsulot #{id}", { id: it.product_id });
      const variant = snap.variant_name ? `<div class="cart-item-variant">${snap.variant_name}</div>` : "";
      return (
        `<article class="cart-item">` +
        `<div class="cart-item-info">` +
        `<div class="cart-item-name">${name}</div>` +
        `${variant}` +
        `<div class="cart-item-bottom">` +
        `<span class="cart-item-variant">${t("order_qty_unit", "{qty} ta", { qty: it.quantity })}</span>` +
        `<span class="cart-item-price">${formatMoney(it.total_price)}</span>` +
        `</div>` +
        `</div>` +
        `</article>`
      );
    })
    .join("");
}

async function loadOrderDetail() {
  const id = window.ORDER_ID;
  if (!id) return;

  const loading = document.getElementById("state-loading");
  const root = document.getElementById("order-root");

  try {
    await (window.appLangReady || Promise.resolve());
    const o = await window.apiFetch(`/api/v1/orders/${id}`);
    if (loading) loading.classList.add("hidden");
    if (!root) return;
    root.classList.remove("hidden");

    root.innerHTML =
      `<div class="order-card">` +
      `<div class="order-card-header">` +
      `<div><div class="order-id">#${o.id}</div><div class="order-date">${formatDate(o.created_at)}</div></div>` +
      `<span class="status-badge ${statusClass(o.status)}">${statusLabel(o.status)}</span>` +
      `</div>` +
      `<div class="divider"></div>` +
      `<div class="price-row"><span>${t("subtotal", "Subtotal")}</span><span class="price-value">${formatMoney(o.subtotal)}</span></div>` +
      `<div class="price-row"><span>${t("delivery", "Yetkazish")}</span><span class="price-value">${formatMoney(o.delivery_fee)}</span></div>` +
      `<div class="price-row discount"><span>${t("discount", "Chegirma")}</span><span class="price-value">-${formatMoney(o.discount)}</span></div>` +
      `<div class="price-row total"><span>${t("total", "Jami")}</span><span class="price-value">${formatMoney(o.total_amount)}</span></div>` +
      `</div>` +
      `<div class="simple-card" style="margin-top:12px;">` +
      `<div class="profile-section-title" style="padding-left:0;">${t("order_items_section", "Mahsulotlar")}</div>` +
      `${renderOrderItems(o.items)}` +
      `</div>` +
      `<div class="profile-section" style="padding:12px 0 0;">` +
      `<button class="btn btn-secondary" id="repeat-btn" type="button">${t("order_repeat", "Qayta buyurtma")}</button>` +
      `</div>`;

    const repeatBtn = document.getElementById("repeat-btn");
    if (repeatBtn) {
      repeatBtn.addEventListener("click", async function () {
        repeatBtn.classList.add("loading");
        try {
          await window.apiFetch(`/api/v1/orders/${id}/repeat`, { method: "POST" });
          hapticOk();
          showToast(t("order_repeat_ok", "Savatga qayta qo'shildi"), "success");
          setTimeout(function () {
            window.location.href = "/webapp/cart";
          }, 260);
        } catch (_) {
          repeatBtn.classList.remove("loading");
          hapticErr();
          showToast(t("order_repeat_fail", "Qayta buyurtma amalga oshmadi"), "error");
        }
      });
    }
  } catch (_) {
    if (loading) loading.classList.add("hidden");
    if (root) {
      root.classList.remove("hidden");
      root.innerHTML = `<div class="empty-state"><div class="empty-title">${t("order_not_found", "Buyurtma topilmadi")}</div></div>`;
    }
  }
}

if (window.ORDER_ID) {
  loadOrderDetail();
} else {
  loadOrdersList();
}
