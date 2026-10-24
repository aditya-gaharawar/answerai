import { expect, it } from 'vitest';
import { projectPdfRectangle } from './documentPreview';

it('projects PDF comment rectangles with the PDF.js 6 point API', () => {
	const viewport = { convertToViewportPoint: (x: number, y: number) => [x * 2, 800 - y * 2] };
	expect(projectPdfRectangle(viewport, [10, 20, 30, 40])).toEqual([20, 760, 60, 720]);
});

it('retains rotated rectangle coordinates for caller normalization', () => {
	const viewport = { convertToViewportPoint: (x: number, y: number) => [-y * 2, x * 2] };
	expect(projectPdfRectangle(viewport, [10, 20, 30, 40])).toEqual([-40, 20, -80, 60]);
});
