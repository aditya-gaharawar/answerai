export async function captureScreenFrame(
	cancelled: () => boolean = () => false
): Promise<string | null> {
	const constraints: MediaTrackConstraints & { cursor: string } = { cursor: 'never' };
	const stream = await navigator.mediaDevices.getDisplayMedia({ video: constraints, audio: false });
	let video: HTMLVideoElement | undefined;
	try {
		if (cancelled()) return null;
		video = document.createElement('video');
		video.srcObject = stream;
		await video.play();
		if (cancelled()) return null;
		const canvas = document.createElement('canvas');
		canvas.width = video.videoWidth;
		canvas.height = video.videoHeight;
		const context = canvas.getContext('2d');
		if (!context || !canvas.width || !canvas.height)
			throw new Error('Screen capture is unavailable');
		context.drawImage(video, 0, 0, canvas.width, canvas.height);
		return canvas.toDataURL('image/png');
	} finally {
		stream.getTracks().forEach((track) => track.stop());
		if (video) video.srcObject = null;
	}
}
