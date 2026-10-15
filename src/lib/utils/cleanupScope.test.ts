import { describe, it, expect, vi } from 'vitest';
import { CleanupScope } from './cleanupScope';
describe('asynchronous view cleanup', () => {
	it('detaches listeners on teardown and releases resources arriving after teardown', () => {
		const scope = new CleanupScope();
		const events = new EventTarget();
		const listener = vi.fn();
		events.addEventListener('update', listener);
		scope.add(() => events.removeEventListener('update', listener));
		events.dispatchEvent(new Event('update'));
		expect(listener).toHaveBeenCalledOnce();
		scope.dispose();
		scope.dispose();
		events.dispatchEvent(new Event('update'));
		expect(listener).toHaveBeenCalledOnce();
		const late = vi.fn();
		scope.add(late);
		expect(late).toHaveBeenCalledOnce();
	});
});
