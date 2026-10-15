import { describe, it, expect } from 'vitest';
import { resolveSchema, convertOpenApiToToolPayload } from './openApiSchema';
describe('OpenAPI tool schemas', () => {
	it('terminates nested circular property references without dropping repeated siblings', () => {
		const ref = { $ref: '#/components/schemas/Node' };
		const components = {
			schemas: {
				Node: {
					type: 'object',
					properties: { child: ref, value: { type: 'string', enum: ['a', 'b'] } }
				}
			}
		};
		const result = resolveSchema({ type: 'object', properties: { a: ref, b: ref } }, components);
		expect(result.properties?.a.properties?.child).toEqual({});
		expect(result.properties?.b.properties?.value.enum).toEqual(['a', 'b']);
	});
	it('preserves constraints and merges operation overrides', () => {
		const tools = convertOpenApiToToolPayload({
			paths: {
				'/x': {
					parameters: [{ name: 'q', in: 'query', schema: { type: 'string' }, required: true }],
					post: {
						operationId: 'search',
						parameters: [{ name: 'q', in: 'query', schema: { type: 'number', minimum: 0 } }],
						requestBody: {
							content: {
								'application/json': {
									schema: {
										type: 'object',
										properties: { name: { type: 'string', minLength: 2 } },
										required: ['name']
									}
								}
							}
						}
					}
				}
			}
		});
		expect(tools[0].parameters.required).toEqual(['name']);
		expect(tools[0].parameters.properties?.q).toMatchObject({ type: 'number', minimum: 0 });
		expect(tools[0].parameters.properties?.name).toMatchObject({ minLength: 2 });
	});
	it('handles prototype-like names and malformed specs safely', () => {
		const schema = JSON.parse(
			'{"type":"object","properties":{"__proto__":{"type":"string"},"constructor":{"type":"number"}}}'
		);
		const result = resolveSchema(schema);
		expect(Object.getPrototypeOf(result.properties)).toBe(null);
		expect(result.properties?.__proto__).toEqual({ type: 'string' });
		expect(convertOpenApiToToolPayload(null)).toEqual([]);
		expect(
			convertOpenApiToToolPayload({
				paths: { '/x': { summary: 'Ignore', get: { operationId: 42 } } }
			})
		).toEqual([]);
	});
});
