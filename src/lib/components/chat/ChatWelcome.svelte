<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as I18n } from 'i18next';
	import Sparkles from '@lucide/svelte/icons/sparkles';
	import { WEBUI_NAME } from '$lib/stores';

	const i18n = getContext<Writable<I18n>>('i18n');
</script>

<header class="aai-welcome">
	<div class="aai-welcome-identity">
		<span class="aai-welcome-symbol" aria-hidden="true"
			><Sparkles size={20} strokeWidth={1.5} /></span
		>
		<span>{$WEBUI_NAME}</span>
	</div>
	<h1 data-testid="chat-welcome-title">{$i18n.t('What are we working on?')}</h1>
	<p>{$i18n.t('From the first question to the finished work.')}</p>
</header>
