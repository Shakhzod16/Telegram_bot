const tg = window.Telegram?.WebApp ?? {
	initData: '',
	initDataUnsafe: {},
	ready() {},
	expand() {},
	showAlert(message) {
		window.alert(message);
	},
	sendData(data) {
		console.log('Telegram sendData fallback:', data);
	},
	openLink(url) {
		window.open(url, '_blank', 'noopener,noreferrer');
	},
};

tg.ready();
tg.expand();

// ❗️ NGROK URL (har safar yangilang)
const API_BASE_URL = 'https://nobuko-nonrepressive-khloe.ngrok-free.dev';

const state = {
	user: null,
	texts: {},
	products: [],
	cart: {},
	location: null,
	orderId: null,
};

const els = {
	title: document.getElementById('title'),
	subtitle: document.getElementById('subtitle'),
	locationBtn: document.getElementById('location-btn'),
	products: document.getElementById('products'),
	cartTitle: document.getElementById('cart-title'),
	cartTotal: document.getElementById('cart-total'),
	cartItems: document.getElementById('cart-items'),
	submitOrder: document.getElementById('submit-order'),
	payments: document.getElementById('payments'),
	payClick: document.getElementById('pay-click'),
	payPayme: document.getElementById('pay-payme'),
};

const productTpl = document.getElementById('product-card-template');
const cartTpl = document.getElementById('cart-item-template');

// ✅ API URL builder
function apiUrl(path) {
	return `${API_BASE_URL}${path}`;
}

// ✅ Telegram init data header
function initDataHeader() {
	return tg.initData ? { 'X-Init-Data': tg.initData } : {};
}

// ✅ Toast
function showToast(message) {
	tg.showAlert(message);
}

// ✅ Price formatter
function formatAmount(value) {
	return `${value.toLocaleString('ru-RU')} so'm`;
}

// ✅ Universal API request
async function apiRequest(path, options = {}) {
	try {
		const response = await fetch(apiUrl(path), {
			...options,
			headers: {
				'Content-Type': 'application/json',
				...initDataHeader(),
				...(options.headers || {}),
			},
		});

		if (!response.ok) {
			let detail = 'Server xatosi';
			try {
				const error = await response.json();
				detail = error.detail || error.error_note || detail;
			} catch (_error) {
				detail = response.statusText || detail;
			}
			throw new Error(detail);
		}

		const contentType = response.headers.get('content-type') || '';
		if (contentType.includes('application/json')) {
			return await response.json();
		}
		return null;
	} catch (error) {
		if (error instanceof TypeError) {
			showToast('❌ Internet yo‘q yoki backend ishlamayapti');
		} else {
			showToast(`❌ ${error.message}`);
		}
		throw error;
	}
}

// ✅ Bootstrap (init)
async function bootstrap() {
	if (!tg.initData) {
		showToast('❌ Telegram ichida oching');
		return;
	}

	const data = await apiRequest('/api/bootstrap', {
		method: 'POST',
		body: JSON.stringify({}),
	});

	state.user = data.user;
	state.products = data.products;
	state.texts = data.texts;

	paintStaticText();
	renderProducts();
	renderCart();
}

// ✅ Static texts
function paintStaticText() {
	els.title.textContent = state.texts.frontend_title || 'FoodExpress';
	els.subtitle.textContent = state.texts.frontend_subtitle || '';
	els.locationBtn.textContent = state.texts.frontend_detect_location || 'Location';
	els.cartTitle.textContent = state.texts.frontend_cart || 'Cart';
	els.submitOrder.textContent = state.texts.frontend_order || 'Buyurtma berish';
	els.payClick.textContent = state.texts.frontend_payment_click || 'Click';
	els.payPayme.textContent = state.texts.frontend_payment_payme || 'Payme';
}

// 🚀 INIT
bootstrap();
