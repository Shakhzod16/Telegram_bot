function show(el, on) {
  if (!el) return;
  el.classList.toggle("hidden", !on);
}

function formatMoney(value) {
  const n = Number(value || 0);
  return `${n.toLocaleString()} UZS`;
}

function cartCount(cart) {
  return (cart.items || []).reduce(function (acc, item) {
    return acc + Number(item.quantity || 0);
  }, 0);
}

let activeCategoryId = null;
let searchTerm = "";
let productDetail = null;
let selectedVariantId = null;

function updateCategoryActiveState() {
  document.querySelectorAll("#categories .category-chip").forEach(function (btn) {
    const id = btn.dataset.categoryId;
    const isActive = id === String(activeCategoryId || "");
    btn.classList.toggle("active", isActive);
  });
}

async function refreshBadgeFromCart() {
  try {
    const cart = await window.apiFetch("/api/v1/cart");
    updateCartBadge(cartCount(cart));
  } catch (e) {
    updateCartBadge(0);
  }
}

async function addToCart(btn, id, variantId) {
  try {
    const payload = {
      product_id: id,
      quantity: 1,
      modifier_ids: [],
    };

    if (variantId) {
      payload.variant_id = Number(variantId);
    }

    const cart = await window.apiFetch("/api/v1/cart/items", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    if (btn && btn.classList && btn.classList.contains("btn-add")) {
      animateAddBtn(btn);
    }

    haptic();
    updateCartBadge(cartCount(cart));
    showToast("Savatga qo'shildi", "success");
  } catch (e) {
    hapticErr();
    showToast("Savatga qo'shib bo'lmadi", "error");
  }
}

window.addToCart = addToCart;

function renderProducts(items) {
  const grid = document.getElementById("products");
  if (!grid) return;
  grid.innerHTML = "";

  (items || []).forEach(function (p) {
    const card = document.createElement("article");
    card.className = "product-card";
    card.addEventListener("click", function () {
      openProductSheet(p.id);
    });

    card.innerHTML =
      `<img class="product-card-img" src="${p.image_url || ""}" alt="${p.name_uz}" loading="lazy" onerror="this.src='';this.style.background='var(--bg-elevated)'" />` +
      `<div class="product-card-body">` +
      `<div class="product-card-name">${p.name_uz}</div>` +
      `<div class="product-card-weight">${p.weight_grams ? `${p.weight_grams} g` : "Standart"}</div>` +
      `<div class="product-card-footer">` +
      `<div class="product-card-price">${formatMoney(p.base_price)}</div>` +
      `<button class="btn-add" onclick="addToCart(this, ${p.id})">+</button>` +
      `</div>` +
      `</div>`;

    const addBtn = card.querySelector(".btn-add");
    if (addBtn) {
      addBtn.addEventListener("click", function (e) {
        e.stopPropagation();
      });
    }

    grid.appendChild(card);
  });
}

function renderCategories(cats) {
  const chipWrap = document.getElementById("categories");
  if (!chipWrap) return;
  chipWrap.innerHTML = "";

  const all = document.createElement("button");
  all.type = "button";
  all.className = "category-chip";
  all.textContent = "Barchasi";
  all.dataset.categoryId = "";
  all.addEventListener("click", function () {
    haptic("light");
    activeCategoryId = null;
    updateCategoryActiveState();
    loadProducts();
  });
  chipWrap.appendChild(all);

  (cats || []).forEach(function (c) {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "category-chip";
    chip.textContent = c.name_uz;
    chip.dataset.categoryId = String(c.id);
    chip.addEventListener("click", function () {
      haptic("light");
      activeCategoryId = c.id;
      updateCategoryActiveState();
      loadProducts();
    });
    chipWrap.appendChild(chip);
  });

  updateCategoryActiveState();
}

async function openProductSheet(productId) {
  try {
    productDetail = await window.apiFetch(`/api/v1/products/${productId}`);
    const variantExists = (productDetail.variants || []).some(function (v) {
      return String(v.id) === String(selectedVariantId);
    });
    if (!variantExists) {
      selectedVariantId = (productDetail.variants || []).find(function (v) {
        return !!v.is_default;
      });
      selectedVariantId = selectedVariantId ? selectedVariantId.id : ((productDetail.variants || [])[0] || {}).id || null;
    }

    const image = document.getElementById("sheet-image");
    const name = document.getElementById("sheet-name");
    const desc = document.getElementById("sheet-desc");
    const variantsLabel = document.getElementById("sheet-variants-label");
    const variants = document.getElementById("sheet-variants");
    const price = document.getElementById("sheet-price");
    const addBtn = document.getElementById("sheet-add-btn");

    if (image) {
      image.src = productDetail.image_url || "";
      image.alt = productDetail.name_uz || "Mahsulot";
    }
    if (name) name.textContent = productDetail.name_uz || "";
    if (desc) desc.textContent = productDetail.description_uz || "Mazali taom.";

    const hasVariants = (productDetail.variants || []).length > 0;
    if (variantsLabel) variantsLabel.classList.toggle("hidden", !hasVariants);
    if (variants) {
      variants.classList.toggle("hidden", !hasVariants);
      variants.innerHTML = "";

      (productDetail.variants || []).forEach(function (v) {
        const item = document.createElement("button");
        item.type = "button";
        item.className = "variant-item" + (String(v.id) === String(selectedVariantId) ? " selected" : "");
        item.innerHTML = `<span>${v.name_uz}</span><span class="variant-price">${formatMoney(v.price)}</span>`;
        item.addEventListener("click", function () {
          selectedVariantId = v.id;
          haptic("light");
          openProductSheet(productId);
        });
        variants.appendChild(item);
      });
    }

    const selectedVariant = (productDetail.variants || []).find(function (v) {
      return String(v.id) === String(selectedVariantId);
    });
    const finalPrice = selectedVariant ? selectedVariant.price : productDetail.base_price;
    if (price) price.textContent = formatMoney(finalPrice);

    if (addBtn) {
      addBtn.onclick = async function () {
        addBtn.classList.add("loading");
        await addToCart(null, productId, selectedVariantId);
        addBtn.classList.remove("loading");
      };
    }

    openSheet("product-sheet");
  } catch (e) {
    hapticErr();
    showToast("Mahsulot ma'lumoti ochilmadi", "error");
  }
}

async function loadProducts() {
  const q = new URLSearchParams();
  if (activeCategoryId) q.set("category_id", String(activeCategoryId));
  if (searchTerm) q.set("search", searchTerm);
  q.set("page", "1");
  q.set("size", "40");

  const loading = document.getElementById("state-loading");
  const empty = document.getElementById("state-empty");
  const root = document.getElementById("catalog-root");

  try {
    show(loading, true);
    const data = await window.apiFetch("/api/v1/products?" + q.toString());
    const items = data.items || [];
    renderProducts(items);

    show(loading, false);
    show(root, items.length > 0);
    show(empty, items.length === 0);
  } catch (e) {
    show(loading, false);
    show(root, false);
    show(empty, true);
  }
}

async function loadCatalog() {
  const loading = document.getElementById("state-loading");
  const empty = document.getElementById("state-empty");
  const root = document.getElementById("catalog-root");

  try {
    await (window.authReady || Promise.resolve());
    const cats = await window.apiFetch("/api/v1/categories");
    renderCategories(cats || []);

    await Promise.all([loadProducts(), refreshBadgeFromCart()]);

    show(loading, false);
    show(root, true);
    show(empty, false);
  } catch (e) {
    show(loading, false);
    show(root, false);
    show(empty, true);
  }
}

(function initSearch() {
  const input = document.getElementById("search-input");
  if (!input) return;
  let timer = null;
  input.addEventListener("input", function (e) {
    clearTimeout(timer);
    timer = setTimeout(function () {
      searchTerm = (e.target.value || "").trim();
      loadProducts();
    }, 240);
  });
})();

loadCatalog();
