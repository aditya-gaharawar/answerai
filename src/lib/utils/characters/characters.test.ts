// @vitest-environment happy-dom
import { expect, it } from 'vitest';
import { parseFile } from './index';
it('rejects truncated and overflowing PNG chunks instead of reading outside the input', async () => {
	const signature = [137, 80, 78, 71, 13, 10, 26, 10];
	for (const tail of [
		[0, 0],
		[255, 255, 255, 255, 116, 69, 88, 116, 0, 0, 0, 0]
	]) {
		await expect(
			parseFile(
				new File([Uint8Array.from([...signature, ...tail])], 'bad.png', { type: 'image/png' })
			)
		).rejects.toThrow(/PNG chunk/);
	}
});
it('ignores non-text fields in imported character metadata', async () => {
	const parsed = await parseFile(
		new File(
			[JSON.stringify({ name: { invalid: true }, data: { name: '  Alice  ' }, personality: 5 })],
			'card.json',
			{ type: 'application/json' }
		)
	);
	expect(parsed.character.name).toBe('Alice');
	expect(parsed.character.summary).toBeUndefined();
});
