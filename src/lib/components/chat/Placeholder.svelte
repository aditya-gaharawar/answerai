<script lang="ts">
	import type { Model } from '$lib/stores';
	import { toast } from 'svelte-sonner';
	import { marked } from 'marked';
	import DOMPurify from 'dompurify';

	import { onMount, getContext, tick, createEventDispatcher } from 'svelte';
	import { blur, fade } from 'svelte/transition';

	const dispatch = createEventDispatcher();

	import { updateFolderById } from '$lib/apis/folders';

	import {
		config,
		user,
		models as _models,
		temporaryChatEnabled,
		selectedFolder
	} from '$lib/stores';
	import { refreshChatList, refreshFolderChatLists } from '$lib/stores/chatList';
	import { sanitizeResponseContent, extractCurlyBraceWords } from '$lib/utils';
	import {
		resolveLocalizedModelDescription,
		resolveLocalizedModelName,
		resolveLocalizedModelPromptSuggestions,
		resolveLocalizedPromptSuggestions
	} from '$lib/utils/localizedContent';
	import { WEBUI_API_BASE_URL, WEBUI_BASE_URL } from '$lib/constants';

	import Suggestions from './Suggestions.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import EyeSlash from '$lib/components/icons/EyeSlash.svelte';
	import MessageInput from './MessageInput.svelte';
	import Sparkles from '$lib/components/icons/Sparkles.svelte';
	import GlobeAlt from '$lib/components/icons/GlobeAlt.svelte';
	import Photo from '$lib/components/icons/Photo.svelte';
	import CodeBrackets from '$lib/components/icons/CodeBrackets.svelte';
	import FolderPlaceholder from './Placeholder/FolderPlaceholder.svelte';
	import FolderTitle from './Placeholder/FolderTitle.svelte';

	const i18n: any = getContext('i18n');

	export let createMessagePair: Function;
	export let stopResponse: Function;

	export let autoScroll = false;
	export let callActive = false;
	export let callEnabled = true;

	export let atSelectedModel: Model | undefined;
	export let selectedModels: string[] = [];

	export let history;

	export let prompt = '';
	export let params: import('$lib/apis').ChatParams = {};
	export let files: import('$lib/types/notes').NoteAttachment[] = [];
	export let messageInput: InstanceType<typeof MessageInput> | undefined = undefined;

	export let selectedToolIds: string[] = [];
	export let selectedSkillIds: string[] = [];
	export let selectedFilterIds: string[] = [];
	export let pendingOAuthTools: import('$lib/types/chat').PendingOAuthTool[] = [];

	export let showCommands = false;

	export let imageGenerationEnabled = false;
	export let codeInterpreterEnabled = false;
	export let webSearchEnabled = false;
	export let toolApprovalMode = 'full';
	export let onToolApprovalModeChange: Function = () => {};
	export let oauthRedirectHandler: Function = () => {};

	export let onUpload: Function = (e: unknown) => {};
	export let onUpdate: (data?: { file?: any }) => void = () => {};
	export let onSelect: (selection: import('$lib/types/chat').PromptSelection) => void = () => {};
	export let onChange = (e: unknown) => {};
	export let onWebSearchToggle: Function = () => {};
	export let messageQueue: { id: string; prompt: string; files: any[] }[] = [];
	export let onQueueSendNow: (id: string) => void = () => {};
	export let onQueueEdit: (id: string) => void = () => {};
	export let onQueueDelete: (id: string) => void = () => {};
	export let askUser: import('svelte').ComponentProps<typeof MessageInput>['askUser'] = {
		show: false,
		questions: [],
		allowOther: true,
		timeoutMs: null,
		onConfirm: (_value: any) => {},
		onCancel: () => {}
	};

	export let dragged = false;

	let models = [];
	export let selectedModelIdx = 0;
	let selectedModel;
	let selectedModelName = '';
	let selectedModelDescription = '';
	let selectedSuggestionPrompts = [];

	$: models = selectedModels.map((id) => $_models.find((m) => m.id === id));
	$: selectedModel = atSelectedModel ?? models[selectedModelIdx];
	$: selectedModelName = resolveLocalizedModelName(selectedModel, $i18n.language);
	$: selectedModelDescription = resolveLocalizedModelDescription(selectedModel, $i18n.language);
	$: selectedSuggestionPrompts =
		resolveLocalizedModelPromptSuggestions(atSelectedModel, $i18n.language) ??
		resolveLocalizedModelPromptSuggestions(models[selectedModelIdx], $i18n.language) ??
		resolveLocalizedPromptSuggestions(
			$config?.default_prompt_suggestions,
			$config?.default_prompt_suggestions_i18n ?? {},
			$i18n.language,
			(key) => $i18n.t(key)
		);

	// Starters open a draft; never submit an unfinished prompt automatically.
	const startTask = async (text: string) => {
		await messageInput?.setText(text);
		messageInput?.focus({ preventScroll: true });
	};

	// True when viewing a shared folder the current user doesn't own AND lacks write access
	$: folderReadOnly =
		$selectedFolder != null &&
		$selectedFolder.user_id !== $user?.id &&
		!$selectedFolder.write_access;
</script>

<div class="aai-workspace m-auto w-full max-w-[62rem] px-3 @2xl:px-16 py-12 sm:py-20 text-center">
	{#if !$selectedFolder && !atSelectedModel}
		<div class="aai-eyebrow">
			<Sparkles className="size-3.5" />
			{$i18n.t('A little curiosity. Endless possibilities.')}
		</div>
		<h1 class="aai-headline">{$i18n.t('What will you create today?')}</h1>
		<p class="aai-subtitle">
			{$i18n.t('Think it through. Explore the web. Turn ideas into something real.')}
		</p>
	{/if}
	{#if $temporaryChatEnabled}
		<Tooltip
			content={$i18n.t("This chat won't appear in history and your messages will not be saved.")}
			className="w-full flex justify-center mb-0.5"
			placement="top"
		>
			<div class="flex items-center gap-1.5 text-gray-500 text-xs my-1 w-fit">
				<EyeSlash strokeWidth="2" className="size-3.5" />{$i18n.t('Temporary Chat')}
			</div>
		</Tooltip>
	{/if}

	<div class="w-full text-3xl text-gray-800 dark:text-gray-100 text-center flex items-center gap-4">
		<div class="w-full flex flex-col justify-center items-center">
			{#if $selectedFolder}
				<FolderTitle
					folder={$selectedFolder}
					readOnly={folderReadOnly}
					onUpdate={async () => {
						await Promise.all([refreshChatList(localStorage.token), refreshFolderChatLists(null)]);
					}}
					onDelete={async () => {
						await Promise.all([refreshChatList(localStorage.token), refreshFolderChatLists(null)]);

						selectedFolder.set(null);
					}}
				/>
			{:else}
				<div class="flex flex-row justify-center gap-2.5 @sm:gap-3 w-fit px-5 max-w-xl">
					<div class="flex shrink-0 justify-center">
						<div class="flex -space-x-4 mb-0.5" in:fade={{ duration: 100 }}>
							{#each models as model, modelIdx}
								<Tooltip
									content={(models[modelIdx]?.info?.meta?.tags ?? [])
										.map((tag) => tag.name.toUpperCase())
										.join(', ')}
									placement="top"
								>
									<button
										aria-hidden={models.length <= 1}
										aria-label={$i18n.t('Get information on {{name}} in the UI', {
											name: models[modelIdx]?.name
										})}
										on:click={() => {
											selectedModelIdx = modelIdx;
										}}
									>
										<img
											src={`${WEBUI_API_BASE_URL}/models/model/profile/image?id=${model?.id}&lang=${$i18n.language}`}
											class=" size-7 @sm:size-8 rounded-xl"
											aria-hidden="true"
											draggable="false"
											on:error={(e) => {
												// LICENSE covers this Open ANSWERAI fallback logo.
												// Do not alter, remove, obscure, or replace it except as LICENSE permits:
												// https://docs.openwebui.com/license.
												if (e.currentTarget instanceof HTMLImageElement)
													e.currentTarget.src = '/favicon.png';
											}}
										/>
									</button>
								</Tooltip>
							{/each}
						</div>
					</div>

					<div
						class=" text-base @sm:text-lg font-medium line-clamp-1 flex items-center"
						in:fade={{ duration: 100 }}
					>
						{#if selectedModelName}
							<Tooltip content={selectedModelName} placement="top" className=" flex items-center ">
								<span class="line-clamp-1">
									{selectedModelName}
								</span>
							</Tooltip>
						{:else}
							{$i18n.t('Hello, {{name}}', { name: $user?.name })}
						{/if}
					</div>
				</div>

				<div class="flex mt-1 mb-2">
					<div in:fade={{ duration: 100, delay: 50 }}>
						{#if selectedModelDescription}
							<Tooltip
								className=" w-fit"
								content={DOMPurify.sanitize(
									marked.parse(
										sanitizeResponseContent(selectedModelDescription).replaceAll('\n', '<br>')
									)
								)}
								placement="top"
							>
								<div
									class="mt-0.5 px-2 text-sm font-normal text-gray-500 dark:text-gray-400 line-clamp-2 max-w-xl markdown"
								>
									{@html DOMPurify.sanitize(
										marked.parse(
											sanitizeResponseContent(selectedModelDescription).replaceAll('\n', '<br>')
										)
									)}
								</div>
							</Tooltip>

							{#if models[selectedModelIdx]?.info?.meta?.user}
								<div class="mt-0.5 text-sm font-normal text-gray-400 dark:text-gray-500">
									{$i18n.t('By')}
									{#if models[selectedModelIdx]?.info?.meta?.user?.community}
										<a
											href="https://answerai.in/m/{models[selectedModelIdx]?.info?.meta?.user
												?.username}"
											>{models[selectedModelIdx]?.info?.meta?.user?.name
												? models[selectedModelIdx]?.info?.meta?.user?.name
												: `@${models[selectedModelIdx]?.info?.meta?.user?.username}`}</a
										>
									{:else}
										{models[selectedModelIdx]?.info?.meta?.user?.name}
									{/if}
								</div>
							{/if}
						{/if}
					</div>
				</div>
			{/if}

			<div class="text-base font-normal @md:max-w-3xl w-full py-3 {atSelectedModel ? 'mt-2' : ''}">
				{#if !($selectedFolder && folderReadOnly)}
					<MessageInput
						enableAgentControls
						bind:params
						{callActive}
						{callEnabled}
						bind:this={messageInput}
						{history}
						bind:selectedModels
						bind:files
						bind:prompt
						bind:autoScroll
						bind:selectedToolIds
						bind:selectedSkillIds
						bind:selectedFilterIds
						bind:imageGenerationEnabled
						bind:codeInterpreterEnabled
						bind:webSearchEnabled
						bind:atSelectedModel
						bind:showCommands
						bind:dragged
						{pendingOAuthTools}
						{oauthRedirectHandler}
						{toolApprovalMode}
						{onToolApprovalModeChange}
						{stopResponse}
						{createMessagePair}
						placeholder={$i18n.t('How can I help you today?')}
						{onChange}
						{onUpload}
						{onUpdate}
						{messageQueue}
						{onQueueSendNow}
						{onQueueEdit}
						{onQueueDelete}
						{askUser}
						{onWebSearchToggle}
						on:chatVariables
						on:submit={(e) => {
							dispatch('submit', e.detail);
						}}
					/>
				{/if}
			</div>
		</div>
	</div>

	{#if !$selectedFolder && !atSelectedModel}
		<div class="aai-starters" aria-label={$i18n.t('Start something new')}>
			<button
				type="button"
				on:click={() => startTask($i18n.t('Help me turn this idea into a clear plan: '))}
			>
				<span class="aai-starter-icon violet"><Sparkles className="size-5" /></span>
				<strong>{$i18n.t('Make a plan')}</strong><span
					>{$i18n.t('From first thought to next steps')}</span
				>
			</button>
			{#if $config?.features?.enable_web_search && ($user?.role === 'admin' || $user?.permissions?.features?.web_search) && selectedModel?.info?.meta?.capabilities?.web_search !== false}
				<button
					type="button"
					on:click={async () => {
						if (!webSearchEnabled) await onWebSearchToggle(true);
						startTask($i18n.t('Research this topic and cite your sources: '));
					}}
				>
					<span class="aai-starter-icon blue"><GlobeAlt className="size-5" /></span>
					<strong>{$i18n.t('Explore a topic')}</strong><span
						>{$i18n.t('Fresh perspectives, with sources')}</span
					>
				</button>
			{/if}
			{#if $config?.features?.enable_image_generation && ($user?.role === 'admin' || $user?.permissions?.features?.image_generation) && selectedModel?.info?.meta?.capabilities?.image_generation !== false}
				<button
					type="button"
					on:click={() => {
						imageGenerationEnabled = true;
						startTask($i18n.t('Create an image of '));
					}}
				>
					<span class="aai-starter-icon rose"><Photo className="size-5" /></span>
					<strong>{$i18n.t('Create an image')}</strong><span
						>{$i18n.t('Give your imagination a canvas')}</span
					>
				</button>
			{/if}
			<button
				type="button"
				on:click={() => startTask($i18n.t('Help me understand and improve this code: '))}
			>
				<span class="aai-starter-icon green"><CodeBrackets className="size-5" /></span>
				<strong>{$i18n.t('Build something')}</strong><span
					>{$i18n.t('Code, debug, and learn together')}</span
				>
			</button>
		</div>
		<p class="aai-guidance">
			{$i18n.t('Add files with +. Enable Agent for multi-step work. You stay in control.')}
		</p>
	{/if}

	{#if $selectedFolder}
		<div class="mx-auto px-4 md:max-w-3xl md:px-6 min-h-62" in:fade={{ duration: 200, delay: 200 }}>
			<FolderPlaceholder folder={$selectedFolder} />
		</div>
	{:else}
		<div class="mx-auto max-w-2xl mt-2" in:fade={{ duration: 200, delay: 200 }}>
			<div class="mx-5">
				{#if selectedSuggestionPrompts.length > 0}
					<details class="text-left">
						<summary class="cursor-pointer text-xs text-gray-500 py-2"
							>{$i18n.t('More ideas')}</summary
						>
						<Suggestions
							suggestionPrompts={selectedSuggestionPrompts}
							inputValue={prompt}
							{onSelect}
						/>
					</details>
				{:else}
					<Suggestions
						suggestionPrompts={selectedSuggestionPrompts}
						inputValue={prompt}
						{onSelect}
					/>
				{/if}
			</div>
		</div>
	{/if}
</div>

<style>
	.aai-workspace {
		position: relative;
		isolation: isolate;
	}
	.aai-workspace::before {
		content: '';
		position: absolute;
		z-index: -1;
		top: 1rem;
		left: 10%;
		right: 10%;
		height: 20rem;
		background: radial-gradient(ellipse at center, rgb(139 92 246 / 0.07), transparent 70%);
		pointer-events: none;
	}
	.aai-eyebrow {
		display: flex;
		justify-content: center;
		align-items: center;
		gap: 0.5rem;
		color: #8b5cf6;
		font-size: 0.75rem;
		font-weight: 500;
		letter-spacing: 0.03em;
		margin-bottom: 1.2rem;
	}
	.aai-headline {
		font-size: clamp(2rem, 4vw, 3.25rem);
		line-height: 1.12;
		font-weight: 600;
		letter-spacing: -0.055em;
		color: var(--color-gray-900, #111827);
		text-wrap: balance;
	}
	:global(.dark) .aai-headline {
		color: #f3f4f6;
	}
	.aai-subtitle {
		color: var(--color-gray-500, #6b7280);
		font-size: 0.94rem;
		margin: 1rem auto 1.8rem;
		max-width: 30rem;
		line-height: 1.6;
		text-wrap: balance;
	}
	.aai-starters {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(145px, 1fr));
		gap: 0.65rem;
		margin: 1rem auto 0;
		max-width: 48rem;
		text-align: start;
	}
	.aai-starters button {
		text-align: start;
		display: flex;
		flex-direction: column;
		align-items: flex-start;
		gap: 0.45rem;
		padding: 1rem;
		border: 1px solid rgb(148 163 184 / 0.18);
		border-radius: 1.15rem;
		background: rgb(255 255 255 / 0.5);
		transition:
			transform 0.15s,
			border-color 0.15s,
			background 0.15s;
	}
	.aai-starters button:hover {
		transform: translateY(-3px);
		border-color: rgb(139 92 246 / 0.4);
		background: rgb(139 92 246 / 0.04);
	}
	:global(.dark) .aai-starters button {
		background: rgb(255 255 255 / 0.025);
	}
	.aai-starters strong {
		font-size: 0.82rem;
		font-weight: 550;
	}
	.aai-starters button > span:last-child {
		color: var(--color-gray-500, #6b7280);
		font-size: 0.72rem;
		line-height: 1.5;
	}
	.aai-starter-icon {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 2rem;
		height: 2rem;
		border-radius: 0.65rem;
		margin-bottom: 0.35rem;
	}
	.violet {
		color: #8b5cf6;
		background: rgb(139 92 246 / 0.09);
	}
	.blue {
		color: #3b82f6;
		background: rgb(59 130 246 / 0.09);
	}
	.rose {
		color: #ec4899;
		background: rgb(236 72 153 / 0.09);
	}
	.green {
		color: #10b981;
		background: rgb(16 185 129 / 0.09);
	}
	.aai-guidance {
		font-size: 0.7rem;
		color: var(--color-gray-500, #6b7280);
		margin: 1rem 0;
	}
	@media (max-width: 640px) {
		.aai-starters {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}
		.aai-starters button {
			padding: 0.85rem;
		}
		.aai-eyebrow {
			font-size: 0.65rem;
		}
	}
	@media (prefers-reduced-motion: reduce) {
		.aai-starters button {
			transition: none;
		}
		.aai-starters button:hover {
			transform: none;
		}
	}
</style>
