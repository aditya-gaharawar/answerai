<script lang="ts">
	import { getContext, onDestroy, onMount } from 'svelte';
	import { emailRequest, type EmailVerificationStep } from '$lib/apis/auths/email';
	import { toast } from 'svelte-sonner';

	export let step: EmailVerificationStep;
	export let onCancel: () => void;
	const i18n: any = getContext('i18n');
	let address = step.email;
	let busy = false;
	let remaining = step.email_sent ? step.resend_after : 0;
	let interval: ReturnType<typeof setInterval> | undefined;
	let message = step.email_sent
		? 'We sent you a verification link. Check your inbox and spam folder.'
		: 'Your email needs verification. Request a link below to finish signing up.';

	function startCountdown(seconds: number) {
		remaining = seconds;
		if (interval) clearInterval(interval);
		interval = setInterval(() => {
			remaining = Math.max(0, remaining - 1);
			if (!remaining && interval) clearInterval(interval);
		}, 1000);
	}
	onMount(() => {
		if (remaining) startCountdown(remaining);
	});
	onDestroy(() => interval && clearInterval(interval));

	async function resend() {
		if (busy || remaining) return;
		busy = true;
		try {
			const result = await emailRequest('resend', { email: address });
			message = result.message;
			startCountdown(result.resend_after);
			toast.success($i18n.t('Verification email requested.'));
		} catch (error) {
			toast.error(error instanceof Error ? error.message : String(error));
		} finally {
			busy = false;
		}
	}
</script>

<div class="my-auto mx-auto w-full max-w-md text-left" aria-live="polite">
	<h1 class="text-2xl font-semibold">{$i18n.t('Verify your email')}</h1>
	<p class="mt-3 text-sm text-gray-600 dark:text-gray-400">{$i18n.t(message)}</p>
	<form class="mt-6 space-y-4" on:submit|preventDefault={resend}>
		<label class="block text-sm">
			{$i18n.t('Email')}
			<input
				class="mt-2 w-full rounded-xl border border-gray-200 bg-transparent px-4 py-3 dark:border-gray-700"
				type="email"
				autocomplete="email"
				bind:value={address}
				required
				maxlength="320"
				disabled={busy}
			/>
		</label>
		<button
			type="submit"
			disabled={busy || remaining > 0}
			class="w-full rounded-xl bg-gray-900 px-4 py-3 text-sm font-medium text-white disabled:opacity-50 dark:bg-white dark:text-black"
		>
			{#if busy}{$i18n.t('Sending…')}{:else if remaining > 0}
				{$i18n.t('Resend in {{seconds}}s', { seconds: remaining })}
			{:else}{$i18n.t('Resend verification email')}{/if}
		</button>
	</form>
	<p class="mt-4 text-xs text-gray-500">
		{$i18n.t('Only the newest link works. After verification, return here and sign in.')}
	</p>
	<button class="mt-6 text-sm underline" type="button" on:click={onCancel}>
		{$i18n.t('Back to sign in')}
	</button>
</div>
