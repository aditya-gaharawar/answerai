<script lang="ts">
	import { onMount } from 'svelte';
	import { accountRequest } from '$lib/apis/billing';
	let policy: any;
	let overview: any;
	let account: any;
	let actions: any[] = [];
	let identifier = '';
	let reason = '';
	let error = '';
	let message = '';
	let busy = false;
	let providerNames = '';
	let origins = '';
	const field =
		'mt-1 w-full rounded-lg border border-gray-200 bg-transparent p-2 text-sm dark:border-gray-700';
	async function refresh() {
		const [nextPolicy, nextOverview, nextActions] = await Promise.all([
			accountRequest('/admin/controls/policy'),
			accountRequest('/admin/controls/overview'),
			accountRequest('/admin/controls/actions')
		]);
		policy = nextPolicy;
		overview = nextOverview;
		actions = nextActions;
		providerNames = policy.trusted_oauth_email_providers.join(', ');
		origins = policy.allowed_cookie_origins.join('\n');
	}
	onMount(() => {
		void refresh().catch((e) => {
			error = String(e);
		});
	});
	async function perform(work: () => Promise<void>) {
		busy = true;
		error = '';
		message = '';
		try {
			await work();
		} catch (e) {
			error = String(e);
		} finally {
			busy = false;
		}
	}
	async function lookup() {
		await perform(async () => {
			account = await accountRequest(
				`/admin/controls/accounts/${encodeURIComponent(identifier.trim())}`
			);
		});
	}
	async function savePolicy() {
		await perform(async () => {
			policy.trusted_oauth_email_providers = providerNames
				.split(',')
				.map((value) => value.trim())
				.filter(Boolean);
			policy.allowed_cookie_origins = origins
				.split('\n')
				.map((value) => value.trim())
				.filter(Boolean);
			await accountRequest('/admin/controls/policy', policy);
			await refresh();
			message = 'Security policy saved.';
		});
	}
	async function control(action: string, label: string) {
		if (!account || !confirm(`${label} for ${account.email}?`)) return;
		await perform(async () => {
			const result = await accountRequest(`/admin/controls/accounts/${account.id}/actions`, {
				action,
				reason
			});
			account = result.account;
			await refresh();
			message = result.message;
		});
	}
	async function reconcile(id: string) {
		await perform(async () => {
			account = await accountRequest(`/admin/controls/subscriptions/${id}/reconcile`, {});
			await refresh();
			message = 'Current provider state verified.';
		});
	}
</script>

<section class="space-y-5 rounded-xl border border-gray-200 p-4 dark:border-gray-800">
	<h3 class="font-semibold">Security & account operations</h3>
	{#if error}<p class="text-sm text-red-500" role="alert">{error}</p>{/if}
	{#if message}<p class="text-sm text-green-600" role="status">{message}</p>{/if}
	{#if policy}
		{#if overview}<div class="flex flex-wrap gap-4 text-xs text-gray-500">
				<span>{overview.active_calls} active calls</span><span
					>{overview.active_subscriptions} paid subscriptions</span
				><span>{overview.verified_webhook_events} verified webhook events</span>
			</div>{/if}
		<label class="block text-sm"
			>Maximum request body (MiB)<input
				class={field}
				type="number"
				min="1"
				max="1024"
				bind:value={policy.max_request_mib}
			/></label
		>
		<label class="flex gap-2 text-sm"
			><input type="checkbox" bind:checked={policy.allow_user_python_tools} />Allow trusted users
			with tool-authoring permissions to run server Python</label
		>
		<p class="text-xs text-gray-500">
			Python tools run with the server's privileges. Leave this off for ordinary users; they can
			still use curated tools shared with them.
		</p>
		<label class="block text-sm"
			>Trusted OAuth email providers (comma-separated IDs)<input
				class={field}
				bind:value={providerNames}
				placeholder="For managed identity providers only"
			/></label
		>
		<p class="text-xs text-gray-500">
			Only list providers that enforce ownership of email addresses but omit the verified-email
			claim. An explicit unverified claim is always rejected for linking.
		</p>
		<label class="block text-sm"
			>Additional trusted cookie origins (one exact URL per line)<textarea
				class={field}
				rows="2"
				bind:value={origins}
				placeholder="https://your-owned-frontend.example"
			></textarea></label
		>
		<p class="text-xs text-gray-500">
			The current application origin and explicit CORS origins are trusted automatically. Wildcards
			and opaque origins cannot authorize cookie-authenticated changes.
		</p>
		<button
			class="rounded-lg bg-blue-600 px-4 py-2 text-sm text-white"
			disabled={busy}
			on:click={savePolicy}>Save security policy</button
		>
		<hr class="border-gray-200 dark:border-gray-800" />
		<label class="block text-sm"
			>Account email or user ID<input class={field} bind:value={identifier} /></label
		>
		<button
			class="rounded-lg border px-4 py-2 text-sm"
			disabled={busy || !identifier.trim()}
			on:click={lookup}>Inspect account</button
		>
		{#if account}
			<div class="rounded-lg bg-gray-50 p-3 text-sm dark:bg-gray-900">
				<strong>{account.name}</strong>
				<p>{account.email}</p>
				<p class="mt-2">
					{account.plan} · Login {account.login_enabled ? 'enabled' : 'disabled'} · Email {account.email_verified
						? 'verified'
						: 'awaiting verification'} · Call {account.active_call ? 'active' : 'inactive'}
				</p>
			</div>
			<label class="block text-sm"
				>Reason for the account action<input
					class={field}
					bind:value={reason}
					maxlength="500"
					placeholder="Record the reason; exclude credentials"
				/></label
			>
			<div class="flex flex-wrap gap-2">
				{#each [['reset_usage', 'Reset usage'], ['stop_call', 'End active call'], ['revoke_sessions', 'Revoke sign-in sessions'], [account.login_enabled ? 'disable_login' : 'enable_login', account.login_enabled ? 'Disable login' : 'Enable login']] as [action, label]}<button
						class="rounded-lg border px-3 py-2 text-xs"
						disabled={busy ||
							reason.trim().length < 3 ||
							(account.role === 'admin' && !['stop_call', 'reset_usage'].includes(action))}
						on:click={() => control(action, label)}>{label}</button
					>{/each}
			</div>
			<p class="text-xs text-gray-500">
				Calls stop on the next authorization check, within five seconds. Login changes do not cancel
				billing. Session revocation removes app sign-in/refresh sessions; API keys remain valid
				until login is disabled or the keys are deleted.
			</p>
			{#if account.usage.length}<ul class="space-y-1 text-xs">
					{#each account.usage as entry}<li>
							{entry.metric}: {entry.used} · Resets {new Date(
								entry.resets_at * 1000
							).toLocaleString()}
						</li>{/each}
				</ul>{/if}
			{#each account.subscriptions as subscription}<div
					class="flex flex-wrap items-center justify-between gap-2 rounded-lg border p-3 text-xs"
				>
					<span
						>{subscription.provider} · {subscription.status}
						{subscription.period_end
							? `· Paid through ${new Date(subscription.period_end * 1000).toLocaleDateString()}`
							: ''}</span
					><button
						class="rounded border px-2 py-1"
						disabled={busy}
						on:click={() => reconcile(subscription.id)}>Verify provider state</button
					>
				</div>{/each}
		{/if}
		<details>
			<summary class="cursor-pointer text-sm font-medium">Recent administrator actions</summary>
			<div class="mt-3 max-h-64 space-y-2 overflow-auto">
				{#each actions as action}<div class="rounded-lg bg-gray-50 p-3 text-xs dark:bg-gray-900">
						<p>{new Date(action.created_at * 1000).toLocaleString()} · {action.action}</p>
						<p class="text-gray-500">
							Actor: {action.actor_id} · Account: {action.target_id ?? 'system'}
						</p>
						{#if action.details.reason}<p class="mt-1">{action.details.reason}</p>{/if}
					</div>{/each}
			</div>
		</details>
	{:else}<p class="text-sm">Loading security controls…</p>{/if}
</section>
