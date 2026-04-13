const tg = window.Telegram?.WebApp ?? {
  initData: "",
  initDataUnsafe: {},
  themeParams: {},
  ready() {},
  expand() {},
  showAlert(message) {
    window.alert(message);
  },
  showPopup(options, cb) {
    const value = window.prompt(options.message || "");
    cb?.(value ? "ok" : "cancel");
  },
  sendData(data) {
    console.log("sendData fallback", data);
  },
  openLink(url) {
    window.open(url, "_blank", "noopener,noreferrer");
  },
  requestLocation() {},
  onEvent() {},
};

tg.ready();
tg.expand();

const API_BASE_URL = window.APP_CONFIG?.apiBaseUrl || window.location.origin;
const CART_STORAGE_KEY = "foodflow_cart_v1";

const CATEGORY_ORDER = [
  { key: "burger", textKey: "frontend_category_burger", fallback: "Burgers" },
  { key: "lavash", textKey: "frontend_category_lavash", fallback: "Lavash" },
  { key: "drinks", textKey: "frontend_category_drinks", fallback: "Drinks" },
  { key: "combo", textKey: "frontend_category_combo", fallback: "Combo" },
];

const state = {
  user: null,
  products: [],
  texts: {},
  savedAddresses: [],
  cart: {
    items: {},
    total: 0,
  },
  location: {
    label: "",
    latitude: null,
    longitude: null,
  },
  selectedAddressId: null,
  language: "en",
  orderId: null,
  selectedCategory: "burger",
  paymentMethod: "click",
  loading: true,
};

const els = {
  appTitle: document.getElementById("app-title"),
  userGreeting: document.getElementById("user-greeting"),
  locationTrigger: document.getElementById("location-trigger"),
  locationPanel: document.getElementById("location-panel"),
  requestLocation: document.getElementById("request-location"),
  locationInput: document.getElementById("location-input"),
  saveAddress: document.getElementById("save-address"),
  savedAddresses: document.getElementById("saved-addresses"),
  categoryTabs: document.getElementById("category-tabs"),
  productsGrid: document.getElementById("products-grid"),
  floatingCart: document.getElementById("floating-cart"),
  cartDrawer: document.getElementById("cart-drawer"),
  drawerBackdrop: document.getElementById("drawer-backdrop"),
  closeDrawer: document.getElementById("close-drawer"),
  cartTitle: document.getElementById("cart-title"),
  cartItems: document.getElementById("cart-items"),
  cartTotal: document.getElementById("cart-total"),
  checkoutBtn: document.getElementById("checkout-btn"),
  paymentActions: document.getElementById("payment-actions"),
};

const productTpl = document.getElementById("product-card-template");
const cartItemTpl = document.getElementById("cart-item-template");

function debounce(fn, waitMs = 250) {
  let timer = null;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), waitMs);
  };
}

function applyTheme() {
  const p = tg.themeParams || {};
  const root = document.documentElement.style;
  if (p.bg_color) root.setProperty("--bg", p.bg_color);
  if (p.secondary_bg_color) root.setProperty("--surface", p.secondary_bg_color);
  if (p.text_color) root.setProperty("--text", p.text_color);
  if (p.hint_color) root.setProperty("--muted", p.hint_color);
  if (p.button_color) root.setProperty("--accent", p.button_color);
}

function showToast(message) {
  tg.showAlert(message);
}

function text(key, fallback) {
  return state.texts[key] || fallback;
}

function formatAmount(value) {
  return `${Number(value || 0).toLocaleString("ru-RU")} so'm`;
}

function apiUrl(path) {
  return `${API_BASE_URL}${path}`;
}

function initDataHeader() {
  return tg.initData ? { "X-Init-Data": tg.initData } : {};
}

function categoryForProduct(product) {
  if (product.category === "pizza") return "combo";
  return product.category;
}

function productById(productId) {
  return state.products.find((p) => p.id === Number(productId));
}

function recalcCartTotal() {
  state.cart.total = Object.entries(state.cart.items).reduce((sum, [id, qty]) => {
    const product = productById(id);
    return product ? sum + product.price * Number(qty) : sum;
  }, 0);
}

function saveCart() {
  localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(state.cart.items));
}

function loadCart() {
  try {
    const raw = localStorage.getItem(CART_STORAGE_KEY);
    if (!raw) return;
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed === "object") {
      state.cart.items = parsed;
    }
  } catch (_error) {}
}

function cartEntries() {
  return Object.entries(state.cart.items)
    .map(([id, quantity]) => {
      const product = productById(id);
      if (!product) return null;
      return {
        product,
        quantity: Number(quantity),
        lineTotal: product.price * Number(quantity),
      };
    })
    .filter(Boolean);
}

function renderSkeletons() {
  els.productsGrid.innerHTML = "";
  for (let i = 0; i < 6; i += 1) {
    const sk = document.createElement("div");
    sk.className = "skeleton";
    els.productsGrid.appendChild(sk);
  }
}

function renderHeader() {
  els.appTitle.textContent = text("frontend_title", "FoodFlow");
  const firstName = state.user?.first_name || state.user?.name || text("frontend_guest", "Guest");
  els.userGreeting.textContent = text("frontend_hello_name", "Hello, {name}").replace("{name}", firstName);
  els.locationTrigger.textContent = state.location.label || text("frontend_detect_location", "Location");
  els.cartTitle.textContent = text("frontend_cart", "Cart");
  els.checkoutBtn.textContent = text("frontend_order", "Checkout");
  if (els.requestLocation) {
    els.requestLocation.textContent = text("frontend_use_telegram_location", "Use Telegram location");
  }
  if (els.locationInput) {
    els.locationInput.placeholder = text("frontend_enter_address", "Enter delivery address");
  }
  if (els.saveAddress) {
    els.saveAddress.textContent = text("frontend_save_address", "Save address");
  }
}

function renderPaymentMethodSelector() {
  const buttons = [...els.paymentActions.querySelectorAll("[data-provider]")];
  buttons.forEach((btn) => {
    if (btn.dataset.provider === state.paymentMethod) {
      btn.classList.add("active");
    } else {
      btn.classList.remove("active");
    }
  });
}

function applySavedAddress(address) {
  if (!address) return;
  state.selectedAddressId = Number(address.id);
  setLocationLabel(
    address.address_text || address.label || "",
    address.latitude ?? null,
    address.longitude ?? null
  );
}

function renderSavedAddresses() {
  if (!els.savedAddresses) return;
  els.savedAddresses.innerHTML = "";
  if (!state.savedAddresses.length) {
    const empty = document.createElement("p");
    empty.className = "muted";
    empty.textContent = text("frontend_addresses_empty", "No saved addresses yet.");
    els.savedAddresses.appendChild(empty);
    return;
  }

  state.savedAddresses.forEach((address) => {
    const card = document.createElement("article");
    card.className = "saved-address";
    const title = address.label || text("frontend_address_label_default", "Address");
    const body = address.address_text || address.label || "";
    const isDefault = Boolean(address.is_default);
    const defaultBadge = isDefault ? ` (${text("frontend_default_badge", "Default")})` : "";
    card.innerHTML = `
      <div class="saved-address-header">
        <span class="saved-address-label">${title}${defaultBadge}</span>
      </div>
      <p class="muted">${body}</p>
      <div class="saved-address-actions">
        <button class="chip" type="button" data-address-action="use" data-address-id="${address.id}">
          ${text("frontend_use_address", "Use")}
        </button>
        <button class="chip" type="button" data-address-action="default" data-address-id="${address.id}">
          ${text("frontend_set_default", "Set default")}
        </button>
        <button class="chip" type="button" data-address-action="delete" data-address-id="${address.id}">
          ${text("frontend_delete_address", "Delete")}
        </button>
      </div>
    `;
    els.savedAddresses.appendChild(card);
  });
}

function renderCategories() {
  els.categoryTabs.innerHTML = "";
  CATEGORY_ORDER.forEach((cat) => {
    const btn = document.createElement("button");
    btn.className = `chip ${state.selectedCategory === cat.key ? "active" : ""}`;
    btn.type = "button";
    btn.textContent = text(cat.textKey, cat.fallback);
    btn.addEventListener("click", () => {
      state.selectedCategory = cat.key;
      renderCategories();
      renderProducts();
    });
    els.categoryTabs.appendChild(btn);
  });
}

function renderProducts() {
  els.productsGrid.innerHTML = "";
  const filtered = state.products.filter((item) => categoryForProduct(item) === state.selectedCategory);
  if (!filtered.length) {
    const empty = document.createElement("p");
    empty.className = "muted";
    empty.textContent = text("frontend_empty_category", "No items in this category yet.");
    els.productsGrid.appendChild(empty);
    return;
  }

  filtered.forEach((product) => {
    const node = productTpl.content.firstElementChild.cloneNode(true);
    const qty = Number(state.cart.items[product.id] || 0);
    node.querySelector(".product-image").src = product.image_url;
    node.querySelector(".product-image").alt = product.name;
    node.querySelector(".product-name").textContent = product.name;
    node.querySelector(".product-description").textContent = product.description;
    node.querySelector(".product-price").textContent = formatAmount(product.price);
    node.querySelector(".qty").textContent = String(qty);

    const bump = () => {
      node.classList.add("bump");
      setTimeout(() => node.classList.remove("bump"), 180);
    };

    node.querySelector(".add-btn").addEventListener("click", () => {
      updateQuantity(product.id, 1);
      bump();
    });
    node.querySelector(".plus").addEventListener("click", () => {
      updateQuantity(product.id, 1);
      bump();
    });
    node.querySelector(".minus").addEventListener("click", () => updateQuantity(product.id, -1));

    els.productsGrid.appendChild(node);
  });
}

function renderCartButton() {
  const count = cartEntries().reduce((sum, row) => sum + row.quantity, 0);
  if (!count) {
    els.floatingCart.classList.add("hidden");
    return;
  }
  els.floatingCart.classList.remove("hidden");
  els.floatingCart.textContent = `${count} ${text("frontend_items_short", "items")} | ${formatAmount(state.cart.total)}`;
}

function renderCart() {
  els.cartItems.innerHTML = "";
  const items = cartEntries();
  if (!items.length) {
    const empty = document.createElement("p");
    empty.className = "muted";
    empty.textContent = text("frontend_empty", "Cart is empty.");
    els.cartItems.appendChild(empty);
    els.checkoutBtn.disabled = true;
    els.paymentActions.classList.add("hidden");
  } else {
    els.checkoutBtn.disabled = false;
    els.paymentActions.classList.remove("hidden");
    items.forEach((item) => {
      const node = cartItemTpl.content.firstElementChild.cloneNode(true);
      node.querySelector(".cart-item-name").textContent = item.product.name;
      node.querySelector(".cart-item-meta").textContent = `${item.quantity} x ${formatAmount(item.product.price)}`;
      node.querySelector(".qty").textContent = String(item.quantity);
      node.querySelector(".plus").addEventListener("click", () => updateQuantity(item.product.id, 1));
      node.querySelector(".minus").addEventListener("click", () => updateQuantity(item.product.id, -1));
      els.cartItems.appendChild(node);
    });
  }
  els.cartTotal.textContent = formatAmount(state.cart.total);
  renderPaymentMethodSelector();
  renderCartButton();
}

function renderAll() {
  renderHeader();
  renderSavedAddresses();
  renderCategories();
  renderProducts();
  renderCart();
}

function updateQuantity(productId, delta) {
  const current = Number(state.cart.items[productId] || 0);
  const next = Math.max(0, Math.min(99, current + delta));
  if (next === 0) {
    delete state.cart.items[productId];
  } else {
    state.cart.items[productId] = next;
  }
  recalcCartTotal();
  saveCart();
  renderProducts();
  renderCart();
}

async function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function requestWithRetry(path, options = {}, retries = 2) {
  let lastError = null;
  for (let attempt = 0; attempt <= retries; attempt += 1) {
    try {
      const response = await fetch(apiUrl(path), {
        ...options,
        headers: {
          "Content-Type": "application/json",
          ...initDataHeader(),
          ...(options.headers || {}),
        },
      });
      if (!response.ok) {
        let detail = "Request failed";
        try {
          const parsed = await response.json();
          detail = parsed.detail || parsed.error_note || detail;
        } catch (_error) {}
        throw new Error(detail);
      }
      const contentType = response.headers.get("content-type") || "";
      return contentType.includes("application/json") ? response.json() : null;
    } catch (error) {
      lastError = error;
      if (attempt < retries) await sleep(200 * (attempt + 1));
    }
  }
  throw lastError;
}

function buildOrderPayload() {
  return {
    user_id: state.user.user_id || state.user.id,
    items: cartEntries().map((row) => ({
      product_id: row.product.id,
      quantity: row.quantity,
    })),
    location: state.location.label
      ? {
          label: state.location.label,
          address_text: state.location.label,
          latitude: state.location.latitude,
          longitude: state.location.longitude,
        }
      : null,
    payment_method: state.paymentMethod,
  };
}

async function refreshSavedAddresses() {
  const rows = await requestWithRetry("/api/addresses", { method: "GET" });
  state.savedAddresses = Array.isArray(rows) ? rows : [];
  if (!state.location.label) {
    const preferred = state.savedAddresses.find((item) => item.is_default) || state.savedAddresses[0];
    if (preferred) {
      applySavedAddress(preferred);
    }
  }
  renderSavedAddresses();
}

async function saveCurrentAddress() {
  const current = (state.location.label || "").trim();
  if (!current) {
    showToast(text("frontend_address_required", "Enter location first."));
    return;
  }

  const suggested = current.split(",")[0].trim().slice(0, 60) || text("frontend_address_label_default", "Address");
  const label = window.prompt(text("frontend_address_label_prompt", "Address label"), suggested);
  if (label === null) return;
  const normalized = (label || "").trim() || suggested;

  await requestWithRetry("/api/addresses", {
    method: "POST",
    body: JSON.stringify({
      label: normalized,
      address_text: current,
      latitude: state.location.latitude,
      longitude: state.location.longitude,
    }),
  });
  await refreshSavedAddresses();
  showToast(text("frontend_address_saved", "Address saved."));
}

async function handleSavedAddressAction(action, addressId) {
  if (!Number.isFinite(addressId) || addressId <= 0) return;
  if (action === "use") {
    const row = state.savedAddresses.find((item) => Number(item.id) === addressId);
    if (row) {
      applySavedAddress(row);
      renderSavedAddresses();
    }
    return;
  }
  if (action === "default") {
    const updated = await requestWithRetry(`/api/addresses/${addressId}/default`, { method: "PATCH" });
    state.savedAddresses = state.savedAddresses.map((item) => ({
      ...item,
      is_default: Number(item.id) === Number(updated.id),
    }));
    applySavedAddress(updated);
    renderSavedAddresses();
    showToast(text("frontend_address_default_set", "Default address updated."));
    return;
  }
  if (action === "delete") {
    await requestWithRetry(`/api/addresses/${addressId}`, { method: "DELETE" });
    state.savedAddresses = state.savedAddresses.filter((item) => Number(item.id) !== addressId);
    if (state.selectedAddressId === addressId) {
      state.selectedAddressId = null;
    }
    if (!state.savedAddresses.some((item) => item.is_default) && state.savedAddresses.length) {
      const first = state.savedAddresses[0];
      await requestWithRetry(`/api/addresses/${first.id}/default`, { method: "PATCH" });
      state.savedAddresses = state.savedAddresses.map((item) => ({
        ...item,
        is_default: Number(item.id) === Number(first.id),
      }));
    }
    renderSavedAddresses();
    showToast(text("frontend_address_deleted", "Address deleted."));
  }
}

function reorderOrderIdFromUrl() {
  const params = new URLSearchParams(window.location.search);
  const raw = params.get("reorder_order_id");
  const parsed = Number(raw || 0);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
}

async function applyReorderFromUrl() {
  const orderId = reorderOrderIdFromUrl();
  if (!orderId) return;

  const data = await requestWithRetry(`/api/orders/${orderId}/reorder`, { method: "POST" });
  const items = Array.isArray(data.items) ? data.items : [];
  if (!items.length) {
    showToast(text("frontend_reorder_empty", "This order has no available items anymore."));
    return;
  }

  state.cart.items = {};
  items.forEach((row) => {
    const productId = Number(row.product_id);
    const quantity = Number(row.quantity);
    if (!Number.isFinite(productId) || !Number.isFinite(quantity) || quantity <= 0) return;
    state.cart.items[productId] = quantity;
  });
  recalcCartTotal();
  saveCart();
  renderAll();

  const skipped = Number(data.skipped_count || 0);
  if (skipped > 0) {
    showToast(text("frontend_reorder_partial", "Some unavailable products were skipped."));
  } else {
    showToast(text("frontend_reorder_applied", "Cart restored from your previous order."));
  }
}

async function bootstrap() {
  if (!tg.initData) {
    showToast(text("frontend_open_in_telegram", "Open this WebApp in Telegram."));
    return;
  }
  state.loading = true;
  renderSkeletons();
  const data = await requestWithRetry("/api/bootstrap", {
    method: "POST",
    body: JSON.stringify({}),
  });
  state.user = data.user;
  state.products = data.products || [];
  state.texts = data.texts || {};
  state.savedAddresses = data.saved_addresses || [];
  state.language = state.user?.language || "en";
  if (!state.location.label && state.savedAddresses.length) {
    const preferred = state.savedAddresses.find((item) => item.is_default) || state.savedAddresses[0];
    if (preferred) {
      applySavedAddress(preferred);
    }
  }
  recalcCartTotal();
  state.loading = false;
  renderAll();
  await applyReorderFromUrl();
}

function openDrawer() {
  els.cartDrawer.classList.remove("hidden");
}

function closeDrawer() {
  els.cartDrawer.classList.add("hidden");
}

async function checkout() {
  if (!cartEntries().length) {
    showToast(text("frontend_empty", "Cart is empty."));
    return;
  }
  const result = await requestWithRetry("/api/order", {
    method: "POST",
    body: JSON.stringify(buildOrderPayload()),
  });
  state.orderId = result.order_id;
  tg.sendData(JSON.stringify({ type: "order_created", order_id: state.orderId }));
  await createPayment(state.paymentMethod);
  showToast(text("frontend_payment_ready", "Payment flow started."));
}

async function createPayment(provider) {
  if (!state.orderId) {
    showToast(text("frontend_order_first", "Create order first."));
    return;
  }
  const payment = await requestWithRetry("/api/payments/create", {
    method: "POST",
    body: JSON.stringify({
      order_id: state.orderId,
      provider,
    }),
  });
  if (payment?.payment_url) {
    tg.openLink(payment.payment_url);
    return;
  }
  if (provider === "cash") {
    showToast(text("frontend_cash_selected", "Cash payment selected. Please pay on delivery."));
    state.cart.items = {};
    recalcCartTotal();
    saveCart();
    renderAll();
  }
}

function setLocationLabel(label, latitude = null, longitude = null) {
  state.location = { label, latitude, longitude };
  renderHeader();
}

function requestLocationViaTelegram() {
  let fallbackTimer = null;
  const fallbackGeo = () => {
    if (!navigator.geolocation) {
      showToast(text("frontend_location_unavailable", "Geolocation unavailable."));
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLocationLabel(
          `${pos.coords.latitude.toFixed(5)}, ${pos.coords.longitude.toFixed(5)}`,
          pos.coords.latitude,
          pos.coords.longitude
        );
      },
      () => showToast(text("frontend_location_denied", "Location permission denied.")),
      { enableHighAccuracy: true, timeout: 12000, maximumAge: 0 }
    );
  };
  try {
    tg.requestLocation();
    showToast(text("frontend_location_request_sent", "Location request sent to Telegram."));
    fallbackTimer = setTimeout(fallbackGeo, 4000);
  } catch (_error) {
    fallbackGeo();
  }
  return () => clearTimeout(fallbackTimer);
}

const debouncedManualLocation = debounce(() => {
  const value = els.locationInput.value.trim();
  if (value) setLocationLabel(value);
}, 350);

els.locationTrigger.addEventListener("click", () => {
  els.locationPanel.classList.toggle("hidden");
});
els.requestLocation.addEventListener("click", requestLocationViaTelegram);
els.locationInput.addEventListener("input", debouncedManualLocation);
if (els.saveAddress) {
  els.saveAddress.addEventListener("click", () => {
    saveCurrentAddress().catch((e) => showToast(e.message));
  });
}
if (els.savedAddresses) {
  els.savedAddresses.addEventListener("click", (event) => {
    const btn = event.target.closest("[data-address-action]");
    if (!btn) return;
    const action = btn.dataset.addressAction;
    const addressId = Number(btn.dataset.addressId || 0);
    handleSavedAddressAction(action, addressId).catch((e) => showToast(e.message));
  });
}
els.floatingCart.addEventListener("click", openDrawer);
els.drawerBackdrop.addEventListener("click", closeDrawer);
els.closeDrawer.addEventListener("click", closeDrawer);
els.checkoutBtn.addEventListener("click", () => checkout().catch((e) => showToast(e.message)));
els.paymentActions.addEventListener("click", (event) => {
  const btn = event.target.closest("[data-provider]");
  if (!btn) return;
  state.paymentMethod = btn.dataset.provider;
  renderPaymentMethodSelector();
});

tg.onEvent("location_requested", (payload) => {
  const lat = Number(payload?.latitude);
  const lon = Number(payload?.longitude);
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) return;
  setLocationLabel(`${lat.toFixed(5)}, ${lon.toFixed(5)}`, lat, lon);
});

loadCart();
applyTheme();
bootstrap().catch((error) => showToast(error.message || text("frontend_bootstrap_failed", "Bootstrap failed")));

