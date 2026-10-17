<script lang="ts">
	import { getContext } from 'svelte';
	import type { ChatParams } from '$lib/apis';
	import { models, settings, user } from '$lib/stores';
	import { findThinkingControl } from '$lib/utils/agentControls';
	import Sparkles from '$lib/components/icons/Sparkles.svelte';

	const i18n: any = getContext('i18n');
	export let params: ChatParams = {};
	export let selectedModels: string[] = [];
	export let disabled = false;
	$: permitted =
		$user?.role === 'admin' ||
		(($user?.permissions?.chat?.controls ?? true) && ($user?.permissions?.chat?.params ?? true));
	$: model =
		selectedModels.length === 1 ? $models.find((m) => m.id === selectedModels[0]) : undefined;
	$: thinking = findThinkingControl(model?.info?.params?.model_controls);
	$: mode = typeof params.agent_mode === 'string' ? params.agent_mode : 'auto';
	$: selection =
		thinking && model
			? (params.model_controls?.[model.id]?.[thinking[0]] ??
				$settings?.params?.model_controls?.[model.id]?.[thinking[0]] ??
				'')
			: '';
	$: agentAvailable =
		selectedModels.length > 0 &&
		selectedModels.every(
			(id) => $models.find((m) => m.id === id)?.info?.meta?.capabilities?.builtin_tools !== false
		);

	function changeMode(value: string) {
		params = {
			...params,
			agent_mode: value === 'agent' || value === 'chat' ? value : 'auto',
			...(value === 'agent' ? { function_calling: 'native' } : {})
		};
	}
	function changeThinking(value: string) {
		if (!model || !thinking) return;
		params = {
			...params,
			model_controls: {
				...params.model_controls,
				[model.id]: { ...params.model_controls?.[model.id], [thinking[0]]: value }
			}
		};
	}
</script>

{#if permitted}
	<div class="agent-toolbar" aria-label={$i18n.t('Chat capabilities')}>
		<div class="agent-select">
			<Sparkles className="size-3.5 text-violet-500" />
			<select
				aria-label={$i18n.t('Conversation mode')}
				value={mode}
				{disabled}
				on:change={(event) => changeMode(event.currentTarget.value)}
			>
				<option value="auto">{$i18n.t('Auto')}</option>
				<option value="agent" disabled={!agentAvailable}>{$i18n.t('Agent')}</option>
				<option value="chat">{$i18n.t('Chat only')}</option>
			</select>
		</div>
		<div
			class="agent-select"
			title={thinking
				? $i18n.t('Choose how much the model thinks')
				: $i18n.t('Select a model with configured thinking controls')}
		>
			<span aria-hidden="true" class="text-violet-500">◉</span>
			<select
				aria-label={$i18n.t('Thinking effort')}
				value={selection}
				disabled={disabled || !thinking}
				on:change={(event) => changeThinking(event.currentTarget.value)}
			>
				<option value="">{$i18n.t('Thinking: default')}</option>
				{#if thinking}
					{#each Object.entries(thinking[1].options) as [value, option]}
						<option {value}>{$i18n.t('Thinking')}: {option.label}</option>
					{/each}
				{/if}
			</select>
		</div>
		<span class="agent-explanation"
			>{mode === 'agent'
				? $i18n.t('Built-in tools · multi-step tasks')
				: mode === 'chat'
					? $i18n.t('Built-in tools off')
					: $i18n.t('Your model, your workflow')}</span
		>
	</div>
{/if}

<style>
	.agent-toolbar {
		display: flex;
		align-items: center;
		flex-wrap: wrap;
		gap: 0.5rem;
		padding: 0.7rem 0.85rem 0.25rem;
	}
	.agent-select {
		display: flex;
		align-items: center;
		gap: 0.35rem;
		padding: 0.35rem 0.55rem;
		border-radius: 999px;
		border: 1px solid rgb(139 92 246 / 0.16);
		background: rgb(139 92 246 / 0.04);
		font-size: 0.75rem;
	}
	select {
		background: transparent;
		color: inherit;
		max-width: 12rem;
		cursor: pointer;
		outline-offset: 3px;
	}
	select:disabled {
		opacity: 0.55;
		cursor: default;
	}
	option {
		background: var(--color-gray-50, white);
		color: #111827;
	}
	.agent-explanation {
		font-size: 0.7rem;
		color: var(--color-gray-500, #6b7280);
		margin-inline-start: auto;
	}
	@media (max-width: 640px) {
		.agent-explanation {
			display: none;
		}
		.agent-toolbar {
			gap: 0.35rem;
		}
	}
</style>
