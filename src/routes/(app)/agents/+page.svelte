<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { models, config } from '$lib/stores';
	import { accountRequest } from '$lib/apis/billing';
	type Run = {
		id: string;
		chat_id: string;
		status: string;
		model_id: string;
		prompt: string;
		created_at: number;
		updated_at: number;
		deadline: number;
		token_budget: number;
		tokens_used: number;
		timeline: { sequence: number; at: number; type: string; tool?: string; duration_ms?: number }[];
		checkpoint: { phase?: string; message?: string; prompt?: string };
	};
	let runs: Run[] = [];
	let objective = '';
	let webSearch = false;
	let tokenBudget = 256000;
	let refreshing = false;
	let since = 0;
	let model = '';
	let error = '';
	let busy = false;
	let mounted = true;
	let timer: ReturnType<typeof setInterval>;
	let requestKey = crypto.randomUUID();
	async function refresh() {
		if (refreshing) return;
		refreshing = true;
		try {
			const next: Run[] = await accountRequest(`/agent-runs/?since=${since}`);
			if (mounted) {
				const merged = new Map(runs.map((run) => [run.id, run]));
				next.forEach((run) => merged.set(run.id, run));
				runs = [...merged.values()].sort((a, b) => b.created_at - a.created_at).slice(0, 100);
				since = Math.max(since, ...next.map((run) => Math.max(0, run.updated_at - 1)));
			}
		} catch (e) {
			if (mounted) error = String(e);
		} finally {
			refreshing = false;
		}
	}
	async function create() {
		busy = true;
		error = '';
		try {
			await accountRequest('/agent-runs/', {
				objective,
				model_id: model,
				request_key: requestKey,
				web_search: webSearch,
				token_budget: tokenBudget,
				max_seconds: 300,
				max_iterations: 12
			});
			objective = '';
			requestKey = crypto.randomUUID();
			await refresh();
		} catch (e) {
			error = String(e);
		} finally {
			busy = false;
		}
	}
	async function action(run: Run, name: string) {
		busy = true;
		try {
			await accountRequest(`/agent-runs/${run.id}/${name}`, {});
			await refresh();
		} catch (e) {
			error = String(e);
		} finally {
			busy = false;
		}
	}
	onMount(() => {
		model = $models[0]?.id ?? '';
		webSearch = !!$config?.features?.enable_web_search;
		void refresh();
		timer = setInterval(() => {
			if (!document.hidden) void refresh();
		}, 3000);
	});
	onDestroy(() => {
		mounted = false;
		clearInterval(timer);
	});
</script>

<svelte:head><title>Agent tasks · ANSWERAI</title></svelte:head>
<section
	aria-label="Agent executions"
	class="mx-auto w-full max-w-5xl px-5 pb-20 pt-8 text-gray-950 dark:text-gray-100 sm:px-10 sm:pt-12"
>
	<a
		href="/"
		class="inline-flex items-center gap-2 text-sm text-gray-500 transition hover:text-gray-950 dark:hover:text-white"
		><span aria-hidden="true">←</span> Back to chat</a
	>
	<header class="mt-9 border-b border-gray-200 pb-8 dark:border-gray-800 sm:mt-12">
		<div class="flex flex-wrap items-center gap-3">
			<span
				class="rounded-md border border-gray-200 px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-gray-500 dark:border-gray-700"
				>AnswerAI / Agents</span
			><span class="flex items-center gap-1.5 text-xs text-gray-500"
				><span class="h-1.5 w-1.5 rounded-full bg-emerald-500"></span> Background tasks</span
			>
		</div>
		<h1 class="mt-5 text-3xl font-semibold tracking-tight sm:text-4xl">Background agent tasks</h1>
		<p class="mt-3 max-w-2xl text-sm leading-6 text-gray-500 dark:text-gray-400">
			Give your agent an objective and follow its progress, even after you leave this page.
		</p>
	</header>
	{#if error}<p
			role="alert"
			class="mt-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/40 dark:text-red-300"
		>
			{error}
		</p>{/if}
	<div class="mt-9 grid gap-8 lg:grid-cols-[minmax(0,1fr)_240px] lg:gap-12">
		<form on:submit|preventDefault={create} class="min-w-0">
			<div class="flex items-start justify-between gap-4">
				<div>
					<h2 class="text-base font-semibold tracking-tight">New task</h2>
					<p class="mt-1 text-sm text-gray-500">Describe what you want the agent to investigate.</p>
				</div>
				<span
					class="shrink-0 rounded-full border border-gray-200 px-2.5 py-1 text-xs text-gray-500 dark:border-gray-700"
					>Read-only</span
				>
			</div>
			<label class="mt-6 block text-sm font-medium"
				>Objective<textarea
					class="mt-2 min-h-36 w-full resize-y rounded-lg border border-gray-200 bg-white p-4 text-sm leading-6 outline-none transition placeholder:text-gray-400 focus:border-gray-500 focus:ring-2 focus:ring-gray-200 disabled:opacity-60 dark:border-gray-700 dark:bg-gray-900 dark:focus:ring-gray-700"
					bind:value={objective}
					disabled={busy}
					on:input={() => (requestKey = crypto.randomUUID())}
					maxlength="16000"
					required
					rows="4"
					placeholder="e.g. Research the latest developments in AI agents and summarize the key findings."
				></textarea></label
			>
			<div class="mt-5 grid gap-4 sm:grid-cols-2">
				<label class="block text-sm font-medium"
					>Model<select
						aria-label="Model"
						class="mt-2 h-10 w-full rounded-lg border border-gray-200 bg-white px-3 text-sm font-normal outline-none focus:border-gray-500 dark:border-gray-700 dark:bg-gray-900"
						bind:value={model}
						required
						>{#each $models as item}<option value={item.id}>{item.name ?? item.id}</option
							>{/each}</select
					></label
				>
				<label class="block text-sm font-medium"
					>Maximum execution credits<select
						aria-label="Maximum execution credits"
						class="mt-2 h-10 w-full rounded-lg border border-gray-200 bg-white px-3 text-sm font-normal outline-none focus:border-gray-500 dark:border-gray-700 dark:bg-gray-900"
						bind:value={tokenBudget}
						disabled={busy}
						><option value={64000}>64,000 credits</option><option value={256000}
							>256,000 credits</option
						><option value={500000}>500,000 credits</option></select
					></label
				>
			</div>
			<label
				class="mt-5 flex cursor-pointer items-start gap-3 rounded-lg border border-gray-200 px-4 py-3 dark:border-gray-800"
				><input
					class="mt-1 accent-black dark:accent-white"
					type="checkbox"
					bind:checked={webSearch}
					disabled={!$config?.features?.enable_web_search || busy}
					aria-label="Web research"
				/><span
					><span class="block text-sm font-medium">Web research</span><span
						class="mt-0.5 block text-xs leading-5 text-gray-500"
						>Search the web for current sources when available.</span
					></span
				></label
			>
			<div class="mt-6 flex flex-wrap items-center justify-between gap-4">
				<p class="text-xs leading-5 text-gray-500">
					Up to 5 minutes · 12 tool iterations · Quotas apply
				</p>
				<button
					class="inline-flex h-10 items-center justify-center gap-2 rounded-lg bg-gray-950 px-4 text-sm font-medium text-white transition hover:bg-gray-700 disabled:cursor-not-allowed disabled:opacity-40 dark:bg-white dark:text-gray-950 dark:hover:bg-gray-200"
					disabled={busy || !model || !objective.trim()}
					>Start research <span aria-hidden="true">↗</span></button
				>
			</div>
		</form>
		<aside
			class="rounded-xl border border-gray-200 bg-gray-50/60 p-5 dark:border-gray-800 dark:bg-gray-900/50"
		>
			<p class="text-xs font-semibold uppercase tracking-widest text-gray-500">How it works</p>
			<ol class="mt-5 space-y-5 text-sm">
				<li class="flex gap-3">
					<span class="shrink-0 whitespace-nowrap font-mono text-xs text-gray-400">01</span><span
						><strong class="font-medium">Set an objective</strong><span
							class="mt-1 block text-xs leading-5 text-gray-500"
							>Choose a model and the resources available for your task.</span
						></span
					>
				</li>
				<li class="flex gap-3">
					<span class="shrink-0 whitespace-nowrap font-mono text-xs text-gray-400">02</span><span
						><strong class="font-medium">Follow along</strong><span
							class="mt-1 block text-xs leading-5 text-gray-500"
							>Review activity as your agent works in the background.</span
						></span
					>
				</li>
				<li class="flex gap-3">
					<span class="shrink-0 whitespace-nowrap font-mono text-xs text-gray-400">03</span><span
						><strong class="font-medium">Review the result</strong><span
							class="mt-1 block text-xs leading-5 text-gray-500"
							>Check the conversation before marking a task complete.</span
						></span
					>
				</li>
			</ol>
			<p
				class="mt-6 border-t border-gray-200 pt-4 text-xs leading-5 text-gray-500 dark:border-gray-800"
			>
				Background tasks use read-only tools. Actions and connectors are available in chat.
			</p>
		</aside>
	</div>
	<section
		class="mt-14 border-t border-gray-200 pt-8 dark:border-gray-800"
		aria-label="Execution history"
	>
		<div class="mb-5 flex items-end justify-between gap-3">
			<div>
				<h2 class="text-base font-semibold tracking-tight">Recent tasks</h2>
				<p class="mt-1 text-sm text-gray-500">Your execution history and activity.</p>
			</div>
			<span class="text-xs text-gray-400">{runs.length} {runs.length === 1 ? 'task' : 'tasks'}</span
			>
		</div>
		<div class="space-y-3">
			{#each runs as run}<article
					class="overflow-hidden rounded-xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900/30"
				>
					<div class="p-5 sm:p-6">
						<div class="flex flex-wrap items-start justify-between gap-3">
							<div class="min-w-0 flex-1">
								<p class="text-xs text-gray-400">
									{new Date(run.created_at * 1000).toLocaleString()} · {run.model_id}
								</p>
								<h3 class="mt-2 break-words text-sm font-medium leading-6">
									{run.prompt?.slice(0, 100) ?? 'Agent execution'}
								</h3>
							</div>
							<span
								class:status-active={['running', 'queued', 'pausing'].includes(run.status)}
								class:status-success={run.status === 'completed'}
								class:status-warning={['needs_review', 'blocked', 'approval_required'].includes(
									run.status
								)}
								class:status-error={['failed', 'cancelled'].includes(run.status)}
								class="status-badge"
								><span class="status-dot"></span>{run.status.replaceAll('_', ' ')}</span
							>
						</div>
						<p class="mt-3 text-xs text-gray-500">
							{run.tokens_used.toLocaleString()} / {run.token_budget.toLocaleString()} execution credits
						</p>
						<details
							class="mt-5 rounded-lg border border-gray-100 dark:border-gray-800"
							open={['running', 'pausing', 'blocked', 'failed'].includes(run.status)}
						>
							<summary
								class="cursor-pointer px-4 py-3 text-xs font-medium text-gray-600 dark:text-gray-300"
								>Activity · {(run.checkpoint.phase ?? run.status).replaceAll('_', ' ')}</summary
							>
							<ol
								class="ml-5 mb-4 space-y-3 border-l border-gray-200 pl-4 text-xs dark:border-gray-700"
								aria-live="polite"
							>
								{#each run.timeline ?? [] as event (event.sequence)}<li
										class="flex flex-wrap items-baseline gap-x-3 gap-y-1"
									>
										<time
											class="font-mono text-gray-400"
											datetime={new Date(event.at * 1000).toISOString()}
											>{new Date(event.at * 1000).toLocaleTimeString()}</time
										><span class="text-gray-700 dark:text-gray-300"
											>{event.tool ?? 'Execution'} · {event.type
												.replaceAll('.', ' ')
												.replaceAll('_', ' ')}</span
										>{#if event.duration_ms != null}<span class="text-gray-400"
												>{Math.round(event.duration_ms)} ms</span
											>{/if}
									</li>{/each}
							</ol>
						</details>
						{#if run.checkpoint.message}<p class="mt-3 text-xs leading-5 text-gray-500">
								{run.checkpoint.message}
							</p>{/if}
					</div>
					<div
						class="flex flex-wrap items-center gap-x-5 gap-y-3 border-t border-gray-100 bg-gray-50/60 px-5 py-3 text-xs font-medium dark:border-gray-800 dark:bg-gray-900/60 sm:px-6"
					>
						<a class="text-gray-800 hover:underline dark:text-gray-200" href={`/c/${run.chat_id}`}
							>Open conversation and tool details <span aria-hidden="true">↗</span></a
						>
						{#if ['queued', 'running', 'pausing', 'paused', 'blocked', 'approval_required'].includes(run.status)}<button
								class="text-red-600 hover:underline disabled:opacity-40"
								disabled={busy}
								on:click={() => action(run, 'cancel')}>Cancel</button
							>{/if}
						{#if ['queued', 'running'].includes(run.status)}<button
								class="hover:underline disabled:opacity-40"
								disabled={busy}
								on:click={() => action(run, 'pause')}>Pause</button
							>{/if}
						{#if ['paused', 'blocked'].includes(run.status)}<button
								class="hover:underline disabled:opacity-40"
								disabled={busy}
								on:click={() => action(run, 'resume')}>Resume from checkpoint</button
							>{/if}
						{#if run.status === 'needs_review'}<button
								class="text-emerald-700 hover:underline disabled:opacity-40 dark:text-emerald-400"
								disabled={busy}
								on:click={() => action(run, 'verify')}>I verified the result</button
							>{/if}
					</div>
				</article>{:else}<div
					class="rounded-xl border border-dashed border-gray-300 px-6 py-12 text-center dark:border-gray-700"
				>
					<div
						class="mx-auto flex h-10 w-10 items-center justify-center rounded-lg border border-gray-200 text-lg text-gray-400 dark:border-gray-700"
						aria-hidden="true"
					>
						✳
					</div>
					<p class="mt-4 text-sm font-medium">No tasks yet</p>
					<p class="mt-1 text-xs text-gray-500">Your agent activity will appear here.</p>
				</div>{/each}
		</div>
	</section>
</section>

<style>
	.status-badge {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		border: 1px solid #e5e7eb;
		border-radius: 9999px;
		padding: 4px 10px;
		color: #6b7280;
		font-size: 11px;
		font-weight: 500;
		white-space: nowrap;
	}
	.status-dot {
		width: 6px;
		height: 6px;
		border-radius: 50%;
		background: currentColor;
	}
	.status-active {
		color: #2563eb;
		border-color: #bfdbfe;
		background: #eff6ff;
	}
	.status-success {
		color: #047857;
		border-color: #a7f3d0;
		background: #ecfdf5;
	}
	.status-warning {
		color: #a16207;
		border-color: #fde68a;
		background: #fffbeb;
	}
	.status-error {
		color: #b91c1c;
		border-color: #fecaca;
		background: #fef2f2;
	}
	:global(.dark) .status-badge {
		background: transparent;
		border-color: #374151;
	}
</style>
