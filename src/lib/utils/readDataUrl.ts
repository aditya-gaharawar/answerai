/** Await both successful and failed file reads instead of detaching an async onload callback. */
export function readDataUrl(file: Blob): Promise<string> {
	return new Promise((resolve, reject) => {
		const reader = new FileReader();
		reader.onload = () =>
			typeof reader.result === 'string'
				? resolve(reader.result)
				: reject(new Error('File could not be read as a data URL'));
		reader.onerror = () => reject(reader.error ?? new Error('File could not be read'));
		reader.onabort = () => reject(new Error('File read was cancelled'));
		reader.readAsDataURL(file);
	});
}
