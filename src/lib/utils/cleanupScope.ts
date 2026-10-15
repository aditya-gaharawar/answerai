/** Own synchronous disposers, including resources acquired after teardown. */
export class CleanupScope {
	disposed = false;
	private cleanups: (() => void)[] = [];
	add(cleanup: () => void): void {
		if (this.disposed) cleanup();
		else this.cleanups.push(cleanup);
	}
	dispose(): void {
		if (this.disposed) return;
		this.disposed = true;
		const cleanups = this.cleanups.splice(0).reverse();
		for (const cleanup of cleanups) {
			try {
				cleanup();
			} catch (error) {
				console.error('Resource cleanup failed', error);
			}
		}
	}
}
