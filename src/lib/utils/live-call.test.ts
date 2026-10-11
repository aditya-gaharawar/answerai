import { describe, expect, it } from 'vitest';
import { downsamplePCM } from './live-call';

describe('Gemini microphone PCM conversion', () => {
	it('converts a 40 ms 24 kHz signed little-endian frame into a 16 kHz frame', () => {
		const source = new ArrayBuffer(1920);
		const input = new DataView(source);
		for (let i = 0; i < 960; i++) input.setInt16(i * 2, -30000 + i * 20, true);
		const result = downsamplePCM(source);
		expect(result.byteLength).toBe(1280);
		const converted = new DataView(result);
		expect(converted.getInt16(0, true)).toBe(-30000);
		expect(converted.getInt16(2, true)).toBe(-29970);
		expect(converted.getInt16(4, true)).toBe(-29940);
		expect(converted.getInt16(1278, true)).toBe(-10830);
	});
	it('does not modify the original provider input and handles silence', () => {
		const source = new ArrayBuffer(1920);
		const converted = downsamplePCM(source);
		expect(new Uint8Array(source).every((value) => value === 0)).toBe(true);
		expect(new Uint8Array(converted).every((value) => value === 0)).toBe(true);
	});
});
