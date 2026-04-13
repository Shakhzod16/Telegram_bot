// Toast
function showToast(msg, type = "info", ms = 2500) {
  let c = document.getElementById("toast-container");
  if (!c) {
    c = document.createElement("div");
    c.id = "toast-container";
    c.className = "toast-container";
    document.body.appendChild(c);
  }
  const t = document.createElement("div");
  const safeType = ["success", "error", "info"].includes(type) ? type : "info";
  t.className = `toast ${safeType}`;
  t.innerHTML = `<span>${{ success: "✓", error: "✕", info: "ℹ" }[safeType]}</span><span>${msg}</span>`;
  c.appendChild(t);
  setTimeout(function () {
    t.classList.add("exit");
    t.addEventListener("animationend", function () {
      t.remove();
    });
  }, ms);
}

// Haptic
function haptic(type = "light") {
  try {
    Telegram.WebApp.HapticFeedback.impactOccurred(type);
  } catch (e) {}
}

function hapticOk() {
  try {
    Telegram.WebApp.HapticFeedback.notificationOccurred("success");
  } catch (e) {}
}

function hapticErr() {
  try {
    Telegram.WebApp.HapticFeedback.notificationOccurred("error");
  } catch (e) {}
}

// Cart badge
function updateCartBadge(n) {
  const b = document.getElementById("cart-badge");
  if (!b) return;
  if (n > 0) {
    b.style.display = "flex";
    b.textContent = n > 99 ? "99+" : String(n);
    b.style.animation = "none";
    b.offsetHeight;
    b.style.animation = "badgePop 220ms cubic-bezier(0.34,1.56,0.64,1)";
  } else {
    b.style.display = "none";
  }
}

// Add to cart button animation
function animateAddBtn(btn) {
  if (!btn) return;
  btn.classList.add("added");
  btn.textContent = "✓";
  setTimeout(function () {
    btn.classList.remove("added");
    btn.textContent = "+";
  }, 700);
}

// Bottom sheet
function openSheet(id) {
  let ov = document.getElementById("sheet-overlay");
  if (!ov) {
    ov = document.createElement("div");
    ov.className = "overlay";
    ov.id = "sheet-overlay";
    document.body.appendChild(ov);
  }
  ov.onclick = function () {
    closeSheet(id);
  };
  ov.style.animation = "fadeIn 220ms forwards";

  const s = document.getElementById(id);
  if (s) {
    s.style.display = "block";
    s.style.animation = "sheetUp 380ms cubic-bezier(0.16,1,0.3,1) forwards";
  }

  document.body.style.overflow = "hidden";
  haptic("medium");
}

function closeSheet(id) {
  const ov = document.getElementById("sheet-overlay");
  const s = document.getElementById(id);
  if (ov) {
    ov.style.opacity = "0";
    setTimeout(function () {
      ov.remove();
    }, 200);
  }
  if (s) {
    s.style.animation = "sheetDown 220ms ease forwards";
    setTimeout(function () {
      s.style.display = "none";
    }, 200);
  }
  document.body.style.overflow = "";
}

// Number counter
function animateNum(el, from, to, ms) {
  if (!el) return;
  const dur = typeof ms === "number" ? ms : 400;
  const start = Date.now();
  const diff = to - from;
  const tick = function () {
    const p = Math.min((Date.now() - start) / dur, 1);
    const e = 1 - Math.pow(1 - p, 3);
    el.textContent = Math.round(from + diff * e).toLocaleString();
    if (p < 1) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}

// List stagger animation
function animateList(nodes, delayStep) {
  const step = typeof delayStep === "number" ? delayStep : 60;
  if (!nodes || typeof nodes.forEach !== "function") return;
  nodes.forEach(function (node, idx) {
    if (!node) return;
    node.style.animationDelay = `${idx * step}ms`;
    node.style.animationPlayState = "running";
  });
}

// Page navigate with exit animation
function goTo(url) {
  const p = document.querySelector(".page");
  if (p) {
    p.style.animation = "pageExit 150ms ease forwards";
  }
  setTimeout(
    function () {
      window.location.href = url;
    },
    p ? 150 : 0,
  );
}

// Inject missing keyframes
if (!document.getElementById("animation-runtime-style")) {
  document.head.insertAdjacentHTML(
    "beforeend",
    `<style id="animation-runtime-style">
@keyframes pageExit { to { opacity:0; transform:scale(0.98); } }
@keyframes sheetDown { to { transform:translateY(100%); } }
</style>`,
  );
}

window.showToast = showToast;
window.haptic = haptic;
window.hapticOk = hapticOk;
window.hapticErr = hapticErr;
window.updateCartBadge = updateCartBadge;
window.animateAddBtn = animateAddBtn;
window.openSheet = openSheet;
window.closeSheet = closeSheet;
window.animateNum = animateNum;
window.animateList = animateList;
window.goTo = goTo;
