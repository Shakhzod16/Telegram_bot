function formatMoney(value) {
  return `${Number(value || 0).toLocaleString()} UZS`;
}

const DELIVERY_LOCATION_KEY = "delivery_location";
let selectedLocation = null;

function t(key, fallback, params) {
  if (typeof window.feT === "function") {
    return window.feT(key, fallback, params);
  }
  return fallback;
}

function parseDeliveryLocation(raw) {
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw);
    const lat = Number(parsed.lat);
    const lng = Number(parsed.lng);
    if (!Number.isFinite(lat) || !Number.isFinite(lng)) return null;
    return {
      lat: lat,
      lng: lng,
      address: String(parsed.address || "").trim(),
    };
  } catch (_) {
    return null;
  }
}

function getStoredDeliveryLocation() {
  const location = parseDeliveryLocation(sessionStorage.getItem(DELIVERY_LOCATION_KEY));
  if (!location) {
    sessionStorage.removeItem(DELIVERY_LOCATION_KEY);
    return null;
  }
  return location;
}

function renderSelectedLocation() {
  const target = document.getElementById("selected-address");
  if (!target) return;

  selectedLocation = getStoredDeliveryLocation();
  if (!selectedLocation) {
    target.textContent = t("checkout_location_missing", "Manzil hali belgilanmagan");
    return;
  }

  const fallback = `${selectedLocation.lat.toFixed(6)}, ${selectedLocation.lng.toFixed(6)}`;
  const text = selectedLocation.address || fallback;
  target.textContent = `PIN: ${text}`;
}

function renderSummary(preview) {
  const root = document.getElementById("checkout-summary");
  if (!root) return;

  root.innerHTML =
    `<div class="price-row"><span>${t("subtotal", "Subtotal")}</span><span class="price-value">${formatMoney(preview.subtotal)}</span></div>` +
    `<div class="price-row"><span>${t("delivery", "Yetkazish")}</span><span class="price-value">${formatMoney(preview.delivery_fee)}</span></div>` +
    `<div class="price-row discount"><span>${t("discount", "Chegirma")}</span><span class="price-value">-${formatMoney(preview.discount)}</span></div>` +
    `<div class="price-row total"><span>${t("total", "Jami")}</span><span class="price-value">${formatMoney(preview.total)}</span></div>`;
}

async function loadPreview() {
  try {
    const cart = await window.apiFetch("/api/v1/cart");
    const subtotal = Number((cart && cart.subtotal) || 0);
    renderSummary({
      subtotal: subtotal,
      delivery_fee: 0,
      discount: 0,
      total: subtotal,
    });
  } catch (e) {
    renderSummary({ subtotal: 0, delivery_fee: 0, discount: 0, total: 0 });
  }
}

async function loadCheckout() {
  const loading = document.getElementById("state-loading");
  const root = document.getElementById("checkout-root");

  await (window.appLangReady || Promise.resolve());
  renderSelectedLocation();
  await loadPreview();

  if (loading) loading.classList.add("hidden");
  if (root) root.classList.remove("hidden");
}

function buildMapsUrl(latitude, longitude) {
  if (typeof latitude !== "number" || typeof longitude !== "number") {
    return null;
  }
  return `https://maps.google.com/?q=${latitude},${longitude}`;
}

async function submitOrder() {
  const submitBtn = document.getElementById("checkout-submit");
  if (submitBtn) submitBtn.classList.add("loading");

  try {
    const location = getStoredDeliveryLocation();
    const manualAddress = String(document.getElementById("checkout-address-text")?.value || "").trim();
    const resolvedAddressText = manualAddress || (location ? location.address : "");
    const latitude = location ? location.lat : null;
    const longitude = location ? location.lng : null;
    const mapsUrl = buildMapsUrl(latitude, longitude);

    if (latitude === null || longitude === null) {
      if (!resolvedAddressText) {
        hapticErr();
        showToast(t("toast_select_location", "Xaritada manzil belgilang yoki qo'lda manzil kiriting."), "error");
        return;
      }
      showToast(t("toast_location_without_coords", "Lokatsiyasiz buyurtma yuborildi. Kuryer bilan aniqlashtiriladi."), "info");
    }

    const idem = `idem-${Date.now()}`;
    await window.apiFetch("/api/v1/orders", {
      method: "POST",
      body: JSON.stringify({
        address_text: resolvedAddressText || null,
        comment: document.getElementById("checkout-comment")?.value || null,
        promo_code: null,
        idempotency_key: idem,
        latitude: latitude,
        longitude: longitude,
        maps_url: mapsUrl,
      }),
    });

    const root = document.getElementById("checkout-root");
    const success = document.getElementById("checkout-success");
    if (root) root.classList.add("hidden");
    if (success) success.classList.remove("hidden");

    updateCartBadge(0);
    hapticOk();
    showToast(t("checkout_success_title", "Buyurtma qabul qilindi"), "success");
  } catch (e) {
    hapticErr();
    showToast((e && e.message) || t("toast_order_failed", "Buyurtma yuborilmadi"), "error");
  } finally {
    if (submitBtn) submitBtn.classList.remove("loading");
  }
}

const submitBtn = document.getElementById("checkout-submit");
if (submitBtn) {
  submitBtn.addEventListener("click", submitOrder);
}

window.addEventListener("pageshow", function () {
  renderSelectedLocation();
});

loadCheckout();
