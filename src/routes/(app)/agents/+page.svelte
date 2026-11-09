<script lang="ts">
	import ArrowUp from '@lucide/svelte/icons/arrow-up';
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
	let hasLoaded = false;
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
			if (mounted) hasLoaded = true;
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
		model =
			($config?.default_models ?? '')
				.split(',')
				.find((id) => $models.some((item) => item.id === id.trim()))
				?.trim() ??
			$models[0]?.id ??
			'';
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

<svelte:head><title>Tasks · ANSWERAI</title></svelte:head>
<section
	aria-label="Agent executions"
	class="aai-content mx-auto w-full px-5 pb-16 pt-8 text-gray-950 dark:text-gray-100 sm:px-8 sm:pt-14"
>
	<a href="/" class="text-sm text-gray-500 hover:text-gray-900 dark:hover:text-white">← Chat</a>
	<header class="mb-8 mt-10">
		<h1 class="text-2xl font-semibold tracking-tight">Agent tasks</h1>
		<p class="mt-2 text-sm text-gray-500">
			Research in the background. Pick up where you left off.
		</p>
	</header>
	{#if error}<p role="alert" class="mb-5 text-sm text-red-600 dark:text-red-400">{error}</p>{/if}
	<form on:submit|preventDefault={create} class="aai-card p-4">
		<label class="sr-only" for="task-objective">Objective</label>
		<textarea
			id="task-objective"
			aria-label="Objective"
			class="min-h-28 w-full resize-y border-0 bg-transparent p-1 text-base leading-7 outline-none placeholder:text-gray-400 focus:ring-0"
			bind:value={objective}
			disabled={busy}
			on:input={() => (requestKey = crypto.randomUUID())}
			maxlength="16000"
			required
			rows="3"
			placeholder="What would you like to research?"
		></textarea>
		<div class="mt-3 flex flex-wrap items-center justify-between gap-3">
			<select
				aria-label="Model"
				class="min-w-0 max-w-[55%] truncate rounded-md border-0 bg-transparent py-2 pl-1 pr-6 text-xs text-gray-500 outline-none focus:ring-1 focus:ring-gray-400"
				bind:value={model}
				disabled={busy}
				required
				>{#each $models as item}<option value={item.id}>{item.name ?? item.id}</option
					>{/each}</select
			>
			<button class="aai-button aai-button--primary" disabled={busy || !model || !objective.trim()}
				>Start task <ArrowUp class="size-4" strokeWidth={1.5} aria-hidden="true" /></button
			>
		</div>
		<details class="mt-2 border-t border-gray-100 pt-3 dark:border-gray-800">
			<summary
				class="w-fit cursor-pointer text-xs text-gray-500 hover:text-gray-900 dark:hover:text-gray-200"
				>Options</summary
			>
			<div class="mt-4 space-y-4 pb-1">
				<label class="flex items-center gap-2 text-sm"
					><input
						type="checkbox"
						bind:checked={webSearch}
						disabled={!$config?.features?.enable_web_search || busy}
					/>Web research</label
				>
				<label class="flex flex-wrap items-center gap-3 text-sm"
					>Maximum execution credits<select
						aria-label="Maximum execution credits"
						class="rounded-md border border-gray-200 bg-transparent px-2 py-1 text-sm dark:border-gray-700"
						bind:value={tokenBudget}
						disabled={busy}
						><option value={64000}>64,000</option><option value={256000}>256,000</option><option
							value={500000}>500,000</option
						></select
					></label
				>
				<p class="text-xs leading-5 text-gray-500">
					Read-only tools · Up to 5 minutes · 12 tool iterations. Review results before marking a
					task complete.
				</p>
			</div>
		</details>
	</form>
	<section aria-label="Execution history" class="mt-12">
		<h2 class="mb-3 text-xs font-medium text-gray-500">Recent tasks</h2>

		{#if !hasLoaded}
			<div role="status" aria-label="Loading tasks" aria-busy="true" class="space-y-4 py-5">
				<span class="sr-only">Loading tasks…</span>
				{#each [0, 1, 2] as row (row)}
					<div class="space-y-2" aria-hidden="true">
						<div class="aai-skeleton h-4 w-3/4"></div>
						<div class="aai-skeleton h-3 w-1/3"></div>
					</div>
				{/each}
			</div>
		{:else}
			{#each runs as run}<article class="border-t border-gray-100 py-5 dark:border-gray-800">
					<div class="flex items-start justify-between gap-4">
						<a
							class="min-w-0 break-words text-sm font-medium leading-6 hover:underline"
							href={`/c/${run.chat_id}`}>{run.prompt?.slice(0, 140) ?? 'Agent task'}</a
						><span
							data-status={run.status}
							class="aai-status shrink-0 pt-1"
							class:text-red-600={run.status === 'failed'}
							class:text-emerald-600={run.status === 'completed'}
							>{run.status.replaceAll('_', ' ')}</span
						>
					</div>
					<div class="mt-2 flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-gray-500">
						<time datetime={new Date(run.created_at * 1000).toISOString()}
							>{new Date(run.created_at * 1000).toLocaleDateString()}</time
						>
						{#if ['queued', 'running'].includes(run.status)}<button
								disabled={busy}
								class="hover:text-gray-950 dark:hover:text-white"
								on:click={() => action(run, 'pause')}>Pause</button
							>{/if}
						{#if ['paused', 'blocked'].includes(run.status)}<button
								disabled={busy}
								class="hover:text-gray-950 dark:hover:text-white"
								on:click={() => action(run, 'resume')}>Resume from checkpoint</button
							>{/if}
						{#if ['queued', 'running', 'pausing', 'paused', 'blocked', 'approval_required'].includes(run.status)}<button
								disabled={busy}
								class="hover:text-red-600"
								on:click={() => action(run, 'cancel')}>Cancel</button
							>{/if}
						{#if run.status === 'needs_review'}<button
								disabled={busy}
								class="text-gray-800 hover:underline dark:text-gray-200"
								on:click={() => action(run, 'verify')}>I verified the result</button
							>{/if}
					</div>
					<details class="mt-3">
						<summary
							class="w-fit cursor-pointer text-xs text-gray-500 hover:text-gray-900 dark:hover:text-white"
							>Activity</summary
						>
						<p class="mt-3 break-words text-xs text-gray-500">
							{run.model_id} · {run.tokens_used.toLocaleString()} / {run.token_budget.toLocaleString()}
							credits
						</p>
						<ol
							class="mt-3 space-y-2 border-l border-gray-200 pl-3 text-xs leading-5 dark:border-gray-700"
							aria-live="polite"
						>
							{#each run.timeline ?? [] as event (event.sequence)}<li>
									<span class="text-gray-400">{new Date(event.at * 1000).toLocaleTimeString()}</span
									>
									<span class="text-gray-600 dark:text-gray-300"
										>{event.tool ?? 'Task'} · {event.type
											.replaceAll('.', ' ')
											.replaceAll('_', ' ')}</span
									>{#if event.duration_ms != null}<span class="text-gray-400">
											· {Math.round(event.duration_ms)} ms</span
										>{/if}
								</li>{/each}
						</ol>
						{#if run.checkpoint.message}<p class="mt-3 text-xs text-gray-500">
								{run.checkpoint.message}
							</p>{/if}
					</details>
				</article>{:else}{#if !error}<p
						class="border-t border-gray-100 py-8 text-center text-sm text-gray-400 dark:border-gray-800"
					>
						Your tasks will appear here.
					</p>{/if}{/each}
		{/if}
	</section>
</section>
