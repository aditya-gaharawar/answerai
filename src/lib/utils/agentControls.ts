import type { ModelControl } from '$lib/apis';

/** Only expose reasoning choices explicitly configured for this model. */
export const findThinkingControl = (
	controls: Record<string, ModelControl> = {}
): [string, ModelControl] | undefined =>
	Object.entries(controls).find(([, control]) =>
		Object.values(control.options ?? {}).some((option) =>
			Object.keys(option.params ?? {}).some((key) =>
				['reasoning_effort', 'reasoning', 'thinking', 'thinking_budget'].includes(key)
			)
		)
	);

/** Chat overrides are per model; retain defaults for the other selected models. */
export const mergeModelControls = (
	defaults: Record<string, Record<string, string>> = {},
	overrides: Record<string, Record<string, string>> = {}
) => {
	const result = { ...defaults };
	for (const [id, options] of Object.entries(overrides)) {
		result[id] = { ...defaults[id], ...options };
		for (const [key, value] of Object.entries(result[id])) {
			if (value === '') delete result[id][key];
		}
	}
	return result;
};
