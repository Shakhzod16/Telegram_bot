window.__authInFlight = null;

window.reauthWithTelegram = async function reauthWithTelegram(force) {
	// Agar allaqachon so'rov ketayotgan bo'lsa, uni kutish
	if (window.__authInFlight) {
		return window.__authInFlight;
	}

	const mustForce = !!force;
	const existing = sessionStorage.getItem('access_token');
	if (!mustForce && existing) {
		return existing;
	}

	const tg = window.Telegram && window.Telegram.WebApp;

	// initData yo'q bo'lsa — bu Telegram ichida emas (browser test)
	if (!tg || !tg.initData) {
		console.warn('[auth] Telegram.WebApp.initData mavjud emas. Browser da ochilganmi?');
		return null;
	}

	window.__authInFlight = (async function () {
		try {
			const base = window.BACKEND_URL || '';
			const url = base + '/api/v1/auth/telegram/init';

			const res = await fetch(url, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ init_data: tg.initData }),
			});

			if (!res.ok) {
				let errMsg = 'Auth xatosi: ' + res.status;
				try {
					const errJson = await res.json();
					if (errJson && errJson.detail) errMsg = errJson.detail;
				} catch (_) {}
				console.error('[auth] /telegram/init xato:', errMsg);
				sessionStorage.removeItem('access_token');
				return null;
			}

			const data = await res.json();
			if (data && data.access_token) {
				sessionStorage.setItem('access_token', data.access_token);
				console.log('[auth] Token olindi va saqlandi.');
				return data.access_token;
			}

			console.error("[auth] Javobda access_token yo'q:", data);
			sessionStorage.removeItem('access_token');
			return null;
		} catch (e) {
			console.error('[auth] Tarmoq xatosi:', e);
			sessionStorage.removeItem('access_token');
			return null;
		} finally {
			window.__authInFlight = null;
		}
	})();

	return window.__authInFlight;
};

// Sahifa yuklanganda darhol auth boshlash
window.authReady = window.reauthWithTelegram(false);
