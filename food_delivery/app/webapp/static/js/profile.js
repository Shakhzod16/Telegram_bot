const PROFILE_I18N = {
  uz: {
    langTitle: "Til",
    accountTitle: "Akkaunt",
    addresses: "Xaritada manzil",
    logout: "Chiqish",
    phoneMissing: "Telefon raqam kiritilmagan",
    toastLanguageUpdated: "Til yangilandi",
    toastLanguageFailed: "Tilni yangilab bo'lmadi",
    toastProfileFailed: "Profilni yuklab bo'lmadi",
    toastSessionEnded: "Sessiya yakunlandi",
    nav: {
      home: "Bosh sahifa",
      cart: "Savat",
      orders: "Buyurtmalar",
      profile: "Profil",
    },
  },
  ru: {
    langTitle: "Язык",
    accountTitle: "Аккаунт",
    addresses: "Мои адреса",
    logout: "Выйти",
    phoneMissing: "Номер телефона не указан",
    toastLanguageUpdated: "Язык обновлен",
    toastLanguageFailed: "Не удалось обновить язык",
    toastProfileFailed: "Не удалось загрузить профиль",
    toastSessionEnded: "Сессия завершена",
    nav: {
      home: "Главная",
      cart: "Корзина",
      orders: "Заказы",
      profile: "Профиль",
    },
  },
};

function normalizeLang(value) {
  return String(value || "").toLowerCase() === "ru" ? "ru" : "uz";
}

function tr(lang) {
  return PROFILE_I18N[normalizeLang(lang)];
}

function setActiveLang(lang) {
  const safeLang = normalizeLang(lang);
  document.querySelectorAll(".lang-btn").forEach(function (btn) {
    btn.classList.toggle("active", btn.dataset.lang === safeLang);
  });
}

function applyNavTranslations(lang) {
  const dict = tr(lang);
  const routeKeyByHref = {
    "/webapp/": "home",
    "/webapp/cart": "cart",
    "/webapp/orders": "orders",
    "/webapp/profile": "profile",
  };
  document.querySelectorAll(".navbar .nav-item").forEach(function (item) {
    const href = item.getAttribute("href") || "";
    const key = routeKeyByHref[href];
    if (!key) return;
    const labelEl = item.querySelector(".nav-label");
    if (!labelEl) return;
    labelEl.textContent = dict.nav[key];
  });
  document.documentElement.lang = normalizeLang(lang);
}

function applyProfileTranslations(lang) {
  const dict = tr(lang);

  const langTitleEl = document.getElementById("profile-lang-title");
  if (langTitleEl) langTitleEl.textContent = dict.langTitle;

  const accountTitleEl = document.getElementById("profile-account-title");
  if (accountTitleEl) accountTitleEl.textContent = dict.accountTitle;

  const addressesLabelEl = document.getElementById("profile-addresses-label");
  if (addressesLabelEl) addressesLabelEl.textContent = dict.addresses;

  const logoutLabelEl = document.getElementById("profile-logout-label");
  if (logoutLabelEl) logoutLabelEl.textContent = dict.logout;
}

function applyLanguageUi(lang) {
  const safeLang = normalizeLang(lang);
  setActiveLang(safeLang);
  applyProfileTranslations(safeLang);
  applyNavTranslations(safeLang);
}

function setLangButtonsDisabled(disabled) {
  document.querySelectorAll(".lang-btn").forEach(function (btn) {
    btn.disabled = !!disabled;
  });
}

async function refreshCartBadge() {
  if (typeof updateCartBadge !== "function") return;
  try {
    const cart = await window.apiFetch("/api/v1/cart");
    const count = (cart.items || []).reduce(function (acc, it) {
      return acc + Number(it.quantity || 0);
    }, 0);
    updateCartBadge(count);
  } catch (_) {
    updateCartBadge(0);
  }
}

function renderProfile(profile, lang) {
  const dict = tr(lang);
  const fullName = `${profile.first_name || ""} ${profile.last_name || ""}`.trim();
  const display = fullName || profile.username || "Foydalanuvchi";

  const nameEl = document.getElementById("profile-name");
  if (nameEl) nameEl.textContent = display;

  const phoneEl = document.getElementById("profile-phone");
  if (phoneEl) phoneEl.textContent = profile.phone || dict.phoneMissing;

  const avatarEl = document.getElementById("profile-avatar");
  if (avatarEl) avatarEl.textContent = (display || "F").slice(0, 1).toUpperCase();
}

function bindLanguageButtons() {
  document.querySelectorAll(".lang-btn").forEach(function (btn) {
    btn.addEventListener("click", async function () {
      const nextLang = normalizeLang(btn.dataset.lang);
      const prevLang = normalizeLang(window.__profileLang || localStorage.getItem("fe_lang") || "uz");
      if (nextLang === prevLang) return;

      setLangButtonsDisabled(true);
      try {
        await window.apiFetch("/api/v1/profile", {
          method: "PATCH",
          body: JSON.stringify({ language: nextLang }),
        });
        window.__profileLang = nextLang;
        localStorage.setItem("fe_lang", nextLang);
        applyLanguageUi(nextLang);
        if (typeof haptic === "function") haptic("light");
        if (typeof showToast === "function") showToast(tr(nextLang).toastLanguageUpdated, "success");
      } catch (_) {
        if (typeof hapticErr === "function") hapticErr();
        if (typeof showToast === "function") showToast(tr(prevLang).toastLanguageFailed, "error");
      } finally {
        setLangButtonsDisabled(false);
      }
    });
  });
}

async function loadProfile() {
  const loading = document.getElementById("state-loading");
  const root = document.getElementById("profile-root");

  // Initial UI based on saved language while profile is loading.
  const savedLang = normalizeLang(localStorage.getItem("fe_lang") || "uz");
  applyLanguageUi(savedLang);

  try {
    const profile = await window.apiFetch("/api/v1/profile");
    const currentLang = normalizeLang(profile.language || savedLang);
    window.__profileLang = currentLang;
    localStorage.setItem("fe_lang", currentLang);

    if (loading) loading.classList.add("hidden");
    if (root) root.classList.remove("hidden");

    renderProfile(profile, currentLang);
    applyLanguageUi(currentLang);
    refreshCartBadge();
  } catch (_) {
    if (loading) loading.classList.add("hidden");
    if (typeof showToast === "function") showToast(tr(savedLang).toastProfileFailed, "error");
  }
}

const logoutBtn = document.getElementById("logout-btn");
if (logoutBtn) {
  logoutBtn.addEventListener("click", function () {
    const currentLang = normalizeLang(window.__profileLang || localStorage.getItem("fe_lang") || "uz");
    sessionStorage.removeItem("access_token");
    if (typeof haptic === "function") haptic("medium");
    if (typeof showToast === "function") showToast(tr(currentLang).toastSessionEnded, "info");
    setTimeout(function () {
      window.location.reload();
    }, 180);
  });
}

bindLanguageButtons();
loadProfile();
