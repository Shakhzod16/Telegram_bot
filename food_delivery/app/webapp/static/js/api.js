function safeGetToken() {
	if (typeof window.getAccessTokenSafe === 'function') {
		return window.getAccessTokenSafe();
	}
	try {
		const sessionToken = sessionStorage.getItem('access_token');
		if (sessionToken) return sessionToken;
	} catch (_) {}
	try {
		return localStorage.getItem('access_token');
	} catch (_) {
		return null;
	}
}

function safeClearToken() {
	if (typeof window.clearAccessTokenSafe === 'function') {
		window.clearAccessTokenSafe();
		return;
	}
	try {
		sessionStorage.removeItem('access_token');
	} catch (_) {}
}

function delay(ms) {
	return new Promise(function (resolve) {
		setTimeout(resolve, ms);
	});
}

function readInitDataFromLaunchParams() {
	function extractFromRaw(raw) {
		if (!raw) return null;
		const text = String(raw).trim();
		if (!text) return null;
		const normalized = text.startsWith('#') || text.startsWith('?')
			? text.slice(1)
			: text;
		if (!normalized) return null;
		try {
			const params = new URLSearchParams(normalized);
			const keys = ['tgWebAppData', 'tg_web_app_data', 'init_data'];
			for (let i = 0; i < keys.length; i += 1) {
				const value = (params.get(keys[i]) || '').trim();
				if (value) return value;
			}
		} catch (_) {}
		return null;
	}

	const fromQuery = extractFromRaw(window.location.search || '');
	if (fromQuery) return fromQuery;
	return extractFromRaw(window.location.hash || '');
}

function readInitDataFromQuery() {
	try {
		const params = new URLSearchParams(window.location.search || '');
		const fromQuery = (params.get('tgWebAppData') || '').trim();
		if (fromQuery) return fromQuery;
	} catch (_) {}
	return null;
}

function readInitDataFast() {
	if (typeof window.getTelegramInitDataSafe === 'function') {
		const stored = window.getTelegramInitDataSafe();
		if (stored) return stored;
	}
	const launchData = readInitDataFromLaunchParams();
	if (launchData) return launchData;
	const tg = window.Telegram && window.Telegram.WebApp;
	if (tg && typeof tg.initData === 'string') {
		const direct = tg.initData.trim();
		if (direct) return direct;
	}
	return readInitDataFromQuery();
}

function readTelegramUserIdFast() {
	const tg = window.Telegram && window.Telegram.WebApp;
	const user = tg && tg.initDataUnsafe && tg.initDataUnsafe.user;
	if (!user || user.id === undefined || user.id === null) return null;
	const asNumber = Number(user.id);
	if (!Number.isFinite(asNumber)) return null;
	return String(Math.trunc(asNumber));
}

function generatedInitDataFromUnsafeUser() {
	const tg = window.Telegram && window.Telegram.WebApp;
	const user = tg && tg.initDataUnsafe && tg.initDataUnsafe.user;
	if (!user || !user.id) return null;
	try {
		return 'user=' + encodeURIComponent(JSON.stringify(user));
	} catch (_) {
		return null;
	}
}

async function resolveTelegramInitDataForHeader() {
	if (typeof window.resolveTelegramInitData === 'function') {
		try {
			const external = await window.resolveTelegramInitData();
			if (external) return external;
		} catch (_) {}
	}

	const tg = window.Telegram && window.Telegram.WebApp;
	if (!tg) return null;
	try {
		tg.ready();
	} catch (_) {}

	const direct = readInitDataFast();
	if (direct) return direct;

	const generated = generatedInitDataFromUnsafeUser();
	if (generated) {
		if (typeof window.setTelegramInitDataSafe === 'function') {
			try {
				window.setTelegramInitDataSafe(generated);
			} catch (_) {}
		}
		return generated;
	}

	for (let i = 0; i < 15; i += 1) {
		await delay(80);
		const delayed = readInitDataFast();
		if (delayed) return delayed;

		const delayedGenerated = generatedInitDataFromUnsafeUser();
		if (delayedGenerated) {
			if (typeof window.setTelegramInitDataSafe === 'function') {
				try {
					window.setTelegramInitDataSafe(delayedGenerated);
				} catch (_) {}
			}
			return delayedGenerated;
		}
	}
	return null;
}

async function buildHeaders(options) {
	const headers = Object.assign({}, (options && options.headers) || {});
	const isFormData = options && options.body instanceof FormData;
	if (!isFormData) {
		headers['Content-Type'] = headers['Content-Type'] || 'application/json';
	} else if ('Content-Type' in headers) {
		delete headers['Content-Type'];
	}
	const token = safeGetToken();
	if (token) {
		headers['Authorization'] = 'Bearer ' + token;
	}

	if (!headers['X-Telegram-Init-Data']) {
		const initData = await resolveTelegramInitDataForHeader();
		if (initData) {
			headers['X-Telegram-Init-Data'] = initData;
		}
	}

	// Fallback for Telegram clients where initData is unavailable,
	// but initDataUnsafe.user.id is still exposed.
	if (!headers['X-Telegram-Id']) {
		const tgUserId = readTelegramUserIdFast();
		if (tgUserId) {
			headers['X-Telegram-Id'] = tgUserId;
		}
	}

	return headers;
}

async function parseErrorMessage(res) {
	let msg = 'Xato: ' + res.status;
	try {
		const clone = res.clone();
		const j = await clone.json();
		if (j && j.detail) msg = j.detail;
		else if (j && j.message) msg = j.message;
		else if (j && j.error && j.error.message) msg = j.error.message;
	} catch (_) {}
	return msg;
}

function showError(msg) {
	const el = document.getElementById('app-error');
	if (!el) return;
	el.textContent = msg;
	el.classList.remove('hidden');
}

function hideError() {
	const el = document.getElementById('app-error');
	if (el) el.classList.add('hidden');
}

window.apiFetch = async function apiFetch(path, options, _retried) {
	const isAuthInit = typeof path === 'string' && path.includes('/auth/telegram/init');

	// Auth so'rovi tugashini kutamiz (auth/init bundan mustasno).
	if (!isAuthInit) {
		try {
			await (window.authReady || Promise.resolve());
		} catch (_) {}

		// Token yo'q bo'lsa authni yana bir urinamiz.
		if (!safeGetToken() && typeof window.reauthWithTelegram === 'function') {
			try {
				await window.reauthWithTelegram(false);
			} catch (_) {}
		}
	}

	const base = window.BACKEND_URL || '';
	const mergedOptions = Object.assign({}, options, { headers: await buildHeaders(options) });

	let res;
	try {
		res = await fetch(base + path, mergedOptions);
	} catch (e) {
		const msg = 'Tarmoq xatosi. Internet aloqasini tekshiring.';
		showError(msg);
		throw new Error(msg);
	}

	// 401 → tokenni yangilash va bir marta qayta urinish.
	if (!isAuthInit && res.status === 401 && !_retried) {
		console.warn('[api] 401 olindi, tokenni yangilash...');
		safeClearToken();

		const freshToken = typeof window.reauthWithTelegram === 'function'
			? await window.reauthWithTelegram(true)
			: null;
		if (freshToken) {
			return window.apiFetch(path, options, true);
		}

		const msg = 'Autentifikatsiya xatosi. Botni qayta oching.';
		showError(msg);
		throw new Error(msg);
	}

	if (!res.ok) {
		const msg = await parseErrorMessage(res);
		showError(msg);
		throw new Error(msg);
	}

	hideError();
	if (res.status === 204) return null;

	try {
		return await res.json();
	} catch (_) {
		return null;
	}
};
