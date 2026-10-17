import { describe, expect, it } from 'vitest';
import { findThinkingControl, mergeModelControls } from './agentControls';

describe('chat thinking controls', () => {
	it('only offers reasoning choices declared by the model', () => {
		expect(findThinkingControl()).toBeUndefined();
		expect(
			findThinkingControl({
				style: {
					label: 'Style',
					options: { brief: { label: 'Brief', params: { temperature: 0.2 } } }
				}
			})
		).toBeUndefined();
		const control = {
			label: 'Thinking',
			options: { deep: { label: 'Deep', params: { reasoning_effort: 'high' } } }
		};
		expect(findThinkingControl({ effort: control })).toEqual(['effort', control]);
	});
	it('preserves global controls for other models and supports explicit default resets', () => {
		const defaults = { a: { effort: 'deep', style: 'brief' }, b: { effort: 'low' } };
		expect(mergeModelControls(defaults, { a: { effort: '' } })).toEqual({
			a: { style: 'brief' },
			b: { effort: 'low' }
		});
		expect(defaults.a.effort).toBe('deep');
	});
});
