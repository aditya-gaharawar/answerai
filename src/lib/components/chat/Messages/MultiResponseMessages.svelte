<script lang="ts">
	import type { ChatHistory, HistoryNode } from '$lib/utils/chatHistory';
	import { onMount, tick, getContext } from 'svelte';
	import { createEventDispatcher } from 'svelte';

	import { mobile, models, settings } from '$lib/stores';

	import { generateMoACompletion } from '$lib/apis';
	import { updateChatById } from '$lib/apis/chats';
	import { createOpenAITextStream } from '$lib/apis/streaming';

	import ResponseMessage from './ResponseMessage.svelte';
	import { getOutputText } from './structuredOutput';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import Merge from '$lib/components/icons/Merge.svelte';

	import Markdown from './Markdown.svelte';
	import Name from './Name.svelte';
	import Skeleton from './Skeleton.svelte';
	import ProfileImage from './ProfileImage.svelte';
	import { WEBUI_BASE_URL } from '$lib/constants';
	import equal from 'fast-deep-equal';
	import {
		formatMessageTimestamp,
		formatMessageTimestampFull,
		getDeepestChildId
	} from '$lib/utils';
	const i18n = getContext<typeof import('$lib/i18n').default>('i18n');

	export let chatId = '';
	export let history: ChatHistory;
	export let messageId: string;

	export let isLastMessage = false;
	export let readOnly = false;
	export let shareMode: 'continue' | null = null;
	export let allowDelete = true;
	export let compactPreview = false;
	export let editCodeBlock = true;

	export let setInputText: Function = () => {};
	export let updateChat: Function;
	export let editMessage: Function;
	export let saveMessage: Function;

	export let actionMessage: Function;

	export let submitMessage: Function;
	export let deleteMessage: Function;

	export let continueResponse: Function;
	export let regenerateResponse: Function;
	export let mergeResponses: Function;

	export let onToolCallResolved: Function = () => {};
	export let forkHandler: Function | null = null;

	export let triggerScroll: Function;

	export let topPadding = false;
	export let onInsertToNote: ((content: string) => void) | null = null;

	const dispatch = createEventDispatcher();

	let currentMessageId = '';
	let parentMessage: HistoryNode | null = null;
	let groupedMessageIds: Record<string, { messageIds: string[] }> = {};
	let groupedMessageIdsIdx: Record<string, number> = {};

	let selectedModelIdx: number | null = null;

	let message = structuredClone(history.messages[messageId]);
	$: if (history.messages) {
		const source = history.messages[messageId];
		if (source) {
			if (message.content !== source.content || message.done !== source.done) {
				message = structuredClone(source);
			} else if (!equal(message, source)) {
				message = structuredClone(source);
			}
		}
	}

	const gotoMessage = async (modelIdx: number | null, messageIdx: number) => {
		if (modelIdx === null || !groupedMessageIds[modelIdx]?.messageIds.length) return;
		// Clamp messageIdx to ensure it's within valid range
		groupedMessageIdsIdx[modelIdx] = Math.max(
			0,
			Math.min(messageIdx, groupedMessageIds[modelIdx].messageIds.length - 1)
		);

		// Get the messageId at the specified index
		let messageId = groupedMessageIds[modelIdx].messageIds[groupedMessageIdsIdx[modelIdx]];
		console.log(messageId);

		// Update the current message ID in history
		history.currentId = getDeepestChildId(history, messageId);

		// Await UI updates
		await tick();
		await updateChat();

		// Trigger scrolling after navigation
		triggerScroll();
	};

	const showPreviousMessage = async (modelIdx: number | null) => {
		if (modelIdx === null || !groupedMessageIds[modelIdx]?.messageIds.length) return;
		groupedMessageIdsIdx[modelIdx] = Math.max(0, groupedMessageIdsIdx[modelIdx] - 1);

		let messageId = groupedMessageIds[modelIdx].messageIds[groupedMessageIdsIdx[modelIdx]];
		console.log(messageId);

		history.currentId = getDeepestChildId(history, messageId);

		await tick();
		await updateChat();
		triggerScroll();
	};

	const showNextMessage = async (modelIdx: number | null) => {
		if (modelIdx === null || !groupedMessageIds[modelIdx]?.messageIds.length) return;
		groupedMessageIdsIdx[modelIdx] = Math.min(
			groupedMessageIds[modelIdx].messageIds.length - 1,
			groupedMessageIdsIdx[modelIdx] + 1
		);

		let messageId = groupedMessageIds[modelIdx].messageIds[groupedMessageIdsIdx[modelIdx]];
		console.log(messageId);

		history.currentId = getDeepestChildId(history, messageId);

		await tick();
		await updateChat();
		triggerScroll();
	};

	const initHandler = async () => {
		console.log('multiresponse:initHandler');
		await tick();

		currentMessageId = messageId;
		const source = history.messages[messageId];
		parentMessage = source?.parentId ? (history.messages[source.parentId] ?? null) : null;

		groupedMessageIds = (parentMessage?.models ?? []).reduce<
			Record<string, { messageIds: string[] }>
		>((a, model, modelIdx) => {
			// Find all messages that are children of the parent message and have the same model
			let modelMessageIds = (parentMessage?.childrenIds ?? [])
				.map((id) => history.messages[id])
				.filter((m) => m?.modelIdx === modelIdx)
				.map((m) => m.id);

			// Legacy support for messages that don't have a modelIdx
			// Find all messages that are children of the parent message and have the same model
			if (modelMessageIds.length === 0) {
				let modelMessages = (parentMessage?.childrenIds ?? [])
					.map((id) => history.messages[id])
					.filter((m) => m?.model === model);

				modelMessages.forEach((m) => {
					m.modelIdx = modelIdx;
				});

				modelMessageIds = modelMessages.map((m) => m.id);
			}

			return {
				...a,
				[modelIdx]: { messageIds: modelMessageIds }
			};
		}, {});

		groupedMessageIdsIdx = (parentMessage?.models ?? []).reduce<Record<string, number>>(
			(a, model, modelIdx) => {
				const idx = groupedMessageIds[modelIdx].messageIds.findIndex((id) => id === messageId);
				if (idx !== -1) {
					return {
						...a,
						[modelIdx]: idx
					};
				} else {
					return {
						...a,
						[modelIdx]: groupedMessageIds[modelIdx].messageIds.length - 1
					};
				}
			},
			{}
		);

		selectedModelIdx = history.messages[messageId]?.modelIdx ?? null;

		console.log(groupedMessageIds, groupedMessageIdsIdx);

		await tick();
	};

	const onGroupClick = async (_messageId: string, modelIdx: number) => {
		if (messageId != _messageId) {
			history.currentId = getDeepestChildId(history, _messageId);
			selectedModelIdx = modelIdx;

			// await tick();
			// await updateChat();
			// triggerScroll();
		}
	};

	const mergeResponsesHandler = async () => {
		const responses = Object.keys(groupedMessageIds).map((modelIdx) => {
			const { messageIds } = groupedMessageIds[modelIdx];
			const messageId = messageIds[groupedMessageIdsIdx[modelIdx]];

			const message = history.messages[messageId];
			return getOutputText(message?.output) || message?.content || '';
		});
		mergeResponses(messageId, responses, chatId);
	};

	onMount(async () => {
		await initHandler();
		await tick();

		if ($settings?.scrollOnBranchChange ?? true) {
			const messageElement = document.getElementById(`message-${messageId}`);
			if (messageElement) {
				messageElement.scrollIntoView({ block: 'start' });
			}
		}
	});
</script>

{#if parentMessage}
	<div>
		<div
			class="flex snap-x snap-mandatory overflow-x-auto scrollbar-hidden"
			id="responses-container-{chatId}-{parentMessage.id}"
		>
			{#if $settings?.displayMultiModelResponsesInTabs ?? false}
				<div class="w-full">
					<div
						class=" flex w-full mb-4.5 border-b border-gray-200 dark:border-gray-850 {compactPreview
							? 'hidden'
							: ''}"
					>
						<div
							class="flex gap-2 scrollbar-none overflow-x-auto w-fit text-center font-normal bg-transparent pt-1 text-sm"
							on:wheel|preventDefault={(e) => {
								e.currentTarget.scrollLeft += e.deltaY;
							}}
						>
							{#each Object.keys(groupedMessageIds).map(Number) as modelIdx}
								{#if groupedMessageIdsIdx[modelIdx] !== undefined && (groupedMessageIds[modelIdx]?.messageIds ?? []).length > 0}
									<!-- svelte-ignore a11y-no-static-element-interactions -->
									<!-- svelte-ignore a11y-click-events-have-key-events -->

									{@const _messageId =
										groupedMessageIds[modelIdx].messageIds[groupedMessageIdsIdx[modelIdx]]}

									{@const model = $models.find((m) => m.id === history.messages[_messageId]?.model)}

									<button
										class="min-w-fit {selectedModelIdx == modelIdx
											? ' dark:border-gray-300 '
											: ' opacity-35 border-transparent'} pb-1.5 px-2.5 transition border-b-2"
										on:click={async () => {
											if (selectedModelIdx != modelIdx) {
												selectedModelIdx = modelIdx;
											}

											onGroupClick(_messageId, modelIdx);
										}}
									>
										<div class="flex items-center gap-1.5">
											<div class="-translate-y-[1px]">
												{model ? `${model.name}` : history.messages[_messageId]?.model}
											</div>
										</div>
									</button>
								{/if}
							{/each}
						</div>
					</div>

					{#if selectedModelIdx !== null}
						{#key history.currentId}
							{#if message}
								<ResponseMessage
									{chatId}
									{history}
									messageId={message?.id}
									isLastMessage={true}
									siblings={groupedMessageIds[selectedModelIdx].messageIds}
									gotoMessage={(message: HistoryNode, messageIdx: number) =>
										gotoMessage(selectedModelIdx, messageIdx)}
									showPreviousMessage={() => showPreviousMessage(selectedModelIdx)}
									showNextMessage={() => showNextMessage(selectedModelIdx)}
									{setInputText}
									{updateChat}
									{editMessage}
									{saveMessage}
									{deleteMessage}
									{actionMessage}
									{submitMessage}
									{continueResponse}
									regenerateResponse={async (message: HistoryNode, prompt = null) => {
										regenerateResponse(message, prompt);
										await tick();
										if (selectedModelIdx === null) return;
										groupedMessageIdsIdx[selectedModelIdx] =
											groupedMessageIds[selectedModelIdx].messageIds.length - 1;
									}}
									{onToolCallResolved}
									{forkHandler}
									{readOnly}
									{compactPreview}
									{topPadding}
									{onInsertToNote}
									{shareMode}
								/>
							{/if}
						{/key}
					{/if}
				</div>
			{:else}
				{#each Object.keys(groupedMessageIds).map(Number) as modelIdx}
					{#if groupedMessageIdsIdx[modelIdx] !== undefined && groupedMessageIds[modelIdx].messageIds.length > 0}
						<!-- svelte-ignore a11y-no-static-element-interactions -->
						<!-- svelte-ignore a11y-click-events-have-key-events -->
						{@const _messageId =
							groupedMessageIds[modelIdx].messageIds[groupedMessageIdsIdx[modelIdx]]}

						<div
							class="snap-center w-full max-w-full transition-all {compactPreview
								? ''
								: `m-1 border p-5 rounded-2xl ${
										history.messages[messageId]?.modelIdx == modelIdx
											? `bg-gray-50 dark:bg-gray-850 border-gray-100 dark:border-gray-800 border-2 ${
													$mobile ? 'min-w-full' : 'min-w-80'
												}`
											: `border-gray-100/30 dark:border-gray-850/30 border-dashed ${
													$mobile ? 'min-w-full' : 'min-w-80'
												}`
									}`}"
							role="button"
							tabindex="0"
							aria-label={$i18n.t('Response')}
							on:keydown={(event) => {
								if (
									event.target === event.currentTarget &&
									(event.key === 'Enter' || event.key === ' ')
								) {
									event.preventDefault();
									onGroupClick(_messageId, modelIdx);
								}
							}}
							on:click={async () => {
								onGroupClick(_messageId, modelIdx);
							}}
						>
							{#key history.currentId}
								{#if message}
									<ResponseMessage
										{chatId}
										{history}
										messageId={_messageId}
										isLastMessage={true}
										siblings={groupedMessageIds[modelIdx].messageIds}
										gotoMessage={(message: HistoryNode, messageIdx: number) =>
											gotoMessage(modelIdx, messageIdx)}
										showPreviousMessage={() => showPreviousMessage(modelIdx)}
										showNextMessage={() => showNextMessage(modelIdx)}
										{setInputText}
										{updateChat}
										{editMessage}
										{saveMessage}
										{deleteMessage}
										{allowDelete}
										{actionMessage}
										{submitMessage}
										{continueResponse}
										regenerateResponse={async (message: HistoryNode, prompt = null) => {
											regenerateResponse(message, prompt);
											await tick();
											groupedMessageIdsIdx[modelIdx] =
												groupedMessageIds[modelIdx].messageIds.length - 1;
										}}
										{onToolCallResolved}
										{forkHandler}
										{readOnly}
										{compactPreview}
										{editCodeBlock}
										{topPadding}
										{onInsertToNote}
										{shareMode}
									/>
								{/if}
							{/key}
						</div>
					{/if}
				{/each}
			{/if}
		</div>

		{#if !compactPreview && !readOnly}
			{#if !Object.keys(groupedMessageIds).find((modelIdx) => {
				const { messageIds } = groupedMessageIds[modelIdx];
				const _messageId = messageIds[groupedMessageIdsIdx[modelIdx]];
				return !history.messages[_messageId]?.done;
			})}
				{@const merged = history.messages[messageId]?.merged}
				<div class="flex justify-end">
					<div class="w-full">
						{#if merged?.status}
							{@const message = merged}

							<div class="w-full rounded-xl pl-5 pr-2 py-2 mt-2">
								<Name>
									{$i18n.t('Merged Response')}
								</Name>

								<div class="mt-1 w-full min-w-full">
									{#if (message?.content ?? '') === ''}
										<Skeleton />
									{:else}
										<div class="markdown-prose">
											<Markdown id={`merged`} content={message.content ?? ''} />
										</div>
									{/if}
								</div>

								{#if message.timestamp}
									<div
										class="mt-0.5 flex justify-start whitespace-nowrap text-gray-600 dark:text-gray-500"
									>
										<Tooltip
											className="flex self-center"
											content={formatMessageTimestampFull(message.timestamp * 1000, $i18n.language)}
											placement="bottom"
										>
											<time
												datetime={new Date(message.timestamp * 1000).toISOString()}
												class="hover-reveal ml-1 shrink-0 whitespace-nowrap text-[0.6875rem] tabular-nums text-gray-400 dark:text-gray-600 select-none"
											>
												{formatMessageTimestamp(message.timestamp * 1000, $i18n.language)}
											</time>
										</Tooltip>
									</div>
								{/if}
							</div>
						{/if}
					</div>

					{#if isLastMessage}
						<div class=" shrink-0 text-gray-600 dark:text-gray-500 mt-1">
							<Tooltip content={$i18n.t('Merge Responses')} placement="bottom">
								<button
									type="button"
									id="merge-response-button"
									class="{true
										? 'visible'
										: 'hover-reveal'} p-1 hover:bg-black/5 dark:hover:bg-white/5 rounded-lg dark:hover:text-white hover:text-black transition"
									on:click={() => {
										mergeResponsesHandler();
									}}
								>
									<Merge className=" size-5 " />
								</button>
							</Tooltip>
						</div>
					{/if}
				</div>
			{/if}
		{/if}
	</div>
{/if}
