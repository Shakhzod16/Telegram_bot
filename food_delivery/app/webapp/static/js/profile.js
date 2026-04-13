async function refreshCartBadge() {
  try {
    const cart = await window.apiFetch("/api/v1/cart");
    const count = (cart.items || []).reduce(function (acc, it) {
      return acc + Number(it.quantity || 0);
    }, 0);
    updateCartBadge(count);
  } catch (e) {
    updateCartBadge(0);
  }
}

function setActiveLang(lang) {
  document.querySelectorAll(".lang-btn").forEach(function (btn) {
    btn.classList.toggle("active", btn.dataset.lang === lang);
  });
}

async function loadProfile() {
  const loading = document.getElementById("state-loading");
  const root = document.getElementById("profile-root");

  try {
    const p = await window.apiFetch("/api/v1/profile");

    if (loading) loading.classList.add("hidden");
    if (root) root.classList.remove("hidden");

    const fullName = `${p.first_name || ""} ${p.last_name || ""}`.trim();
    const display = fullName || p.username || "Foydalanuvchi";

    document.getElementById("profile-name").textContent = display;
    document.getElementById("profile-phone").textContent = p.phone || "Telefon raqam kiritilmagan";
    document.getElementById("profile-avatar").textContent = display.slice(0, 1).toUpperCase();

    setActiveLang(p.language || "uz");

    document.querySelectorAll(".lang-btn").forEach(function (btn) {
      btn.onclick = async function () {
        const nextLang = btn.dataset.lang;
        try {
          await window.apiFetch("/api/v1/profile", {
            method: "PATCH",
            body: JSON.stringify({ language: nextLang }),
          });
          setActiveLang(nextLang);
          haptic("light");
          showToast("Til yangilandi", "success");
        } catch (e) {
          hapticErr();
          showToast("Tilni yangilab bo'lmadi", "error");
        }
      };
    });

    refreshCartBadge();
  } catch (e) {
    if (loading) loading.classList.add("hidden");
    showToast("Profilni yuklab bo'lmadi", "error");
  }
}

const logoutBtn = document.getElementById("logout-btn");
if (logoutBtn) {
  logoutBtn.addEventListener("click", function () {
    sessionStorage.removeItem("access_token");
    haptic("medium");
    showToast("Sessiya yakunlandi", "info");
    setTimeout(function () {
      window.location.reload();
    }, 180);
  });
}

loadProfile();
