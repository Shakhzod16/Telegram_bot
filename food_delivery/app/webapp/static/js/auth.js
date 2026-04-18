window.__authInFlight = null;
window.__authRetryTimer = null;
window.__authRetryCount = 0;

const ACCESS_TOKEN_KEY = 'access_token';
const TELEGRAM_INIT_DATA_KEY = 'tg_init_data';
let memoryAccessToken = null;
let memoryInitData = null;

function safeGetToken() {
	if (memoryAccessToken) return memoryAccessToken;
	try {
		const token = sessionStorage.getItem(ACCESS_TOKEN_KEY);
		if (token) {
			memoryAccessToken = token;
			return token;
		}
	} catch (_) {}
	try {
		const token = localStorage.getItem(ACCESS_TOKEN_KEY);
		if (token) {
			memoryAccessToken = token;
			return token;
		}
	} catch (_) {}
	return null;
}

function safeSetToken(token) {
	memoryAccessToken = token || null;
	try {
		if (token) sessionStorage.setItem(ACCESS_TOKEN_KEY, token);
		else sessionStorage.removeItem(ACCESS_TOKEN_KEY);
	} catch (_) {}
	try {
		if (token) localStorage.setItem(ACCESS_TOKEN_KEY, token);
		else localStorage.removeItem(ACCESS_TOKEN_KEY);
	} catch (_) {}
}

function safeClearToken() {
	safeSetToken(null);
}

function safeGetInitData() {
	if (memoryInitData) return memoryInitData;
	try {
		const v = sessionStorage.getItem(TELEGRAM_INIT_DATA_KEY);
		if (v) {
			memoryInitData = v;
			return v;
		}
	} catch (_) {}
	try {
		const v = localStorage.getItem(TELEGRAM_INIT_DATA_KEY);
		if (v) {
			memoryInitData = v;
			return v;
		}
	} catch (_) {}
	return null;
}

function safeSetInitData(initData) {
	memoryInitData = initData || null;
	try {
		if (initData) sessionStorage.setItem(TELEGRAM_INIT_DATA_KEY, initData);
		else sessionStorage.removeItem(TELEGRAM_INIT_DATA_KEY);
	} catch (_) {}
	try {
		if (initData) localStorage.setItem(TELEGRAM_INIT_DATA_KEY, initData);
		else localStorage.removeItem(TELEGRAM_INIT_DATA_KEY);
	} catch (_) {}
}

window.getAccessTokenSafe = safeGetToken;
window.setAccessTokenSafe = safeSetToken;
window.clearAccessTokenSafe = safeClearToken;
window.getTelegramInitDataSafe = safeGetInitData;
window.setTelegramInitDataSafe = safeSetInitData;

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

function generateInitDataFromFallbackUserId() {
	function normalizeUserId(raw) {
		const asNumber = Number(raw);
		if (!Number.isFinite(asNumber)) return null;
		return Math.trunc(asNumber);
	}

	function readUserIdFromRaw(raw) {
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
				const value = normalizeUserId((params.get(keys[i]) || '').trim());
				if (value !== null) return value;
			}
		} catch (_) {}
		return null;
	}

	let userId = null;
	if (typeof window.getTelegramUserIdSafe === 'function') {
		userId = normalizeUserId(window.getTelegramUserIdSafe());
	}
	if (userId === null) {
		userId = readUserIdFromRaw(window.location.search || '') || readUserIdFromRaw(window.location.hash || '');
	}
	if (userId === null) return null;

	if (typeof window.setTelegramUserIdSafe === 'function') {
		try {
			window.setTelegramUserIdSafe(String(userId));
		} catch (_) {}
	}

	try {
		return 'user=' + encodeURIComponent(JSON.stringify({ id: userId }));
	} catch (_) {
		return null;
	}
}

async function resolveTelegramInitData() {
	const tg = window.Telegram && window.Telegram.WebApp;
	if (!tg) return safeGetInitData();

	try {
		tg.ready();
	} catch (_) {}

	let initData = (tg.initData || '').trim();
	if (initData) {
		safeSetInitData(initData);
		return initData;
	}

	const launchData = readInitDataFromLaunchParams();
	if (launchData) {
		safeSetInitData(launchData);
		return launchData;
	}

	const queryData = readInitDataFromQuery();
	if (queryData) {
		safeSetInitData(queryData);
		return queryData;
	}

	const generatedFromFallbackUser = generateInitDataFromFallbackUserId();
	if (generatedFromFallbackUser) {
		safeSetInitData(generatedFromFallbackUser);
		return generatedFromFallbackUser;
	}

	for (let i = 0; i < 35; i += 1) {
		await delay(100);
		initData = (tg.initData || '').trim();
		if (initData) {
			safeSetInitData(initData);
			return initData;
		}
	}

	const unsafeUser = tg.initDataUnsafe && tg.initDataUnsafe.user;
	if (unsafeUser && unsafeUser.id) {
		try {
			const generated = 'user=' + encodeURIComponent(JSON.stringify(unsafeUser));
			safeSetInitData(generated);
			return generated;
		} catch (_) {
			return safeGetInitData();
		}
	}

	const generatedFromFallbackUserAfterWait = generateInitDataFromFallbackUserId();
	if (generatedFromFallbackUserAfterWait) {
		safeSetInitData(generatedFromFallbackUserAfterWait);
		return generatedFromFallbackUserAfterWait;
	}

	return safeGetInitData();
}

window.resolveTelegramInitData = resolveTelegramInitData;

async function performTelegramAuth() {
	const tg = window.Telegram && window.Telegram.WebApp;
	if (!tg) {
		console.warn('[auth] Telegram.WebApp topilmadi.');
		return null;
	}

	const initData = await resolveTelegramInitData();
	if (!initData) {
		console.warn('[auth] initData topilmadi.');
		return null;
	}

	const base = window.BACKEND_URL || '';
	const url = base + '/api/v1/auth/telegram/init';

	const res = await fetch(url, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			'X-Telegram-Init-Data': initData,
		},
		body: JSON.stringify({ init_data: initData }),
	});

	if (!res.ok) {
		let errMsg = 'Auth xatosi: ' + res.status;
		try {
			const errJson = await res.json();
			if (errJson && errJson.detail) errMsg = errJson.detail;
		} catch (_) {}
		console.error('[auth] /telegram/init xato:', errMsg);
		safeClearToken();
		return null;
	}

	const data = await res.json();
	if (data && data.access_token) {
		safeSetToken(data.access_token);
		window.__authRetryCount = 0;
		if (window.__authRetryTimer) {
			clearTimeout(window.__authRetryTimer);
			window.__authRetryTimer = null;
		}
		console.log('[auth] Token olindi va saqlandi.');
		return data.access_token;
	}

	console.error("[auth] Javobda access_token yo'q:", data);
	safeClearToken();
	return null;
}

function scheduleAuthRetry() {
	if (window.__authRetryTimer) return;
	if (window.__authRetryCount >= 8) return;

	window.__authRetryCount += 1;
	window.__authRetryTimer = setTimeout(async function () {
		window.__authRetryTimer = null;
		if (safeGetToken()) return;
		const token = await window.reauthWithTelegram(true);
		if (!token) scheduleAuthRetry();
	}, 1200);
}

window.reauthWithTelegram = async function reauthWithTelegram(force) {
	if (window.__authInFlight) {
		return window.__authInFlight;
	}

	const mustForce = !!force;
	const existing = safeGetToken();
	if (!mustForce && existing) {
		return existing;
	}

	window.__authInFlight = (async function () {
		try {
			const token = await performTelegramAuth();
			if (!token) scheduleAuthRetry();
			return token;
		} catch (e) {
			console.error('[auth] Tarmoq xatosi:', e);
			safeClearToken();
			scheduleAuthRetry();
			return null;
		} finally {
			window.__authInFlight = null;
		}
	})();

	return window.__authInFlight;
};

window.authReady = window.reauthWithTelegram(false);

window.addEventListener('focus', function () {
	if (!safeGetToken()) {
		window.reauthWithTelegram(false);
	}
});

document.addEventListener('visibilitychange', function () {
	if (document.visibilityState === 'visible' && !safeGetToken()) {
		window.reauthWithTelegram(false);
	}
});
