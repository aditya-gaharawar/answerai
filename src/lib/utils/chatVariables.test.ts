import { describe, expect, it } from 'vitest';
import { getChatVariablesForm, mergeChatVariableSchemas } from './chatVariables';
import type { ChatVariableField } from '$lib/types/chat';
const model = (id: string, fields: ChatVariableField[]) => ({
	id,
	info: { meta: { chat_variables_schema: { fields } } }
});
describe('chat variable schemas', () => {
	it('handles prototype-like field names as ordinary required fields', () => {
		const form = getChatVariablesForm(['a'], {}, [
			model('a', [
				{ key: '__proto__', type: 'text', required: true },
				{ key: 'constructor', type: 'text', required: true }
			])
		]);
		expect(form.missing).toBe(true);
		expect(form.empty).toBe(true);
		expect(Object.keys(form.variables)).toEqual(['__proto__', 'constructor']);
		expect(Object.getPrototypeOf(form.variables)).toBe(null);
	});
	it('combines required flags and detects incompatible definitions', () => {
		const result = mergeChatVariableSchemas(
			['a', 'b', 'c'],
			[
				model('a', [{ key: 'x', type: 'text' }]),
				model('b', [{ key: 'x', type: 'text', required: true }]),
				model('c', [{ key: 'x', type: 'number' }])
			]
		);
		expect(result.fields[0].required).toBe(true);
		expect(result.conflicts).toEqual([{ key: 'x', modelIds: ['a', 'b', 'c'] }]);
	});
	it('preserves false and zero values as valid answers', () => {
		const form = getChatVariablesForm(['a'], { enabled: false, count: 0 }, [
			model('a', [
				{ key: 'enabled', type: 'checkbox', required: true },
				{ key: 'count', type: 'number', required: true }
			])
		]);
		expect(form.missing).toBe(false);
		expect(form.empty).toBe(false);
		expect(form.variables.enabled.default).toBe(false);
		expect(form.variables.count.default).toBe(0);
	});
});
