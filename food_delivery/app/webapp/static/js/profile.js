function normalizeLang(value) {
  const lang = String(value || "").toLowerCase();
  if (lang === "ru" || lang === "en") return lang;
  return "uz";
}

function t(key, fallback, params) {
  if (typeof window.feT === "function") {
    return window.feT(key, fallback, params);
  }
  return fallback;
}

function setActiveLang(lang) {
  const safeLang = normalizeLang(lang);
  document.querySelectorAll(".lang-btn").forEach(function (btn) {
    btn.classList.toggle("active", btn.dataset.lang === safeLang);
  });
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

function applyLanguageUi(lang) {
  const safeLang = normalizeLang(lang);
  if (typeof window.setAppLanguage === "function") {
    window.setAppLanguage(safeLang);
  } else {
    localStorage.setItem("fe_lang", safeLang);
  }
  setActiveLang(safeLang);
}

function renderProfile(profile, lang) {
  const fullName = `${profile.first_name || ""} ${profile.last_name || ""}`.trim();
  const display = fullName || profile.username || t("profile_user_fallback", "Foydalanuvchi");

  const nameEl = document.getElementById("profile-name");
  if (nameEl) nameEl.textContent = display;

  const phoneEl = document.getElementById("profile-phone");
  if (phoneEl) phoneEl.textContent = profile.phone || t("profile_phone_missing", "Telefon raqam kiritilmagan");

  const avatarEl = document.getElementById("profile-avatar");
  if (avatarEl) avatarEl.textContent = (display || "F").slice(0, 1).toUpperCase();

  setActiveLang(lang);
}

function bindLanguageButtons() {
  document.querySelectorAll(".lang-btn").forEach(function (btn) {
    btn.addEventListener("click", async function () {
      const nextLang = normalizeLang(btn.dataset.lang);
      const prevLang = normalizeLang(
        (typeof window.getAppLanguage === "function" && window.getAppLanguage()) ||
          localStorage.getItem("fe_lang") ||
          "uz"
      );
      if (nextLang === prevLang) return;

      setLangButtonsDisabled(true);
      try {
        await window.apiFetch("/api/v1/profile", {
          method: "PATCH",
          body: JSON.stringify({ language: nextLang }),
        });
        applyLanguageUi(nextLang);
        if (typeof haptic === "function") haptic("light");
        if (typeof showToast === "function") showToast(t("profile_lang_updated", "Til yangilandi"), "success");
      } catch (_) {
        if (typeof hapticErr === "function") hapticErr();
        if (typeof showToast === "function") showToast(t("profile_lang_update_failed", "Tilni yangilab bo'lmadi"), "error");
      } finally {
        setLangButtonsDisabled(false);
      }
    });
  });
}

async function loadProfile() {
  const loading = document.getElementById("state-loading");
  const root = document.getElementById("profile-root");

  try {
    await (window.appLangReady || Promise.resolve());
    const profile = await window.apiFetch("/api/v1/profile");
    const currentLang = normalizeLang(profile.language || (window.getAppLanguage ? window.getAppLanguage() : "uz"));
    applyLanguageUi(currentLang);

    if (loading) loading.classList.add("hidden");
    if (root) root.classList.remove("hidden");

    renderProfile(profile, currentLang);
    refreshCartBadge();
  } catch (_) {
    if (loading) loading.classList.add("hidden");
    if (typeof showToast === "function") showToast(t("profile_load_failed", "Profilni yuklab bo'lmadi"), "error");
  }
}

const logoutBtn = document.getElementById("logout-btn");
if (logoutBtn) {
  logoutBtn.addEventListener("click", function () {
    sessionStorage.removeItem("access_token");
    if (typeof haptic === "function") haptic("medium");
    if (typeof showToast === "function") showToast(t("profile_session_ended", "Sessiya yakunlandi"), "info");
    setTimeout(function () {
      window.location.reload();
    }, 180);
  });
}

bindLanguageButtons();
loadProfile();
