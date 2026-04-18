const DELIVERY_LOCATION_KEY = "delivery_location";
const DEFAULT_CENTER = [41.2995, 69.2401];
const DEFAULT_ZOOM = 13;

let deliveryMap = null;
let selectedLat = DEFAULT_CENTER[0];
let selectedLng = DEFAULT_CENTER[1];
let selectedAddress = "";
let pendingLookupId = 0;
let moveTimer = null;

function t(key, fallback, params) {
  if (typeof window.feT === "function") {
    return window.feT(key, fallback, params);
  }
  return fallback;
}

function parseStoredLocation() {
  try {
    const raw = sessionStorage.getItem(DELIVERY_LOCATION_KEY);
    if (!raw) return null;
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

function renderCoords() {
  const coordsEl = document.getElementById("map-coords");
  if (!coordsEl) return;
  coordsEl.textContent = `${t("map_coords", "Koordinata:")} ${selectedLat.toFixed(6)}, ${selectedLng.toFixed(6)}`;
}

function setAddressText(text) {
  const addressEl = document.getElementById("map-address");
  if (!addressEl) return;
  addressEl.textContent = text;
}

async function reverseGeocode(lat, lng) {
  const url = `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lng}&zoom=18&addressdetails=1`;
  const res = await fetch(url, {
    method: "GET",
    headers: {
      Accept: "application/json",
    },
  });
  if (!res.ok) throw new Error("reverse_geocode_failed");
  const data = await res.json();
  return String(data.display_name || "").trim();
}

async function updateSelection() {
  if (!deliveryMap) return;
  const center = deliveryMap.getCenter();
  selectedLat = Number(center.lat);
  selectedLng = Number(center.lng);
  renderCoords();

  const lookupId = ++pendingLookupId;
  setAddressText(t("map_loading", "Manzil aniqlanmoqda..."));
  try {
    const address = await reverseGeocode(selectedLat, selectedLng);
    if (lookupId !== pendingLookupId) return;
    selectedAddress = address || `${selectedLat.toFixed(6)}, ${selectedLng.toFixed(6)}`;
    setAddressText(selectedAddress);
  } catch (_) {
    if (lookupId !== pendingLookupId) return;
    selectedAddress = `${selectedLat.toFixed(6)}, ${selectedLng.toFixed(6)}`;
    setAddressText(`${t("map_coords", "Koordinata:")} ${selectedAddress}`);
  }
}

function scheduleSelectionUpdate() {
  if (moveTimer) clearTimeout(moveTimer);
  moveTimer = setTimeout(updateSelection, 250);
}

function saveLocationAndReturn() {
  const payload = {
    lat: selectedLat,
    lng: selectedLng,
    address: selectedAddress || `${selectedLat.toFixed(6)}, ${selectedLng.toFixed(6)}`,
    saved_at: Date.now(),
  };
  sessionStorage.setItem(DELIVERY_LOCATION_KEY, JSON.stringify(payload));
  if (typeof hapticOk === "function") hapticOk();

  if (document.referrer && document.referrer.includes("/webapp/checkout")) {
    history.back();
    return;
  }
  window.location.href = "/webapp/checkout";
}

function initMap() {
  if (!window.L) {
    if (typeof showToast === "function") showToast(t("map_load_failed", "Xarita yuklanmadi"), "error");
    return;
  }

  const stored = parseStoredLocation();
  if (stored) {
    selectedLat = stored.lat;
    selectedLng = stored.lng;
    selectedAddress = stored.address;
  }

  deliveryMap = L.map("delivery-map", {
    zoomControl: true,
    attributionControl: true,
  }).setView([selectedLat, selectedLng], stored ? 16 : DEFAULT_ZOOM);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(deliveryMap);

  deliveryMap.on("moveend", scheduleSelectionUpdate);
  renderCoords();

  if (selectedAddress) {
    setAddressText(selectedAddress);
  } else {
    scheduleSelectionUpdate();
  }
}

const confirmBtn = document.getElementById("confirm-location-btn");
if (confirmBtn) {
  confirmBtn.addEventListener("click", saveLocationAndReturn);
}

(async function startMap() {
  await (window.appLangReady || Promise.resolve());
  initMap();
})();

document.addEventListener("fe:lang-changed", function () {
  renderCoords();
});
