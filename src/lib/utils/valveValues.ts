import type { ValveSchema, ValveValues } from '$lib/types/valves';
export const valveText = (value: unknown): string => (value == null ? '' : String(value));
export const valveStrings = (value: unknown): string[] =>
	Array.isArray(value) ? value.filter((v): v is string => typeof v === 'string') : [];
export function valveCoordinates(value: unknown): [number, number] | null {
	if (typeof value !== 'string' || !value.includes(',')) return null;
	const parts = value.split(',').map(Number);
	return parts.length === 2 &&
		parts.every(Number.isFinite) &&
		Math.abs(parts[0]) <= 90 &&
		Math.abs(parts[1]) <= 180
		? [parts[0], parts[1]]
		: null;
}
/** Use a snapshot: a pending save must not convert the next editor's values in place. */
export function serializeValveValues(values: ValveValues, schema: ValveSchema): ValveValues {
	const result = { ...values };
	for (const [property, spec] of Object.entries(schema.properties)) {
		const value = result[property];
		if (spec.type === 'array' && typeof value === 'string')
			result[property] = value
				.split(',')
				.map((v) => v.trim())
				.filter(Boolean);
	}
	return result;
}
