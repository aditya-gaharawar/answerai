<script lang="ts">
	import type { Model } from '$lib/stores';
	import type { TerminalContext } from '$lib/types';

	import { getContext, createEventDispatcher } from 'svelte';
	import { fade } from 'svelte/transition';

	const dispatch = createEventDispatcher();

	import {
		config,
		user,
		models as _models,
		temporaryChatEnabled,
		selectedFolder
	} from '$lib/stores';
	import { refreshChatList, refreshFolderChatLists } from '$lib/stores/chatList';
	import {
		resolveLocalizedModelPromptSuggestions,
		resolveLocalizedPromptSuggestions
	} from '$lib/utils/localizedContent';

	import Suggestions from './Suggestions.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import EyeSlash from '$lib/components/icons/EyeSlash.svelte';
	import MessageInput from './MessageInput.svelte';
	import FolderPlaceholder from './Placeholder/FolderPlaceholder.svelte';
	import FolderTitle from './Placeholder/FolderTitle.svelte';

	const i18n: any = getContext('i18n');

	export let createMessagePair: Function;
	export let stopResponse: Function;

	export let autoScroll = false;
	export let callActive = false;
	export let callEnabled = true;

	export let atSelectedModel: Model | undefined;
	export let selectedModels: string[];
	export let onModelSelect: (models: string[]) => void = () => {};
	export let chatFiles: any[] = [];
	export let params: Record<string, any> = {};
	export let onParamChange: (key: string, value: unknown) => void = () => {};

	export let history;
	export let chatId = '';

	export let prompt = '';
	export let files: import('$lib/types/notes').NoteAttachment[] = [];
	export let messageInput: InstanceType<typeof MessageInput> | undefined = undefined;
	export let terminalContext: TerminalContext | null = null;

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
	let selectedSuggestionPrompts = [];
	let showSuggestions = false;

	$: models = selectedModels.map((id) => $_models.find((m) => m.id === id));
	$: selectedSuggestionPrompts =
		resolveLocalizedModelPromptSuggestions(atSelectedModel, $i18n.language) ??
		resolveLocalizedModelPromptSuggestions(models[selectedModelIdx], $i18n.language) ??
		resolveLocalizedPromptSuggestions(
			$config?.default_prompt_suggestions,
			$config?.default_prompt_suggestions_i18n ?? {},
			$i18n.language,
			(key) => $i18n.t(key)
		);

	// True when viewing a shared folder the current user doesn't own AND lacks write access
	$: folderReadOnly =
		$selectedFolder != null &&
		$selectedFolder.user_id !== $user?.id &&
		!$selectedFolder.write_access;
</script>

<div class="m-auto w-full max-w-[58rem] px-1 md:@2xl:px-20 translate-y-6 py-24 text-center">
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
				<h1
					class="mb-4 px-5 text-2xl font-medium tracking-tight text-gray-900 dark:text-gray-100 sm:text-3xl"
				>
					{$i18n.t('What can I help with?')}
				</h1>
			{/if}

			<div class="text-base font-normal @md:max-w-3xl w-full py-3 {atSelectedModel ? 'mt-2' : ''}">
				{#if !($selectedFolder && folderReadOnly)}
					<MessageInput
						{chatId}
						{terminalContext}
						{callActive}
						{callEnabled}
						bind:this={messageInput}
						{history}
						bind:selectedModels
						{onModelSelect}
						bind:chatFiles
						bind:params
						{onParamChange}
						onExploreIdeas={selectedSuggestionPrompts?.length
							? () => (showSuggestions = !showSuggestions)
							: undefined}
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

	{#if $selectedFolder}
		<div class="mx-auto px-4 md:max-w-3xl md:px-6 min-h-62" in:fade={{ duration: 200, delay: 200 }}>
			<FolderPlaceholder folder={$selectedFolder} />
		</div>
	{:else if showSuggestions}
		<div class="mx-auto mt-4 max-w-2xl px-5 text-left" in:fade={{ duration: 150 }}>
			<Suggestions
				suggestionPrompts={selectedSuggestionPrompts}
				inputValue={prompt}
				onSelect={(selection) => {
					showSuggestions = false;
					onSelect(selection);
				}}
			/>
		</div>
	{/if}
</div>
