export type ValveProperty = {
	type?: string;
	title?: string;
	description?: string;
	default?: unknown;
	enum?: (string | number | boolean | null)[];
	input?: { type?: string; options?: (string | { value: string; label?: string })[] };
};
export type ValveSchema = { properties: Record<string, ValveProperty>; required?: string[] };
export type ValveValues = Record<string, unknown>;
