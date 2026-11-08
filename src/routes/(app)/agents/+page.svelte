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

<svelte:head><title>Agent executions · ANSWERAI</title></svelte:head>
<section aria-label="Agent executions" class="mx-auto w-full max-w-4xl overflow-auto p-6 md:p-10">
	<a href="/" class="text-sm text-gray-500">← Chat</a>
	<h1 class="mt-4 text-2xl font-semibold">Background agent tasks</h1>
	<p class="mt-2 text-sm text-gray-500">
		Server-side tasks persist across browser refreshes. This mode uses read-only built-in tools;
		actions and external connectors require an interactive chat.
	</p>
	{#if error}<p role="alert" class="my-4 text-red-500">{error}</p>{/if}
	<form
		class="my-6 space-y-3 rounded-2xl border border-gray-200 p-4 dark:border-gray-800"
		on:submit|preventDefault={create}
	>
		<label class="block text-sm"
			>Objective<textarea
				class="mt-2 w-full rounded-lg border bg-transparent p-3"
				bind:value={objective}
				disabled={busy}
				on:input={() => (requestKey = crypto.randomUUID())}
				maxlength="16000"
				required
				rows="4"
			></textarea></label
		>
		<label class="block text-sm"
			>Model<select
				aria-label="Model"
				class="ml-3 rounded-lg border bg-transparent p-2"
				bind:value={model}
				required
				>{#each $models as item}<option value={item.id}>{item.name ?? item.id}</option
					>{/each}</select
			></label
		>
		<label class="flex items-center gap-2 text-sm">
			<input
				type="checkbox"
				bind:checked={webSearch}
				disabled={!$config?.features?.enable_web_search || busy}
			/>
			Web research
		</label>
		<label class="block text-sm"
			>Maximum execution credits
			<select
				class="ml-3 rounded-lg border bg-transparent p-2"
				aria-label="Maximum execution credits"
				bind:value={tokenBudget}
				disabled={busy}
			>
				<option value={64000}>64,000</option><option value={256000}>256,000</option><option
					value={500000}>500,000</option
				>
			</select>
		</label>
		<p class="text-xs text-gray-500">
			Budget: five minutes and twelve tool iterations. Quotas apply. Results require your
			verification.
		</p>
		<button
			class="rounded-lg bg-blue-600 px-4 py-2 text-white disabled:opacity-50"
			disabled={busy || !model || !objective.trim()}>Start research</button
		>
	</form>
	<section class="space-y-4" aria-label="Execution history">
		{#each runs as run}<article class="rounded-2xl border border-gray-200 p-4 dark:border-gray-800">
				<div class="flex flex-wrap items-center justify-between gap-3">
					<h2 class="font-medium">{run.prompt?.slice(0, 100) ?? 'Agent execution'}</h2>
					<span class="rounded-full bg-gray-100 px-3 py-1 text-xs dark:bg-gray-800"
						>{run.status.replaceAll('_', ' ')}</span
					>
				</div>
				<p class="mt-2 text-xs text-gray-500">
					{run.model_id} · {run.tokens_used.toLocaleString()} / {run.token_budget.toLocaleString()} execution
					credits
				</p>
				<details
					class="mt-4"
					open={['running', 'pausing', 'blocked', 'failed'].includes(run.status)}
				>
					<summary class="cursor-pointer text-sm"
						>Activity · {run.checkpoint.phase ?? run.status}</summary
					>
					<ol
						class="mt-3 space-y-2 border-l border-gray-200 pl-4 text-sm dark:border-gray-700"
						aria-live="polite"
					>
						{#each run.timeline ?? [] as event (event.sequence)}
							<li class="flex flex-wrap gap-2">
								<time
									class="text-xs text-gray-500"
									datetime={new Date(event.at * 1000).toISOString()}
									>{new Date(event.at * 1000).toLocaleTimeString()}</time
								>
								<span
									>{event.tool ?? 'Execution'} · {event.type
										.replaceAll('.', ' ')
										.replaceAll('_', ' ')}</span
								>
								{#if event.duration_ms != null}<span class="text-xs text-gray-500"
										>{Math.round(event.duration_ms)} ms</span
									>{/if}
							</li>
						{/each}
					</ol>
				</details>
				{#if run.checkpoint.message}<p class="mt-2 text-sm text-gray-500">
						{run.checkpoint.message}
					</p>{/if}
				<div class="mt-4 flex flex-wrap gap-4 text-sm">
					<a class="text-blue-500" href={`/c/${run.chat_id}`}>Open conversation and tool details</a>
					{#if ['queued', 'running', 'pausing', 'paused', 'blocked', 'approval_required'].includes(run.status)}<button
							class="text-red-500"
							disabled={busy}
							on:click={() => action(run, 'cancel')}>Cancel</button
						>{/if}
					{#if ['queued', 'running'].includes(run.status)}<button
							disabled={busy}
							on:click={() => action(run, 'pause')}>Pause</button
						>{/if}
					{#if ['paused', 'blocked'].includes(run.status)}<button
							disabled={busy}
							on:click={() => action(run, 'resume')}>Resume from checkpoint</button
						>{/if}
					{#if run.status === 'needs_review'}<button
							class="text-green-600"
							disabled={busy}
							on:click={() => action(run, 'verify')}>I verified the result</button
						>{/if}
				</div>
			</article>{:else}<p class="text-sm text-gray-500">No executions yet.</p>{/each}
	</section>
</section>
