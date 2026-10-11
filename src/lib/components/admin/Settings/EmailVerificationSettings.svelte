<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { emailRequest, type EmailSettings } from '$lib/apis/auths/email';
	import Switch from '$lib/components/common/Switch.svelte';
	import AdminSettingSection from './AdminSettingSection.svelte';
	import AdminSettingRow from './AdminSettingRow.svelte';

	const i18n: any = getContext('i18n');
	let settings: EmailSettings | null = null;
	let password = '';
	let clearPassword = false;
	let busy = false;
	let loadError = '';
	const inputClass =
		'mt-1 w-full rounded-lg border border-gray-200 bg-transparent px-3 py-2 text-xs dark:border-gray-700';

	onMount(async () => {
		try {
			settings = await emailRequest('config', undefined, localStorage.token);
		} catch (error) {
			loadError = error instanceof Error ? error.message : String(error);
		}
	});

	export async function save(): Promise<boolean> {
		if (!settings || busy) return false;
		busy = true;
		try {
			const { password_configured, ...values } = settings;
			settings = await emailRequest(
				'config',
				{
					...values,
					smtp_password: password || null,
					clear_password: clearPassword
				},
				localStorage.token
			);
			password = '';
			clearPassword = false;
			return true;
		} catch (error) {
			toast.error(error instanceof Error ? error.message : String(error));
			return false;
		} finally {
			busy = false;
		}
	}

	async function testDelivery() {
		if (busy || !(await save())) return;
		busy = true;
		try {
			const result = await emailRequest('test', {}, localStorage.token);
			toast.success($i18n.t(result.message));
		} catch (error) {
			toast.error(error instanceof Error ? error.message : String(error));
		} finally {
			busy = false;
		}
	}
</script>

<AdminSettingSection title={$i18n.t('Email verification')}>
	{#if loadError}<p role="alert" class="text-xs text-red-600">{loadError}</p>
	{:else if settings}
		<AdminSettingRow label={$i18n.t('Require email verification for new signups')}>
			<Switch
				bind:state={settings.enabled}
				ariaLabel={$i18n.t('Require email verification for new signups')}
			/>
		</AdminSettingRow>
		<p class="text-xs text-gray-500">
			{$i18n.t(
				'New password accounts must verify their email before signing in. Existing accounts keep access. Accounts already awaiting verification must still verify when this setting is disabled.'
			)}
		</p>
		<fieldset disabled={busy} class="mt-4 grid gap-3 sm:grid-cols-2">
			<label class="text-xs"
				>{$i18n.t('SMTP host')}<input
					class={inputClass}
					type="text"
					bind:value={settings.smtp_host}
					placeholder="smtp.example.com"
					autocomplete="off"
					maxlength="255"
				/></label
			>
			<label class="text-xs"
				>{$i18n.t('SMTP port')}<input
					class={inputClass}
					type="number"
					min="1"
					max="65535"
					bind:value={settings.smtp_port}
				/></label
			>
			<label class="text-xs"
				>{$i18n.t('Connection security')}<select
					class={inputClass}
					bind:value={settings.smtp_security}
					><option value="starttls">STARTTLS (587)</option><option value="ssl">TLS (465)</option
					></select
				></label
			>
			<label class="text-xs"
				>{$i18n.t('SMTP username')}<input
					class={inputClass}
					type="text"
					bind:value={settings.smtp_username}
					autocomplete="off"
					maxlength="320"
				/></label
			>
			<label class="text-xs sm:col-span-2"
				>{$i18n.t('SMTP password')}<input
					class={inputClass}
					type="password"
					bind:value={password}
					autocomplete="new-password"
					placeholder={$i18n.t(
						settings.password_configured
							? 'Password configured. Leave blank to keep it.'
							: 'Enter your SMTP password or app password'
					)}
				/></label
			>
			{#if settings.password_configured}<label class="flex items-center gap-2 text-xs sm:col-span-2"
					><input type="checkbox" bind:checked={clearPassword} />{$i18n.t(
						'Clear the configured SMTP password'
					)}</label
				>{/if}
			<label class="text-xs"
				>{$i18n.t('Sender email')}<input
					class={inputClass}
					type="email"
					bind:value={settings.from_email}
					placeholder="noreply@answerai.in"
					maxlength="320"
				/></label
			>
			<label class="text-xs"
				>{$i18n.t('Sender name')}<input
					class={inputClass}
					type="text"
					bind:value={settings.from_name}
					maxlength="100"
				/></label
			>
			<label class="text-xs sm:col-span-2"
				>{$i18n.t('Public application URL')}<input
					class={inputClass}
					type="url"
					bind:value={settings.public_url}
					placeholder="https://answerai.in"
				/></label
			>
			<label class="text-xs"
				>{$i18n.t('Link expiry (seconds)')}<input
					class={inputClass}
					type="number"
					min="300"
					max="86400"
					bind:value={settings.token_ttl_seconds}
				/></label
			>
			<label class="text-xs"
				>{$i18n.t('Resend cooldown (seconds)')}<input
					class={inputClass}
					type="number"
					min="60"
					max="3600"
					bind:value={settings.resend_cooldown_seconds}
				/></label
			>
		</fieldset>
		<button
			type="button"
			class="mt-4 rounded-lg border border-gray-200 px-3 py-2 text-xs disabled:opacity-50 dark:border-gray-700"
			disabled={busy}
			on:click={testDelivery}>{$i18n.t(busy ? 'Sending…' : 'Save and send test email')}</button
		>
		<p class="mt-2 text-xs text-gray-500">
			{$i18n.t(
				'The test goes to your administrator email. Use the Save button below to save all authentication settings.'
			)}
		</p>
	{:else}<p class="text-xs text-gray-500">{$i18n.t('Loading email settings…')}</p>{/if}
</AdminSettingSection>
