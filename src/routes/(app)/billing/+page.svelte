<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { accountRequest, openCheckout } from '$lib/apis/billing';
	let account: any;
	let plans: any;
	let error = '';
	let notice = '';
	let busy = false;
	let destroyed = false;
	let poll: ReturnType<typeof setInterval>;
	const labels: Record<string, string> = {
		uploads: 'File uploads',
		images: 'Image generation',
		web_search: 'Web search',
		code_interpreter: 'Code execution',
		tools: 'Tools and integrations',
		memory: 'Memory',
		automations: 'Automations',
		live_calls: 'Live voice calls',
		live_video: 'Live camera input',
		direct_connections: 'Personal model connections'
	};
	async function refresh() {
		try {
			const [nextAccount, nextPlans] = await Promise.all([
				accountRequest('/billing/me'),
				accountRequest('/billing/plans')
			]);
			if (!destroyed) {
				account = nextAccount;
				plans = nextPlans;
				error = '';
			}
		} catch (e) {
			if (!destroyed) error = e instanceof Error ? e.message : 'Billing could not load.';
		}
	}
	async function buy(provider: string) {
		busy = true;
		error = '';
		try {
			await openCheckout(await accountRequest('/billing/checkout', { provider }), () => {
				notice = 'Payment is being checked. Your plan updates after confirmation.';
				void refresh();
			});
		} catch (e) {
			error = e instanceof Error ? e.message : 'Checkout failed.';
		} finally {
			busy = false;
		}
	}
	async function manage(subscription: any, action: string) {
		busy = true;
		error = '';
		try {
			const result = await accountRequest(`/billing/subscriptions/${subscription.id}`, { action });
			if (result.url || result.subscription_id)
				await openCheckout(result, () => {
					notice = 'Waiting for payment confirmation.';
					void refresh();
				});
			else notice = result.message;
			await refresh();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Subscription could not update.';
		} finally {
			busy = false;
		}
	}
	onMount(() => {
		if (new URLSearchParams(location.search).get('checkout') === 'returned')
			notice =
				'Waiting for payment confirmation. Returning from checkout does not activate your plan.';
		void refresh();
		poll = setInterval(() => {
			void refresh();
		}, 15000);
	});
	onDestroy(() => {
		destroyed = true;
		clearInterval(poll);
	});
	function price(item: any) {
		return new Intl.NumberFormat(undefined, {
			style: 'currency',
			currency: item.currency.toUpperCase()
		}).format(
			item.amount /
				([
					'jpy',
					'krw',
					'vnd',
					'clp',
					'bif',
					'djf',
					'gnf',
					'kmf',
					'mga',
					'pyg',
					'rwf',
					'ugx',
					'vuv',
					'xaf',
					'xof',
					'xpf'
				].includes(item.currency.toLowerCase())
					? 1
					: 100)
		);
	}
</script>

<svelte:head><title>Plans · ANSWERAI</title></svelte:head>
<main class="mx-auto w-full max-w-5xl overflow-auto p-6 md:p-10">
	<div class="mb-8">
		<p class="text-sm text-blue-500">ANSWERAI membership</p>
		<h1 class="mt-2 text-3xl font-semibold">A plan for how you use AI</h1>
		<p class="mt-3 text-gray-500">Choose your model access, tools, and live voice experience.</p>
	</div>
	{#if error}<p
			class="mb-5 rounded-xl bg-red-50 p-4 text-sm text-red-600 dark:bg-red-950"
			role="alert"
		>
			{error}
		</p>{/if}
	{#if notice}<p
			class="mb-5 rounded-xl bg-blue-50 p-4 text-sm text-blue-700 dark:bg-blue-950 dark:text-blue-200"
			role="status"
		>
			{notice}
		</p>{/if}
	{#if account && plans}
		<div class="mb-7 rounded-2xl border border-gray-200 p-5 dark:border-gray-800">
			<p>
				Current plan: <strong class="capitalize">{account.plan}</strong>{!plans.enabled
					? ' · Plan enforcement is disabled'
					: ''}
			</p>
			<div class="mt-3 flex flex-wrap gap-5 text-sm text-gray-500">
				{#each account.usage.filter( (row: any) => ['messages', 'live_minutes'].includes(row.metric) ) as row}<span
						>{row.metric === 'messages' ? 'Messages' : 'Live minutes'}: {row.used} / {row.metric ===
						'messages'
							? account.entitlements.messages_per_day
							: account.entitlements.live_minutes_per_day} today · Resets {new Date(
							row.resets_at * 1000
						).toLocaleTimeString()}</span
					>{/each}
			</div>
		</div>
		<div class="grid gap-6 md:grid-cols-2">
			{#each ['free', 'plus'] as name}
				<section
					class="rounded-3xl border p-6 {name === 'plus'
						? 'border-blue-500 bg-blue-50/30 dark:bg-blue-950/20'
						: 'border-gray-200 dark:border-gray-800'}"
				>
					<h2 class="text-xl font-semibold">ANSWERAI {name === 'plus' ? 'Plus' : 'Free'}</h2>
					<p class="mt-3 text-sm text-gray-500">
						{name === 'plus'
							? 'More capacity and access to premium features.'
							: 'Start with the essentials.'}
					</p>
					<p class="mt-5 text-2xl font-semibold">
						{name === 'free' ? 'Free' : 'Provider-priced subscription'}
					</p>
					<ul class="mt-6 space-y-3 text-sm">
						<li>{plans[name].messages_per_day} generation requests per day</li>
						<li>{plans[name].requests_per_minute} requests per minute</li>
						<li>{plans[name].audio_requests_per_day} speech and transcription requests per day</li>
						<li>
							{plans[name].models.includes('*')
								? 'All models shared with your account'
								: `${plans[name].models.length} selected models`}
						</li>
						{#if plans[name].live_minutes_per_day}<li>
								{plans[name].live_minutes_per_day} live minutes per day
							</li>{/if}{#each Object.entries(plans[name].features).filter(([, enabled]) => enabled) as [feature]}<li
							>
								✓ {labels[feature] ?? feature}
							</li>{/each}
					</ul>
					{#if name === 'plus'}<div class="mt-7 space-y-3">
							{#each plans.prices as item}<button
									class="w-full rounded-xl bg-blue-600 px-4 py-3 text-white disabled:opacity-50"
									disabled={busy ||
										account.plan === 'plus' ||
										account.plan === 'admin' ||
										account.plan === 'blocked'}
									on:click={() => buy(item.provider)}
									>{price(item)} / {item.interval_count > 1
										? `${item.interval_count} `
										: ''}{item.interval} · {item.provider === 'stripe'
										? 'Stripe'
										: 'Razorpay'}</button
								>{/each}{#if !plans.prices.length}<p class="text-sm text-gray-500">
									Paid checkout is not available yet.
								</p>{/if}
						</div>{/if}
				</section>
			{/each}
		</div>
		{#if account.subscriptions.length}<section class="mt-8">
				<h2 class="mb-4 text-lg font-semibold">Your subscriptions</h2>
				{#each account.subscriptions as subscription}<div
						class="mb-3 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-gray-200 p-4 dark:border-gray-800"
					>
						<div>
							<p class="capitalize">{subscription.provider} · {subscription.status}</p>
							{#if subscription.period_end}<p class="mt-1 text-xs text-gray-500">
									{subscription.cancel_at_period_end ? 'Access until' : 'Paid through'}
									{new Date(subscription.period_end * 1000).toLocaleDateString()}
								</p>{/if}
						</div>
						<div class="flex gap-3 text-sm">
							{#if subscription.status === 'pending'}<button
									disabled={busy}
									on:click={() => manage(subscription, 'resume')}>Resume checkout</button
								><button disabled={busy} on:click={() => manage(subscription, 'abandon')}
									>Cancel checkout</button
								>{:else}{#if subscription.provider === 'stripe'}<button
										disabled={busy}
										on:click={() => manage(subscription, 'portal')}>Manage billing</button
									>{/if}{#if subscription.status === 'active' && !subscription.cancel_at_period_end}<button
										class="text-red-500"
										disabled={busy}
										on:click={() => {
											if (
												confirm(
													'Cancel subscription renewal? Your paid access remains until the period ends.'
												)
											)
												void manage(subscription, 'cancel');
										}}>Cancel renewal</button
									>{/if}{/if}
						</div>
					</div>{/each}
			</section>{/if}
	{:else if !error}<p role="status">Loading your plans…</p>{/if}
</main>
