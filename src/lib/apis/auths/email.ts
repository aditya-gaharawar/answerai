import { WEBUI_API_BASE_URL } from '$lib/constants';

export type EmailVerificationStep = {
	next_step: 'verify_email';
	email: string;
	email_sent: boolean;
	resend_after: number;
};

export type EmailSettings = {
	enabled: boolean;
	smtp_host: string;
	smtp_port: number;
	smtp_security: 'starttls' | 'ssl';
	smtp_username: string;
	smtp_password?: string | null;
	password_configured?: boolean;
	clear_password?: boolean;
	from_email: string;
	from_name: string;
	public_url: string;
	token_ttl_seconds: number;
	resend_cooldown_seconds: number;
};

export async function emailRequest(
	path: 'verify' | 'resend' | 'config' | 'test',
	body?: Record<string, unknown>,
	token?: string
) {
	const response = await fetch(`${WEBUI_API_BASE_URL}/auths/email/${path}`, {
		method: path === 'config' && !body ? 'GET' : 'POST',
		credentials: 'include',
		cache: 'no-store',
		headers: {
			'Content-Type': 'application/json',
			...(token ? { Authorization: `Bearer ${token}` } : {})
		},
		...(body ? { body: JSON.stringify(body) } : {})
	});
	const result = await response.json();
	if (!response.ok) {
		throw new Error(
			typeof result.detail === 'string'
				? result.detail
				: 'The request could not be completed. Check your details and try again.'
		);
	}
	return result;
}
