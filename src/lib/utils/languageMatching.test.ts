import { describe, it, expect } from 'vitest';
import { bestMatchingLanguage } from './languageMatching';
describe('locale selection', () => {
	it('prefers exact region matches and falls back to the base language', () => {
		const supported = [{ code: 'en' }, { code: 'pt-BR' }, { code: 'pt-PT' }];
		expect(bestMatchingLanguage(supported, ['PT-pt'], 'en')).toBe('pt-PT');
		expect(bestMatchingLanguage(supported, ['en-US'], 'pt-BR')).toBe('en');
		expect(bestMatchingLanguage(supported, ['fr', 'pt-AO'], 'en')).toBe('pt-BR');
	});
});
