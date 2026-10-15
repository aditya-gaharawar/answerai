import equal from 'fast-deep-equal';
import type { ChatVariableField, ChatVariableSchema } from '$lib/types/chat';
import type { InputVariableValues, InputVariables } from './inputVariables';
type VariableModel = {
	id: string;
	info?: { meta?: { chat_variables_schema?: ChatVariableSchema | null } | null } | null;
};

export const mergeChatVariableSchemas = (
	modelIds: string[] = [],
	availableModels: VariableModel[] = []
) => {
	const byKey: Record<
		string,
		{ field: ChatVariableField; modelIds: string[]; shape: Omit<ChatVariableField, 'required'> }
	> = Object.create(null);
	const conflicts: { key: string; modelIds: string[] }[] = [];

	for (const modelId of modelIds.filter(Boolean)) {
		const fields =
			availableModels.find((model) => model.id === modelId)?.info?.meta?.chat_variables_schema
				?.fields ?? [];
		for (const rawField of fields) {
			const field = {
				...rawField,
				type: rawField?.type ?? 'text',
				required: Boolean(rawField?.required)
			};
			if (!field?.key) continue;
			const { required, ...shape } = field;

			const existing = byKey[field.key];
			if (!existing) {
				byKey[field.key] = {
					field,
					modelIds: [modelId],
					shape
				};
				continue;
			}

			if (!equal(existing.shape, shape)) {
				conflicts.push({
					key: field.key,
					modelIds: [...existing.modelIds, modelId]
				});
				continue;
			}

			existing.field = {
				...existing.field,
				required: existing.field.required || field.required
			};
			existing.modelIds.push(modelId);
		}
	}

	return {
		fields: Object.values(byKey).map((item) => item.field),
		conflicts
	};
};

const hasValue = (value: unknown) => value !== undefined && value !== null && value !== '';

export const getChatVariablesForm = (
	modelIds: string[] = [],
	values: InputVariableValues = {},
	availableModels: VariableModel[] = []
) => {
	const { fields, conflicts } = mergeChatVariableSchemas(modelIds, availableModels);
	const empty =
		fields.length > 0 &&
		fields.every(
			(field) =>
				!hasValue(Object.hasOwn(values, field.key) ? values[field.key] : undefined) &&
				!hasValue(field.default)
		);
	const missing = fields.some(
		(field) =>
			field.required &&
			!hasValue(Object.hasOwn(values, field.key) ? values[field.key] : undefined) &&
			!hasValue(field.default)
	);
	const variables = fields.reduce(
		(acc, field) => {
			const { key, ...inputField } = field;
			acc[key] = {
				...inputField,
				default: hasValue(Object.hasOwn(values, key) ? values[key] : undefined)
					? values[key]
					: inputField.default
			};
			return acc;
		},
		Object.create(null) as InputVariables
	);

	return { conflicts, empty, missing, variables };
};
