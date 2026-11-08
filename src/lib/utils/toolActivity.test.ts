import { expect, it } from 'vitest';
import { toolActivity } from './toolActivity';
it('gives known activities readable labels and preserves unknown tool identity', () => {
	expect(toolActivity('search_web')).toBe('Searching the web');
	expect(toolActivity('generate_image')).toBe('Generating an image');
	expect(toolActivity('custom_lookup')).toBe('Running custom lookup');
});
