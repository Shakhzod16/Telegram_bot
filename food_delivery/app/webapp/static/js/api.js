function buildHeaders(options) {
	const headers = Object.assign({}, (options && options.headers) || {});
	headers['Content-Type'] = headers['Content-Type'] || 'application/json';
	const token = sessionStorage.getItem('access_token');
	if (token) {
		headers['Authorization'] = 'Bearer ' + token;
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

	// Auth so'rovi tugashini kutamiz (auth/init bundan mustasno)
	if (!isAuthInit) {
		try {
			await (window.authReady || Promise.resolve());
		} catch (_) {}
	}

	const base = window.BACKEND_URL || '';
	const mergedOptions = Object.assign({}, options, { headers: buildHeaders(options) });

	let res;
	try {
		res = await fetch(base + path, mergedOptions);
	} catch (e) {
		const msg = 'Tarmoq xatosi. Internet aloqasini tekshiring.';
		showError(msg);
		throw new Error(msg);
	}

	// 401 → tokenni yangilash va bir marta qayta urinish
	if (!isAuthInit && res.status === 401 && !_retried) {
		console.warn('[api] 401 olindi, tokenni yangilash...');
		sessionStorage.removeItem('access_token');

		const freshToken = await window.reauthWithTelegram(true);
		if (freshToken) {
			// ✅ FIX: apiFetch ni rekursiv chaqiramiz (_retried=true bilan)
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
