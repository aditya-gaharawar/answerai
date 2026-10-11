<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { emailRequest } from '$lib/apis/auths/email';
	import { WEBUI_NAME } from '$lib/stores';

	const i18n: any = getContext('i18n');
	let token = '';
	let loaded = false;
	let busy = false;
	let verified = false;
	let error = '';
	let email = '';
	let requested = false;

	onMount(() => {
		token = new URLSearchParams(window.location.hash.slice(1)).get('token') ?? '';
		// Keep the secret out of browser history, referrers, and server access logs.
		window.history.replaceState(null, '', window.location.pathname);
		if (!token) error = 'This verification link is missing its token. Request a new email below.';
		loaded = true;
	});

	async function verify() {
		if (busy || !token) return;
		busy = true;
		error = '';
		try {
			await emailRequest('verify', { token });
			verified = true;
			token = '';
		} catch (err) {
			error = err instanceof Error ? err.message : String(err);
		} finally {
			busy = false;
		}
	}

	async function resend() {
		if (busy || requested) return;
		busy = true;
		try {
			await emailRequest('resend', { email });
			requested = true;
		} catch (err) {
			error = err instanceof Error ? err.message : String(err);
		} finally {
			busy = false;
		}
	}
</script>

<svelte:head>
	<title>{$i18n.t('Verify email')} · {$WEBUI_NAME}</title>
	<meta name="referrer" content="no-referrer" />
	<meta name="robots" content="noindex, nofollow" />
</svelte:head>

<main
	class="flex min-h-screen items-center justify-center bg-white px-6 text-gray-900 dark:bg-black dark:text-white"
>
	<div class="w-full max-w-md" aria-live="polite">
		<p class="mb-5 text-sm font-semibold tracking-wide">{$WEBUI_NAME}</p>
		{#if !loaded}
			<p>{$i18n.t('Loading…')}</p>
		{:else if verified}
			<h1 class="text-2xl font-semibold">{$i18n.t('Email verified')}</h1>
			<p class="mt-3 text-sm text-gray-500">
				{$i18n.t(
					'Your email is confirmed. Sign in to continue. Administrator approval and MFA may still be required.'
				)}
			</p>
			<a
				class="mt-6 inline-block rounded-xl bg-gray-900 px-5 py-3 text-white dark:bg-white dark:text-black"
				href="/auth?form=signin">{$i18n.t('Sign in')}</a
			>
		{:else}
			<h1 class="text-2xl font-semibold">{$i18n.t('Confirm your email address')}</h1>
			<p class="mt-3 text-sm text-gray-500">
				{$i18n.t('Select Verify email to finish confirming your ANSWERAI account.')}
			</p>
			{#if error}<p class="mt-4 text-sm text-red-600 dark:text-red-400" role="alert">
					{$i18n.t(error)}
				</p>{/if}
			{#if token && !error}
				<button
					class="mt-6 w-full rounded-xl bg-gray-900 px-5 py-3 text-white disabled:opacity-50 dark:bg-white dark:text-black"
					type="button"
					on:click={verify}
					disabled={busy}>{$i18n.t(busy ? 'Verifying…' : 'Verify email')}</button
				>
			{:else if requested}
				<p class="mt-6 text-sm">
					{$i18n.t(
						'If your account needs verification, a new link will be sent. Check your inbox and spam folder.'
					)}
				</p>
			{:else}
				<form class="mt-6 space-y-3" on:submit|preventDefault={resend}>
					<label class="block text-sm"
						>{$i18n.t('Email')}<input
							class="mt-2 w-full rounded-xl border border-gray-200 bg-transparent px-4 py-3 dark:border-gray-700"
							type="email"
							autocomplete="email"
							bind:value={email}
							required
							maxlength="320"
						/></label
					>
					<button
						class="w-full rounded-xl bg-gray-900 px-5 py-3 text-white disabled:opacity-50 dark:bg-white dark:text-black"
						type="submit"
						disabled={busy}
						>{$i18n.t(busy ? 'Sending…' : 'Request a new verification email')}</button
					>
				</form>
			{/if}
			<a class="mt-6 inline-block text-sm underline" href="/auth?form=signin"
				>{$i18n.t('Back to sign in')}</a
			>
		{/if}
	</div>
</main>
