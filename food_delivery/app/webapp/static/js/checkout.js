function formatMoney(value) {
  return `${Number(value || 0).toLocaleString()} UZS`;
}

let selectedAddressId = null;

function pickAddress(addresses) {
  if (!addresses || addresses.length === 0) return null;

  const saved = Number(sessionStorage.getItem("last_address_id") || 0);
  const fromSaved = addresses.find(function (a) {
    return a.id === saved;
  });
  if (fromSaved) return fromSaved;

  const fromDefault = addresses.find(function (a) {
    return !!a.is_default;
  });
  return fromDefault || addresses[0];
}

async function renderAddress() {
  const target = document.getElementById("selected-address");
  if (!target) return null;

  try {
    const addresses = await window.apiFetch("/api/v1/addresses");
    const selected = pickAddress(addresses || []);

    if (!selected) {
      target.textContent = "Manzil topilmadi. Davom etish uchun manzil qo'shing.";
      return null;
    }

    selectedAddressId = selected.id;
    sessionStorage.setItem("last_address_id", String(selected.id));
    target.textContent = `${selected.title || "Manzil"}: ${selected.address_line}`;
    return selected.id;
  } catch (e) {
    target.textContent = "Manzilni yuklashda xatolik.";
    return null;
  }
}

function renderSummary(preview) {
  const root = document.getElementById("checkout-summary");
  if (!root) return;

  root.innerHTML =
    `<div class="price-row"><span>Subtotal</span><span class="price-value">${formatMoney(preview.subtotal)}</span></div>` +
    `<div class="price-row"><span>Yetkazish</span><span class="price-value">${formatMoney(preview.delivery_fee)}</span></div>` +
    `<div class="price-row discount"><span>Chegirma</span><span class="price-value">-${formatMoney(preview.discount)}</span></div>` +
    `<div class="price-row total"><span>Jami</span><span class="price-value">${formatMoney(preview.total)}</span></div>`;
}

async function loadPreview(addressId) {
  const fallback = {
    subtotal: 0,
    delivery_fee: 0,
    discount: 0,
    total: 0,
  };

  if (!addressId) {
    renderSummary(fallback);
    return;
  }

  try {
    const preview = await window.apiFetch("/api/v1/checkout/preview", {
      method: "POST",
      body: JSON.stringify({ address_id: addressId, promo_code: null }),
    });
    renderSummary(preview);
  } catch (e) {
    try {
      const cart = await window.apiFetch("/api/v1/cart");
      fallback.subtotal = Number(cart.subtotal || 0);
      fallback.total = fallback.subtotal;
      renderSummary(fallback);
    } catch (err) {
      renderSummary(fallback);
    }
  }
}

async function loadCheckout() {
  const loading = document.getElementById("state-loading");
  const root = document.getElementById("checkout-root");

  const addressId = await renderAddress();
  await loadPreview(addressId);

  if (loading) loading.classList.add("hidden");
  if (root) root.classList.remove("hidden");
}

const submitBtn = document.getElementById("checkout-submit");
if (submitBtn) {
  submitBtn.addEventListener("click", async function () {
    const btn = this;
    btn.classList.add("loading");

    try {
      if (!selectedAddressId) {
        hapticErr();
        showToast("Avval manzil tanlang", "error");
        btn.classList.remove("loading");
        return;
      }

      const idem = `idem-${Date.now()}`;
      await window.apiFetch("/api/v1/orders", {
        method: "POST",
        body: JSON.stringify({
          address_id: selectedAddressId,
          comment: document.getElementById("checkout-comment").value || null,
          promo_code: null,
          idempotency_key: idem,
        }),
      });

      const root = document.getElementById("checkout-root");
      const success = document.getElementById("checkout-success");
      if (root) root.classList.add("hidden");
      if (success) success.classList.remove("hidden");

      updateCartBadge(0);
      hapticOk();
      showToast("Buyurtma qabul qilindi!", "success");
    } catch (e) {
      btn.classList.remove("loading");
      hapticErr();
      showToast("Buyurtma yuborilmadi", "error");
    }
  });
}

loadCheckout();
