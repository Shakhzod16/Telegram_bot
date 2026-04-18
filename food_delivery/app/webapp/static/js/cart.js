function t(key, fallback, params) {
  if (typeof window.feT === "function") {
    return window.feT(key, fallback, params);
  }
  return fallback;
}

function formatMoney(value) {
  const n = Number(value || 0);
  return `${n.toLocaleString()} UZS`;
}

function cartCount(items) {
  return (items || []).reduce(function (acc, item) {
    return acc + Number(item.quantity || 0);
  }, 0);
}

let lastCart = { items: [], subtotal: 0 };
let promoPercent = 0;

function renderTotals(cart) {
  const subtotal = Number((cart && cart.subtotal) || 0);
  const delivery = 0;
  const discount = promoPercent > 0 ? Math.round((subtotal * promoPercent) / 100) : 0;
  const total = Math.max(0, subtotal + delivery - discount);

  const subtotalEl = document.getElementById("cart-subtotal");
  const deliveryEl = document.getElementById("cart-delivery");
  const discountEl = document.getElementById("cart-discount");
  const discountRow = document.getElementById("cart-discount-row");
  const totalEl = document.getElementById("cart-total");

  if (subtotalEl) subtotalEl.textContent = formatMoney(subtotal);
  if (deliveryEl) deliveryEl.textContent = formatMoney(delivery);
  if (discountEl) discountEl.textContent = `- ${formatMoney(discount)}`;
  if (discountRow) discountRow.classList.toggle("hidden", discount <= 0);
  if (totalEl) totalEl.textContent = formatMoney(total);
}

function ensureCartVisibility(hasItems) {
  const loading = document.getElementById("state-loading");
  const empty = document.getElementById("state-empty");
  const root = document.getElementById("cart-root");

  if (loading) loading.classList.add("hidden");
  if (empty) empty.classList.toggle("hidden", hasItems);
  if (root) root.classList.toggle("hidden", !hasItems);
}

function lineVariantText(item) {
  if (item.variant_name) return item.variant_name;
  if (item.modifiers && item.modifiers.length > 0) {
    return item.modifiers
      .map(function (m) {
        return m.name_uz || m.name_ru || "";
      })
      .filter(Boolean)
      .join(", ");
  }
  return t("catalog_standard", "Standart");
}

async function deleteCartItem(itemId, rowEl) {
  try {
    await window.apiFetch(`/api/v1/cart/items/${itemId}`, { method: "DELETE" });
    haptic("light");
    if (rowEl) {
      rowEl.classList.add("removing");
      setTimeout(function () {
        rowEl.remove();
      }, 120);
    }

    lastCart = await window.apiFetch("/api/v1/cart");
    const count = cartCount(lastCart.items);
    updateCartBadge(count);
    renderTotals(lastCart);
    ensureCartVisibility(count > 0);
  } catch (_) {
    hapticErr();
    showToast(t("cart_item_delete_failed", "Mahsulot o'chirilmadi"), "error");
  }
}

async function patchQuantity(item, nextQty, qtyEl, priceEl) {
  if (nextQty <= 0) {
    const row = qtyEl ? qtyEl.closest(".cart-item") : null;
    await deleteCartItem(item.id, row);
    return;
  }

  const oldVal = Number(item.total_price || 0);

  try {
    haptic("light");
    const cart = await window.apiFetch(`/api/v1/cart/items/${item.id}`, {
      method: "PATCH",
      body: JSON.stringify({ quantity: nextQty }),
    });

    const updated = (cart.items || []).find(function (x) {
      return x.id === item.id;
    });

    if (updated) {
      item.quantity = updated.quantity;
      item.total_price = updated.total_price;
      if (qtyEl) qtyEl.textContent = String(updated.quantity);
      if (priceEl) animateNum(priceEl, oldVal, Number(updated.total_price));
    }

    lastCart = cart;
    renderTotals(cart);
    updateCartBadge(cartCount(cart.items));
  } catch (_) {
    hapticErr();
    showToast(t("cart_qty_update_failed", "Miqdorni yangilab bo'lmadi"), "error");
  }
}

function renderLines(items) {
  const lines = document.getElementById("cart-lines");
  if (!lines) return;
  lines.innerHTML = "";

  (items || []).forEach(function (item) {
    const row = document.createElement("article");
    row.className = "cart-item";

    const img = item.snapshot && item.snapshot.image_url ? item.snapshot.image_url : "";

    row.innerHTML =
      `<img class="cart-item-img" src="${img}" alt="${item.product_name}" onerror="this.src='';this.style.background='var(--bg-elevated)'" />` +
      `<div class="cart-item-info">` +
      `<div class="cart-item-name">${item.product_name}</div>` +
      `<div class="cart-item-variant">${lineVariantText(item)}</div>` +
      `<div class="cart-item-bottom">` +
      `<div class="qty-control">` +
      `<button class="qty-btn minus" type="button">-</button>` +
      `<span class="qty-value">${item.quantity}</span>` +
      `<button class="qty-btn plus" type="button">+</button>` +
      `</div>` +
      `<div style="display:flex;align-items:center;gap:8px;">` +
      `<span class="cart-item-price">${formatMoney(item.total_price)}</span>` +
      `<button class="btn btn-danger btn-sm" type="button">×</button>` +
      `</div>` +
      `</div>` +
      `</div>`;

    const minus = row.querySelector(".qty-btn.minus");
    const plus = row.querySelector(".qty-btn.plus");
    const qtyEl = row.querySelector(".qty-value");
    const priceEl = row.querySelector(".cart-item-price");
    const remove = row.querySelector(".btn-danger");

    minus.addEventListener("click", function () {
      patchQuantity(item, Number(item.quantity) - 1, qtyEl, priceEl);
    });

    plus.addEventListener("click", function () {
      patchQuantity(item, Number(item.quantity) + 1, qtyEl, priceEl);
    });

    remove.addEventListener("click", function () {
      deleteCartItem(item.id, row);
    });

    lines.appendChild(row);
  });
}

async function refreshCart() {
  try {
    await (window.appLangReady || Promise.resolve());
    const data = await window.apiFetch("/api/v1/cart");
    lastCart = data;

    const hasItems = !!(data.items && data.items.length > 0);
    ensureCartVisibility(hasItems);

    if (!hasItems) {
      updateCartBadge(0);
      return;
    }

    renderLines(data.items);
    renderTotals(data);
    updateCartBadge(cartCount(data.items));
  } catch (_) {
    const loading = document.getElementById("state-loading");
    const empty = document.getElementById("state-empty");
    const root = document.getElementById("cart-root");
    if (loading) loading.classList.add("hidden");
    if (root) root.classList.add("hidden");
    if (empty) empty.classList.remove("hidden");
  }
}

const clearBtn = document.getElementById("cart-clear");
if (clearBtn) {
  clearBtn.addEventListener("click", async function () {
    try {
      await window.apiFetch("/api/v1/cart/clear", { method: "DELETE" });
      promoPercent = 0;
      haptic("light");
      showToast(t("cart_cleared", "Savat tozalandi"), "info");
      refreshCart();
    } catch (_) {
      hapticErr();
      showToast(t("cart_clear_failed", "Savatni tozalab bo'lmadi"), "error");
    }
  });
}

const promoBtn = document.getElementById("promo-apply");
if (promoBtn) {
  promoBtn.addEventListener("click", function () {
    const input = document.getElementById("promo-input");
    const code = input ? (input.value || "").trim() : "";
    if (!code) {
      hapticErr();
      showToast(t("promo_enter_code", "Promo kod kiriting"), "error");
      return;
    }

    promoPercent = 10;
    if (input) input.classList.add("applied");
    showToast(t("promo_applied", "Chegirma qo'llanildi! -10%"), "success");
    hapticOk();
    renderTotals(lastCart || { subtotal: 0, items: [] });
  });
}

refreshCart();
