<script>
	import { parsePluginDraft } from '$lib/utils/pluginImport';
	import { goto } from '$app/navigation';
	import { createNewTool, getTools } from '$lib/apis/tools';
	import ToolkitEditor from '$lib/components/workspace/Tools/ToolkitEditor.svelte';
	import { COMMUNITY_ORIGINS, WEBUI_VERSION } from '$lib/constants';
	import { tools } from '$lib/stores';
	import { compareVersion, extractFrontmatter } from '$lib/utils';
	import { onMount, getContext } from 'svelte';
	import { toast } from 'svelte-sonner';

	const i18n = getContext('i18n');

	let mounted = false;
	let clone = false;
	/** @type {import('$lib/types/plugins').PluginDraft | null} */
	let tool = null;

	/** @param {import('$lib/types/plugins').PluginDraft} data */
	const saveHandler = async (data) => {
		console.log(data);

		const manifest = extractFrontmatter(data.content);
		if (compareVersion(manifest?.required_answerai_version ?? '0.0.0', WEBUI_VERSION)) {
			console.log('Version is lower than required');
			// LICENSE covers this Open WebUI wordmark.
			// Do not alter, remove, obscure, or replace it except as LICENSE permits:
			// https://docs.openwebui.com/license.
			toast.error(
				$i18n.t(
					'ANSWERAI version (v{{ANSWERAI_VERSION}}) is lower than required version (v{{REQUIRED_VERSION}})',
					{
						ANSWERAI_VERSION: WEBUI_VERSION,
						REQUIRED_VERSION: manifest?.required_answerai_version ?? '0.0.0'
					}
				)
			);
			return;
		}

		const res = await createNewTool(localStorage.token, {
			id: data.id,
			name: data.name,
			meta: data.meta,
			content: data.content,
			commit_message: data.commit_message,
			access_grants: data.access_grants
		}).catch((error) => {
			toast.error(`${error}`);
			return null;
		});

		if (res) {
			toast.success($i18n.t('Tool created successfully'));
			tools.set(await getTools(localStorage.token));

			await goto('/workspace/tools');
		}
	};

	onMount(() => {
		/** @param {MessageEvent} event */
		const handleImport = async (event) => {
			if (!COMMUNITY_ORIGINS.includes(event.origin) || event.source !== window.opener) return;

			try {
				tool = parsePluginDraft(event.data);
			} catch {
				toast.error($i18n.t('Invalid JSON file'));
			}
			console.log(tool);
		};
		window.addEventListener('message', handleImport);

		if (window.opener ?? false) {
			for (const origin of COMMUNITY_ORIGINS) window.opener.postMessage('loaded', origin);
		}

		if (sessionStorage.tool) {
			try {
				tool = parsePluginDraft(sessionStorage.tool);
			} catch {
				toast.error($i18n.t('Invalid JSON file'));
			}
			sessionStorage.removeItem('tool');

			console.log(tool);
			clone = true;
		}

		mounted = true;
		return () => window.removeEventListener('message', handleImport);
	});
</script>

{#if mounted}
	{#key tool?.content}
		<div class="h-full min-w-0 overflow-x-hidden">
			<ToolkitEditor
				id={tool?.id ?? ''}
				name={tool?.name ?? ''}
				meta={tool?.meta ?? { description: '' }}
				content={tool?.content ?? ''}
				accessGrants={tool?.access_grants !== undefined ? tool.access_grants : []}
				{clone}
				onSave={saveHandler}
			/>
		</div>
	{/key}
{/if}
