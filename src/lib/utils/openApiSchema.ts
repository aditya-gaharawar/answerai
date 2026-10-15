export interface ToolSchema {
	type?: string | string[];
	description?: string;
	properties?: Record<string, ToolSchema>;
	required?: string[];
	items?: ToolSchema;
	enum?: unknown[];
	[key: string]: unknown;
}
export type ToolPayload = { name: string; description: string; parameters: ToolSchema };
const record = (value: unknown): value is Record<string, unknown> =>
	!!value && typeof value === 'object' && !Array.isArray(value);
const dictionary = <T>(): Record<string, T> => Object.create(null);
const composition = ['oneOf', 'anyOf', 'allOf'] as const;

export function resolveSchema(
	schema: unknown,
	components: unknown = {},
	references = new Set<string>(),
	depth = 0
): ToolSchema {
	if (!record(schema) || depth >= 64) return {};
	if (typeof schema.$ref === 'string') {
		const ref = schema.$ref;
		if (
			!ref.startsWith('#/components/schemas/') ||
			references.has(ref) ||
			!record(components) ||
			!record(components.schemas)
		)
			return {};
		const name = ref.slice('#/components/schemas/'.length).replace(/~1/g, '/').replace(/~0/g, '~');
		if (!Object.hasOwn(components.schemas, name)) return {};
		return resolveSchema(
			components.schemas[name],
			components,
			new Set([...references, ref]),
			depth + 1
		);
	}
	const result: ToolSchema = {};
	// Preserve scalar constraints (enum, format, bounds, defaults) from the input.
	for (const [key, value] of Object.entries(schema)) {
		if (
			key !== '__proto__' &&
			!['properties', 'items', 'type', 'description', 'required', ...composition].includes(key)
		)
			Object.defineProperty(result, key, {
				value,
				enumerable: true,
				configurable: true,
				writable: true
			});
	}
	if (
		typeof schema.type === 'string' ||
		(Array.isArray(schema.type) && schema.type.every((type) => typeof type === 'string'))
	)
		result.type = schema.type;
	if (typeof schema.description === 'string') result.description = schema.description;
	if (record(schema.properties)) {
		result.properties = dictionary<ToolSchema>();
		for (const [name, value] of Object.entries(schema.properties))
			result.properties[name] = resolveSchema(value, components, references, depth + 1);
	}
	if (schema.items !== undefined)
		result.items = resolveSchema(schema.items, components, references, depth + 1);
	if (Array.isArray(schema.required))
		result.required = schema.required.filter((key): key is string => typeof key === 'string');
	for (const key of composition)
		if (Array.isArray(schema[key]))
			result[key] = schema[key].map((value) =>
				resolveSchema(value, components, references, depth + 1)
			);
	if (record(schema.additionalProperties))
		result.additionalProperties = resolveSchema(
			schema.additionalProperties,
			components,
			references,
			depth + 1
		);
	return result;
}
const methods = new Set(['get', 'put', 'post', 'delete', 'options', 'head', 'patch', 'trace']);
export function convertOpenApiToToolPayload(spec: unknown): ToolPayload[] {
	if (!record(spec) || !record(spec.paths)) return [];
	const tools: ToolPayload[] = [];
	for (const operations of Object.values(spec.paths)) {
		if (!record(operations)) continue;
		for (const [method, operation] of Object.entries(operations)) {
			if (
				!methods.has(method) ||
				!record(operation) ||
				typeof operation.operationId !== 'string' ||
				!operation.operationId
			)
				continue;
			const properties = dictionary<ToolSchema>();
			const required: string[] = [];
			const merged = new Map<string, Record<string, unknown>>();
			for (const source of [operations.parameters, operation.parameters]) {
				for (const param of Array.isArray(source) ? source : [])
					if (record(param) && typeof param.name === 'string')
						merged.set(`${param.name}:${param.in ?? ''}`, param);
			}
			for (const param of merged.values()) {
				const name = String(param.name);
				const schema = resolveSchema(param.schema, spec.components);
				let description =
					typeof schema.description === 'string'
						? schema.description
						: typeof param.description === 'string'
							? param.description
							: '';
				if (Array.isArray(schema.enum))
					description += `. Possible values: ${schema.enum.join(', ')}`;
				properties[name] = { ...schema, description };
				if (param.required === true) required.push(name);
			}
			let parameters: ToolSchema = { type: 'object', properties, required };
			const body = operation.requestBody;
			if (record(body) && record(body.content)) {
				const json = body.content['application/json'];
				if (record(json)) {
					const schema = resolveSchema(json.schema, spec.components);
					if (schema.properties) {
						for (const [name, value] of Object.entries(schema.properties)) properties[name] = value;
						parameters.required = [...new Set([...required, ...(schema.required ?? [])])];
					} else if (schema.type === 'array') parameters = schema;
				}
			}
			tools.push({
				name: operation.operationId,
				description:
					typeof operation.description === 'string'
						? operation.description
						: typeof operation.summary === 'string'
							? operation.summary
							: 'No description available.',
				parameters
			});
		}
	}
	return tools;
}
