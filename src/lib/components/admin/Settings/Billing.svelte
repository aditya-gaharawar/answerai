<script lang="ts">
	import { onMount } from 'svelte';
	import { accountRequest } from '$lib/apis/billing';
	let config: any;
	let live: any;
	let features: string[] = [];
	let credentials: Record<string, boolean> = {};
	let error = '';
	let message = '';
	let busy = false;
	let userId = '';
	let override = '';
	let until = '';
	let userPlan: any;
	const inputClass =
		'mt-1 w-full rounded-lg border border-gray-200 bg-transparent p-2 text-sm dark:border-gray-700';
	onMount(async () => {
		try {
			const [billing, calls] = await Promise.all([
				accountRequest('/billing/config'),
				accountRequest('/live/config')
			]);
			features = billing.feature_keys;
			credentials = billing.credentials;
			const { feature_keys, credentials: ignored, ...settings } = billing;
			config = settings;
			const { openai_key_configured, gemini_key_configured, ...liveSettings } = calls;
			live = liveSettings;
			credentials.OPENAI_REALTIME_API_KEY = openai_key_configured;
			credentials.GEMINI_LIVE_API_KEY = gemini_key_configured;
		} catch (e) {
			error = String(e);
		}
	});
	async function save() {
		busy = true;
		error = '';
		message = '';
		try {
			await accountRequest('/billing/config', config);
			await accountRequest('/live/config', live);
			message =
				'Plans, payment settings, and live providers saved. Refresh the app to update its controls.';
		} catch (e) {
			error = String(e);
		} finally {
			busy = false;
		}
	}
	async function updateOverride() {
		error = '';
		message = '';
		try {
			userPlan = await accountRequest(`/billing/users/${encodeURIComponent(userId.trim())}`, {
				plan: override,
				until: until ? Math.floor(new Date(until).getTime() / 1000) : 0
			});
			message = `Account plan is now ${userPlan.plan}.`;
		} catch (e) {
			error = String(e);
		}
	}
</script>

<div class="space-y-7 p-1">
	<h2 class="text-lg font-semibold">Plans, payments & live calls</h2>
	{#if error}<p class="text-sm text-red-500" role="alert">{error}</p>{/if}{#if message}<p
			class="text-sm text-green-600"
			role="status"
		>
			{message}
		</p>{/if}
	{#if config && live}
		<label class="flex items-center gap-3 font-medium"
			><input type="checkbox" bind:checked={config.enabled} />Enforce Free and Plus plans</label
		>
		<p class="text-xs text-gray-500">
			These limits apply to non-admin users alongside existing group permissions. A limit of zero
			disables usage. Model access lists use exact IDs; * allows all shared models. Live model IDs
			use live:openai/model or live:gemini/model.
		</p>
		<div class="grid gap-5 md:grid-cols-2">
			{#each ['free', 'plus'] as name}<fieldset
					class="space-y-3 rounded-xl border border-gray-200 p-4 dark:border-gray-800"
				>
					<legend class="px-2 font-semibold capitalize">{name} plan</legend
					>{#each [['messages_per_day', 'Generation requests per day'], ['requests_per_minute', 'Requests per minute'], ['live_minutes_per_day', 'Live minutes per day'], ['max_call_minutes', 'Maximum minutes per call']] as [key, label]}<label
							class="block text-sm"
							>{label}<input
								class={inputClass}
								type="number"
								min={key === 'max_call_minutes' ? 1 : 0}
								bind:value={config[name][key]}
							/></label
						>{/each}<label class="block text-sm"
						>Allowed model IDs (one per line)<textarea
							class={inputClass}
							rows="4"
							value={config[name].models.join('\n')}
							on:input={(event) => {
								config[name].models = event.currentTarget.value
									.split('\n')
									.map((value) => value.trim())
									.filter(Boolean);
								config = config;
							}}
						></textarea></label
					>
					<div class="space-y-2">
						{#each features as feature}<label class="flex gap-2 text-sm"
								><input
									type="checkbox"
									bind:checked={config[name].features[feature]}
								/>{feature.replaceAll('_', ' ')}</label
							>{/each}
					</div>
				</fieldset>{/each}
		</div>
		<fieldset class="space-y-3 rounded-xl border border-gray-200 p-4 dark:border-gray-800">
			<legend class="px-2 font-semibold">Daily feature limits</legend>
			<div class="grid gap-4 md:grid-cols-2">
				{#each ['free', 'plus'] as name}<div>
						<h3 class="mb-3 capitalize">{name}</h3>
						{#each features.filter((feature) => !feature.startsWith('live_')) as feature}<label
								class="mb-2 block text-xs"
								>{feature.replaceAll('_', ' ')}<input
									class={inputClass}
									type="number"
									min="0"
									max="1000000"
									bind:value={config[name].feature_limits[feature]}
								/></label
							>{/each}
					</div>{/each}
			</div>
		</fieldset>
		<fieldset class="space-y-4 rounded-xl border border-gray-200 p-4 dark:border-gray-800">
			<legend class="px-2 font-semibold">Payment gateways</legend><label class="block text-sm"
				>Public application URL<input
					class={inputClass}
					type="url"
					bind:value={config.public_url}
				/></label
			><label class="flex gap-2"
				><input type="checkbox" bind:checked={config.stripe_enabled} />Enable Stripe</label
			><label class="block text-sm"
				>Stripe recurring Price ID<input
					class={inputClass}
					bind:value={config.stripe_price_id}
					placeholder="price_…"
				/></label
			><label class="flex gap-2"
				><input type="checkbox" bind:checked={config.razorpay_enabled} />Enable Razorpay</label
			><label class="block text-sm"
				>Razorpay Plan ID<input
					class={inputClass}
					bind:value={config.razorpay_plan_id}
					placeholder="plan_…"
				/></label
			>
			<p class="text-xs text-gray-500">
				Checkout prices come from the selected gateway plan. Configure webhook delivery before
				enabling checkout.
			</p>
		</fieldset>
		<fieldset class="space-y-4 rounded-xl border border-gray-200 p-4 dark:border-gray-800">
			<legend class="px-2 font-semibold">Current call feature</legend><label class="flex gap-2"
				><input type="checkbox" bind:checked={live.enabled} />Enable live calls</label
			><label class="flex gap-2"
				><input type="checkbox" bind:checked={live.camera_enabled} />Allow camera frames</label
			><label class="block text-sm"
				>Default provider<select class={inputClass} bind:value={live.default_provider}
					><option value="openai">OpenAI Realtime</option><option value="gemini">Gemini Live</option
					></select
				></label
			>{#each ['openai', 'gemini'] as provider}<div class="space-y-2">
					<label class="flex gap-2"
						><input type="checkbox" bind:checked={live[`${provider}_enabled`]} />Enable {provider ===
						'openai'
							? 'OpenAI Realtime'
							: 'Gemini Live'}</label
					><label class="block text-sm"
						>Model<input class={inputClass} bind:value={live[`${provider}_model`]} /></label
					><label class="block text-sm"
						>Voice<input class={inputClass} bind:value={live[`${provider}_voice`]} /></label
					>
				</div>{/each}<label class="block text-sm"
				>Voice assistant instructions<textarea
					class={inputClass}
					rows="4"
					bind:value={live.instructions}
				></textarea></label
			>
		</fieldset>
		<div class="rounded-xl bg-gray-50 p-4 text-xs dark:bg-gray-900">
			<p class="mb-2 font-semibold">Server credential status</p>
			{#each Object.entries(credentials) as [key, ready]}<p class="mb-1">
					{key}: {ready ? 'Configured' : 'Missing'}
				</p>{/each}
			<p class="mt-2 text-gray-500">
				Set missing credentials in the server environment or .env, then restart. Secret values are
				never returned to the browser.
			</p>
		</div>
		<button
			class="rounded-xl bg-blue-600 px-5 py-2.5 text-white disabled:opacity-50"
			disabled={busy}
			on:click={save}>{busy ? 'Saving…' : 'Save settings'}</button
		>
		<fieldset class="space-y-3 rounded-xl border border-gray-200 p-4 dark:border-gray-800">
			<legend class="px-2 font-semibold">Individual account access</legend><label
				class="block text-sm">User ID<input class={inputClass} bind:value={userId} /></label
			><label class="block text-sm"
				>Plan override<select class={inputClass} bind:value={override}
					><option value="">Automatic (subscription or Free)</option><option value="free"
						>Free</option
					><option value="plus">Plus</option><option value="blocked"
						>Block paid and generation features</option
					></select
				></label
			><label class="block text-sm"
				>Expires (optional)<input
					class={inputClass}
					type="datetime-local"
					bind:value={until}
				/></label
			><button
				class="rounded-lg border px-4 py-2 text-sm"
				disabled={!userId.trim()}
				on:click={updateOverride}>Apply account access</button
			>
			<p class="text-xs text-gray-500">
				An override does not change payment collection. Cancel a subscription separately if needed.
			</p>
		</fieldset>
	{:else if !error}<p>Loading settings…</p>{/if}
</div>
