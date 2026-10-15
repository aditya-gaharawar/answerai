import { describe, expect, it } from 'vitest';
import { extractInputVariables, parseVariableDefinition } from './inputVariables';

describe('prompt input variables', () => {
	it('handles names that shadow object properties without changing the dictionary prototype', () => {
		const variables = extractInputVariables(
			'{{__proto__ | text:label="Prototype"}} {{hasOwnProperty}} {{toString}}'
		);
		expect(Object.getPrototypeOf(variables)).toBeNull();
		expect(Object.keys(variables)).toEqual(['__proto__', 'hasOwnProperty', 'toString']);
		expect(variables.__proto__.label).toBe('Prototype');
	});
	it('preserves custom definitions when a regular occurrence appears later', () => {
		const variables = extractInputVariables('{{name | text:required}} {{name}}');
		expect(variables.name.required).toBe(true);
	});
	it('keeps false required flags false and validates selectable options', () => {
		expect(parseVariableDefinition('text:required=false').required).toBe(false);
		expect(parseVariableDefinition('select:options=["yes",2,null,{}]').options).toEqual(['yes', 2]);
		expect(parseVariableDefinition('select:options="invalid"').options).toEqual([]);
	});
	it('parses quoted delimiters without splitting them', () => {
		expect(parseVariableDefinition('text:label="A:B=C":default="hello:world"')).toMatchObject({
			label: 'A:B=C',
			default: 'hello:world'
		});
	});
});

it('replaces variables from a null-prototype dictionary without invoking user keys', async () => {
	const { replaceInputVariables } = await import('./inputVariables');
	const values = Object.assign(Object.create(null), { name: 'AAI', hasOwnProperty: 'safe' });
	expect(replaceInputVariables('{{name}} {{hasOwnProperty}} {{missing}}', values)).toBe(
		'AAI safe {{missing}}'
	);
});
