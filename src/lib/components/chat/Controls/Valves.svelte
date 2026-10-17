<script lang="ts">
	import type { ValveSchema, ValveValues } from '$lib/types/valves';
	import { serializeValveValues } from '$lib/utils/valveValues';
	import { resolveLocalizedResource } from '$lib/utils/localizedContent';
	import { toast } from 'svelte-sonner';

	import { config, functions, models, settings, tools, user } from '$lib/stores';
	import { createEventDispatcher, onMount, onDestroy, getContext, tick } from 'svelte';

	import {
		getUserValvesSpecById as getToolUserValvesSpecById,
		getUserValvesById as getToolUserValvesById,
		updateUserValvesById as updateToolUserValvesById,
		getTools
	} from '$lib/apis/tools';
	import {
		getUserValvesSpecById as getFunctionUserValvesSpecById,
		getUserValvesById as getFunctionUserValvesById,
		updateUserValvesById as updateFunctionUserValvesById,
		getFunctions
	} from '$lib/apis/functions';

	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import Valves from '$lib/components/common/Valves.svelte';

	const dispatch = createEventDispatcher();

	const i18n = getContext<typeof import('$lib/i18n').default>('i18n');

	export let show = false;

	let tab = 'tools';
	let selectedId = '';

	let loading = false;

	let valvesSpec: ValveSchema | null = null;
	let valves: ValveValues = {};

	let debounceTimer: ReturnType<typeof setTimeout> | undefined;

	let loadVersion = 0;
	let destroyed = false;
	let editVersion = 0;
	onDestroy(() => {
		destroyed = true;
		loadVersion += 1;
		clearTimeout(debounceTimer);
	});
	const current = (version: number, resourceId: string, resourceTab: string) =>
		!destroyed &&
		show &&
		version === loadVersion &&
		selectedId === resourceId &&
		tab === resourceTab;
	const debounceSubmitHandler = () => {
		clearTimeout(debounceTimer);
		const resourceId = selectedId;
		const resourceTab = tab;
		const version = loadVersion;
		const revision = ++editVersion;
		const values = valvesSpec ? serializeValveValues(valves, valvesSpec) : null;
		debounceTimer = setTimeout(() => {
			if (values && current(version, resourceId, resourceTab))
				void saveValues(resourceId, resourceTab, values, version, revision);
		}, 500);
	};
	const getUserValves = async (resourceId: string, resourceTab: string, visible: boolean) => {
		const version = ++loadVersion;
		clearTimeout(debounceTimer);
		valves = {};
		valvesSpec = null;
		if (!resourceId || !visible) {
			loading = false;
			return;
		}
		loading = true;
		try {
			const [values, spec]: [ValveValues, ValveSchema | null] = await Promise.all(
				resourceTab === 'tools'
					? [
							getToolUserValvesById(localStorage.token, resourceId),
							getToolUserValvesSpecById(localStorage.token, resourceId)
						]
					: [
							getFunctionUserValvesById(localStorage.token, resourceId),
							getFunctionUserValvesSpecById(localStorage.token, resourceId)
						]
			);
			if (!current(version, resourceId, resourceTab)) return;
			valves = values ?? {};
			valvesSpec = spec;
			for (const property in spec?.properties ?? {}) {
				if (
					spec?.properties[property]?.type === 'array' &&
					spec.properties[property]?.input?.type !== 'multiselect'
				) {
					const value = valves[property];
					valves[property] = value == null ? null : (Array.isArray(value) ? value : []).join(',');
				}
			}
		} catch (error) {
			if (current(version, resourceId, resourceTab)) toast.error(`${error}`);
		} finally {
			if (current(version, resourceId, resourceTab)) loading = false;
		}
	};
	const saveValues = async (
		resourceId: string,
		resourceTab: string,
		values: ValveValues,
		version: number,
		revision: number
	) => {
		try {
			const res = await (
				resourceTab === 'tools' ? updateToolUserValvesById : updateFunctionUserValvesById
			)(localStorage.token, resourceId, values);
			// Keep editable strings and edits made while the save was pending.
			if (res && current(version, resourceId, resourceTab) && revision === editVersion)
				toast.success($i18n.t('Valves updated'));
		} catch (error) {
			if (current(version, resourceId, resourceTab)) toast.error(`${error}`);
		}
	};
	const submitHandler = async () => {
		clearTimeout(debounceTimer);
		if (!selectedId || !valvesSpec || loading) return;
		await saveValues(
			selectedId,
			tab,
			serializeValveValues(valves, valvesSpec),
			loadVersion,
			++editVersion
		);
	};

	$: if (tab) {
		selectedId = '';
	}

	$: getUserValves(selectedId, tab, show);

	$: if (show) {
		init();
	}

	const init = async () => {
		loading = true;

		if ($functions === null) {
			functions.set(await getFunctions(localStorage.token));
		}
		if ($tools === null) {
			tools.set(await getTools(localStorage.token));
		}

		loading = false;
	};
</script>

{#if show && !loading}
	<form
		class="flex flex-col h-full justify-between space-y-2 text-xs"
		on:submit|preventDefault={() => {
			submitHandler();
			dispatch('save');
		}}
	>
		<div class="flex flex-col">
			<div class="space-y-1">
				<div class="flex gap-2">
					<div class="flex-1">
						<select
							class="w-full rounded-sm py-1 px-1 text-xs bg-transparent outline-hidden"
							bind:value={tab}
							placeholder={$i18n.t('Select')}
						>
							<option value="tools" class="bg-gray-100 dark:bg-gray-800">{$i18n.t('Tools')}</option>
							<option value="functions" class="bg-gray-100 dark:bg-gray-800"
								>{$i18n.t('Functions')}</option
							>
						</select>
					</div>

					<div class="flex-1">
						<select
							class="w-full rounded-sm py-1 px-1 text-xs bg-transparent outline-hidden"
							bind:value={selectedId}
							on:change={async () => {
								await tick();
							}}
						>
							{#if tab === 'tools'}
								<option value="" selected disabled class="bg-gray-100 dark:bg-gray-800"
									>{$i18n.t('Select a tool')}</option
								>

								{#each ($tools ?? [])
									.filter((tool) => !tool?.id?.startsWith('server:'))
									.sort((a, b) => (a.name ?? '').localeCompare(b.name ?? '')) as tool, toolIdx}
									<option value={tool.id} class="bg-gray-100 dark:bg-gray-800"
										>{resolveLocalizedResource(tool, $i18n.language)}</option
									>
								{/each}
							{:else if tab === 'functions'}
								<option value="" selected disabled class="bg-gray-100 dark:bg-gray-800"
									>{$i18n.t('Select a function')}</option
								>

								{#each ($functions ?? []).toSorted( (a, b) => (a.name ?? '').localeCompare(b.name ?? '') ) as func, funcIdx}
									<option value={func.id} class="bg-gray-100 dark:bg-gray-800"
										>{resolveLocalizedResource(func, $i18n.language)}</option
									>
								{/each}
							{/if}
						</select>
					</div>
				</div>
			</div>

			{#if selectedId}
				<div class="my-1 text-xs">
					{#if !loading}
						<div class="chat-control-valves">
							<Valves
								{valvesSpec}
								meta={(tab === 'tools' ? $tools : $functions)?.find(
									(item) => item.id === selectedId
								)?.meta}
								userValves
								bind:valves
								on:change={() => {
									debounceSubmitHandler();
								}}
							/>
						</div>
					{:else}
						<Spinner className="size-5" />
					{/if}
				</div>
			{/if}
		</div>
	</form>
{:else}
	<Spinner className="size-4" />
{/if}

<style>
	.chat-control-valves :global(input),
	.chat-control-valves :global(select),
	.chat-control-valves :global(textarea) {
		font-size: 0.75rem;
		line-height: 1rem;
	}
</style>
