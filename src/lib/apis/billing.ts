import { WEBUI_API_BASE_URL } from '$lib/constants';

export async function accountRequest(path: string, body?: unknown) {
	const response = await fetch(`${WEBUI_API_BASE_URL}${path}`, {
		method: body === undefined ? 'GET' : 'POST',
		headers: { Authorization: `Bearer ${localStorage.token}`, 'Content-Type': 'application/json' },
		body: body === undefined ? undefined : JSON.stringify(body)
	});
	const result = await response.json().catch(() => ({}));
	if (!response.ok)
		throw new Error(
			typeof result.detail === 'string' ? result.detail : 'Request could not complete.'
		);
	return result;
}

let razorpayLoad: Promise<void> | undefined;
export async function openCheckout(result: any, finished: () => void) {
	if (result.url) {
		location.assign(result.url);
		return;
	}
	if (!razorpayLoad) {
		razorpayLoad = new Promise((resolve, reject) => {
			if ((window as any).Razorpay) {
				resolve();
				return;
			}
			const script = document.createElement('script');
			script.src = 'https://checkout.razorpay.com/v1/checkout.js';
			script.onload = () => resolve();
			script.onerror = () => {
				razorpayLoad = undefined;
				script.remove();
				reject(new Error('Razorpay checkout could not load.'));
			};
			document.head.appendChild(script);
		});
	}
	await razorpayLoad;
	const checkout = new (window as any).Razorpay({
		key: result.key_id,
		subscription_id: result.subscription_id,
		name: 'ANSWERAI Plus',
		description: 'ANSWERAI Plus subscription',
		prefill: { email: result.email, name: result.name },
		theme: { color: '#2563eb' },
		handler: finished,
		modal: { ondismiss: finished }
	});
	checkout.on('payment.failed', finished);
	checkout.open();
}
