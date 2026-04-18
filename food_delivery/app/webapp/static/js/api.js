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

const TELEGRAM_USER_ID_KEY = 'tg_user_id_fallback';
let memoryTelegramUserId = null;

function normalizeTelegramUserId(raw) {
	if (raw === undefined || raw === null) return null;
	const asNumber = Number(raw);
	if (!Number.isFinite(asNumber)) return null;
	return String(Math.trunc(asNumber));
}

function safeSetTelegramUserId(rawId) {
	const normalized = normalizeTelegramUserId(rawId);
	if (!normalized) return null;
	memoryTelegramUserId = normalized;
	try {
		sessionStorage.setItem(TELEGRAM_USER_ID_KEY, normalized);
	} catch (_) {}
	try {
		localStorage.setItem(TELEGRAM_USER_ID_KEY, normalized);
	} catch (_) {}
	return normalized;
}

function safeGetTelegramUserId() {
	if (memoryTelegramUserId) return memoryTelegramUserId;
	try {
		const sessionValue = sessionStorage.getItem(TELEGRAM_USER_ID_KEY);
		if (sessionValue) {
			memoryTelegramUserId = sessionValue;
			return sessionValue;
		}
	} catch (_) {}
	try {
		const localValue = localStorage.getItem(TELEGRAM_USER_ID_KEY);
		if (localValue) {
			memoryTelegramUserId = localValue;
			return localValue;
		}
	} catch (_) {}
	return null;
}

window.getTelegramUserIdSafe = safeGetTelegramUserId;
window.setTelegramUserIdSafe = safeSetTelegramUserId;

function readTelegramUserIdFromLaunchParams() {
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
			const keys = ['tg_user_id', 'tgUserId', 'telegram_id', 'user_id'];
			for (let i = 0; i < keys.length; i += 1) {
				const value = normalizeTelegramUserId((params.get(keys[i]) || '').trim());
				if (value) return value;
			}
		} catch (_) {}
		return null;
	}
	const fromQuery = extractFromRaw(window.location.search || '');
	if (fromQuery) return fromQuery;
	return extractFromRaw(window.location.hash || '');
}

function parseTelegramUserIdFromInitData(initData) {
	if (!initData) return null;
	try {
		const params = new URLSearchParams(String(initData));
		const rawUser = (params.get('user') || '').trim();
		if (!rawUser) return null;
		const parsedUser = JSON.parse(rawUser);
		return normalizeTelegramUserId(parsedUser && parsedUser.id);
	} catch (_) {
		return null;
	}
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
	return safeSetTelegramUserId(user.id);
}

function generatedInitDataFromUnsafeUser() {
	const tg = window.Telegram && window.Telegram.WebApp;
	let user = tg && tg.initDataUnsafe && tg.initDataUnsafe.user;
	if (!user || !normalizeTelegramUserId(user.id)) {
		const fallbackId = safeGetTelegramUserId();
		if (!fallbackId) return null;
		user = { id: Number(fallbackId) };
	}
	try {
		return 'user=' + encodeURIComponent(JSON.stringify(user));
	} catch (_) {
		return null;
	}
}

async function resolveTelegramUserIdForHeader() {
	const fromLaunch = readTelegramUserIdFromLaunchParams();
	if (fromLaunch) return safeSetTelegramUserId(fromLaunch);

	const direct = readTelegramUserIdFast();
	if (direct) return direct;

	const fromInitData = parseTelegramUserIdFromInitData(readInitDataFast());
	if (fromInitData) return safeSetTelegramUserId(fromInitData);

	if (typeof window.getTelegramInitDataSafe === 'function') {
		const storedInitData = window.getTelegramInitDataSafe();
		const fromStoredInitData = parseTelegramUserIdFromInitData(storedInitData);
		if (fromStoredInitData) return safeSetTelegramUserId(fromStoredInitData);
	}

	for (let i = 0; i < 15; i += 1) {
		await delay(80);
		const delayed = readTelegramUserIdFast();
		if (delayed) return delayed;

		const delayedFromInitData = parseTelegramUserIdFromInitData(readInitDataFast());
		if (delayedFromInitData) return safeSetTelegramUserId(delayedFromInitData);
	}
	return safeGetTelegramUserId();
}

safeSetTelegramUserId(readTelegramUserIdFromLaunchParams());

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

	// Fallback for clients where initData is unavailable.
	// We resolve Telegram user id from initDataUnsafe, URL params, or stored fallback.
	if (!headers['X-Telegram-Id']) {
		const tgUserId = await resolveTelegramUserIdForHeader();
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
