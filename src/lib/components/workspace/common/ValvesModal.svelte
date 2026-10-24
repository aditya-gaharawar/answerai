<script lang="ts">
	import type { ValveSchema, ValveValues } from '$lib/types/valves';
	import { serializeValveValues } from '$lib/utils/valveValues';
	import { toast } from 'svelte-sonner';
	import { createEventDispatcher } from 'svelte';
	import { onMount, onDestroy, getContext } from 'svelte';
	import { tools, functions } from '$lib/stores';
	import { addUser } from '$lib/apis/auths';

	import Modal from '../../common/Modal.svelte';
	import {
		getFunctionValvesById,
		getFunctionValvesSpecById,
		updateFunctionValvesById
	} from '$lib/apis/functions';
	import { getToolValvesById, getToolValvesSpecById, updateToolValvesById } from '$lib/apis/tools';

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

	import Spinner from '../../common/Spinner.svelte';
	import Switch from '$lib/components/common/Switch.svelte';
	import Valves from '$lib/components/common/Valves.svelte';
	import XMark from '$lib/components/icons/XMark.svelte';

	const i18n = getContext<typeof import('$lib/i18n').default>('i18n');
	const dispatch = createEventDispatcher();

	export let show = false;

	export let type = 'tool';
	export let id: string | null = null;
	export let userValves = false;
	export let meta: import('$lib/types/plugins').PluginMeta | null | undefined = null;
	$: resourceMeta =
		meta ?? (type === 'tool' ? $tools : $functions)?.find((item) => item.id === id)?.meta ?? {};

	let saving = false;
	let loading = false;

	let valvesSpec: ValveSchema | null = null;
	let valves: ValveValues = {};

	const submitHandler = async () => {
		if (!id || loading || saving) return;
		saving = true;

		if (valvesSpec) {
			const submittedValves = serializeValveValues(valves, valvesSpec);

			let res = null;

			if (userValves) {
				if (type === 'tool') {
					res = await updateToolUserValvesById(localStorage.token, id, submittedValves).catch(
						(error) => {
							toast.error(`${error}`);
						}
					);
				} else if (type === 'function') {
					res = await updateFunctionUserValvesById(localStorage.token, id, submittedValves).catch(
						(error) => {
							toast.error(`${error}`);
						}
					);
				}
			} else {
				if (type === 'tool') {
					res = await updateToolValvesById(localStorage.token, id, submittedValves).catch(
						(error) => {
							toast.error(`${error}`);
						}
					);
				} else if (type === 'function') {
					res = await updateFunctionValvesById(localStorage.token, id, submittedValves).catch(
						(error) => {
							toast.error(`${error}`);
						}
					);
				}
			}

			if (res) {
				toast.success($i18n.t('Valves updated successfully'));
				dispatch('save');
			}
		}

		saving = false;
	};

	let loadVersion = 0;
	let destroyed = false;
	onDestroy(() => {
		destroyed = true;
		loadVersion += 1;
	});
	const initHandler = async (
		resourceId: string | null,
		resourceType: string,
		userScope: boolean,
		visible: boolean
	) => {
		const version = ++loadVersion;
		valves = {};
		valvesSpec = null;
		if (!resourceId || !visible) {
			loading = false;
			return;
		}
		loading = true;
		try {
			const getValues = userScope
				? resourceType === 'tool'
					? getToolUserValvesById
					: getFunctionUserValvesById
				: resourceType === 'tool'
					? getToolValvesById
					: getFunctionValvesById;
			const getSpec = userScope
				? resourceType === 'tool'
					? getToolUserValvesSpecById
					: getFunctionUserValvesSpecById
				: resourceType === 'tool'
					? getToolValvesSpecById
					: getFunctionValvesSpecById;
			const [values, spec]: [ValveValues, ValveSchema | null] = await Promise.all([
				getValues(localStorage.token, resourceId),
				getSpec(localStorage.token, resourceId)
			]);
			if (destroyed || version !== loadVersion) return;
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
			if (!destroyed && version === loadVersion) {
				toast.error('Error fetching valves');
				show = false;
			}
		} finally {
			if (!destroyed && version === loadVersion) loading = false;
		}
	};
	$: initHandler(id, type, userValves, show);
</script>

<Modal size="sm" bind:show>
	<div>
		<div class="flex justify-between dark:text-gray-100 px-4 pt-3 pb-1">
			<div class="self-center text-sm font-medium">{$i18n.t('Valves')}</div>
			<button
				class="self-center rounded-lg p-1 text-gray-500 transition hover:bg-gray-50 hover:text-gray-700 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-200"
				on:click={() => {
					show = false;
				}}
			>
				<XMark className={'size-4'} />
			</button>
		</div>

		<div class="flex flex-col md:flex-row w-full px-4 pb-3 md:space-x-4 dark:text-gray-200">
			<div class=" flex flex-col w-full sm:flex-row sm:justify-center sm:space-x-6">
				<form
					class="flex flex-col w-full"
					on:submit|preventDefault={() => {
						submitHandler();
					}}
				>
					<div>
						{#if !loading}
							<Valves {valvesSpec} bind:valves meta={resourceMeta} {userValves} />
						{:else}
							<Spinner className="size-5" />
						{/if}
					</div>

					<div class="flex justify-end pt-2.5 text-sm font-normal">
						<button
							class="flex h-7 shrink-0 items-center justify-center gap-1.5 rounded-lg bg-gray-900 px-2.5 text-xs font-normal text-white transition hover:bg-black disabled:opacity-60 dark:bg-gray-100 dark:text-gray-900 dark:hover:bg-white disabled:cursor-not-allowed"
							type="submit"
							disabled={saving}
						>
							{$i18n.t('Save')}

							{#if saving}
								<span class="shrink-0">
									<Spinner className="size-3" />
								</span>
							{/if}
						</button>
					</div>
				</form>
			</div>
		</div>
	</div>
</Modal>
