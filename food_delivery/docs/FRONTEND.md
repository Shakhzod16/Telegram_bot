# WebApp Frontend Qoidalar

## Telegram WebApp SDK

Har sahifada ishlatilishi shart:

```javascript
// Telegram tema ranglarini CSS ga o'tkazish
document.documentElement.style.setProperty(
  '--tg-bg', Telegram.WebApp.backgroundColor
);

// Back button
Telegram.WebApp.BackButton.show();
Telegram.WebApp.BackButton.onClick(() => history.back());

// Haptic feedback
Telegram.WebApp.HapticFeedback.impactOccurred('light'); // tugma bosilganda
Telegram.WebApp.HapticFeedback.notificationOccurred('success'); // muvaffaqiyat

// WebApp tayyor
Telegram.WebApp.ready();
Telegram.WebApp.expand();
```

## api.js — Central Fetch Wrapper

Barcha API so'rovlar shu wrapper orqali qilinadi:

```javascript
async function apiCall(method, endpoint, body = null) {
  const token = localStorage.getItem('jwt_token');
  const options = {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` })
    },
    ...(body && { body: JSON.stringify(body) })
  };

  const res = await fetch(`/api/v1${endpoint}`, options);

  if (res.status === 401) {
    await reAuthenticate();
    return apiCall(method, endpoint, body);
  }

  if (!res.ok) {
    const err = await res.json();
    throw new APIError(err.detail, res.status);
  }

  return res.json();
}
```

## Loading Skeleton pattern

```html
<div class="skeleton-card" id="loading-state">
  <div class="skeleton-img"></div>
  <div class="skeleton-line"></div>
  <div class="skeleton-line short"></div>
</div>

<div id="content-state" style="display:none">
  <!-- real content -->
</div>
```

```javascript
async function loadProducts() {
  showSkeleton();
  try {
    const data = await apiCall('GET', '/products');
    renderProducts(data);
    showContent();
  } catch (e) {
    showError(e.message);
  }
}
```

## CSS Telegram theme variables

```css
:root {
  --bg: var(--tg-theme-bg-color, #ffffff);
  --text: var(--tg-theme-text-color, #000000);
  --hint: var(--tg-theme-hint-color, #999999);
  --link: var(--tg-theme-link-color, #2481cc);
  --button-bg: var(--tg-theme-button-color, #2481cc);
  --button-text: var(--tg-theme-button-text-color, #ffffff);
  --secondary-bg: var(--tg-theme-secondary-bg-color, #f0f0f0);
}
```

## Bottom Navbar

```html
<nav class="bottom-nav">
  <a href="/webapp/" class="nav-item active">
    <svg><!-- home icon --></svg>
    <span>Bosh sahifa</span>
  </a>
  <a href="/webapp/cart" class="nav-item">
    <svg><!-- cart icon --></svg>
    <span>Savat</span>
    <span class="badge" id="cart-badge">0</span>
  </a>
  <a href="/webapp/orders" class="nav-item">
    <svg><!-- orders icon --></svg>
    <span>Buyurtmalar</span>
  </a>
  <a href="/webapp/profile" class="nav-item">
    <svg><!-- profile icon --></svg>
    <span>Profil</span>
  </a>
</nav>
```
