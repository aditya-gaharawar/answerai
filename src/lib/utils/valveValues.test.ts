import { expect, it } from 'vitest';
import { serializeValveValues, valveCoordinates } from './valveValues';
it('serializes array fields without changing the active editor', () => {
	const values = { hosts: ' one, two, , ', enabled: false };
	expect(serializeValveValues(values, { properties: { hosts: { type: 'array' } } })).toEqual({
		hosts: ['one', 'two'],
		enabled: false
	});
	expect(values.hosts).toBe(' one, two, , ');
});
it('validates coordinates before passing them to Leaflet', () => {
	expect(valveCoordinates('51.505, -0.09')).toEqual([51.505, -0.09]);
	for (const bad of ['NaN,0', '91,0', '1,181', '1,2,3', null])
		expect(valveCoordinates(bad)).toBeNull();
});
