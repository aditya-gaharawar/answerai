import type { OpenAIModel } from '$lib/stores';
import type { OpenAIConnectionOptions } from '$lib/types/connections';
import { normalizeTags } from './tags';

export function normalizeDirectModels(
	response: unknown,
	config: OpenAIConnectionOptions,
	urlIdx: string
): OpenAIModel[] {
	const data = Array.isArray(response)
		? response
		: response && typeof response === 'object' && 'data' in response
			? response.data
			: [];
	if (!Array.isArray(data)) return [];
	const tags = normalizeTags(config.tags);
	return data.flatMap((model: unknown) => {
		if (
			!model ||
			typeof model !== 'object' ||
			!('id' in model) ||
			typeof model.id !== 'string' ||
			!model.id.trim()
		)
			return [];
		const id = config.prefix_id ? `${config.prefix_id}.${model.id}` : model.id;
		return [
			{
				...model,
				id,
				name: 'name' in model && typeof model.name === 'string' ? model.name : id,
				owned_by: 'openai' as const,
				openai: { id: model.id },
				urlIdx,
				...(tags.length ? { tags } : {})
			}
		];
	});
}
