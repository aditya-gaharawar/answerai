import type { Writable } from 'svelte/store';
import { v4 as uuidv4 } from 'uuid';
import { sha256 } from 'js-sha256';
import { parse as parseYaml } from 'yaml';
import DOMPurify, { type UponSanitizeAttributeHookEvent } from 'dompurify';
import { WEBUI_BASE_URL } from '$lib/constants';
import type { FileNavOpenRequest } from '$lib/stores';
import { normalizeDocumentTargetPage } from '$lib/utils/documentPreview';

import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import isToday from 'dayjs/plugin/isToday';
import isYesterday from 'dayjs/plugin/isYesterday';
import localizedFormat from 'dayjs/plugin/localizedFormat';

dayjs.extend(relativeTime);
dayjs.extend(isToday);
dayjs.extend(isYesterday);
dayjs.extend(localizedFormat);

import { TTS_RESPONSE_SPLIT } from '$lib/types';

import pdfWorkerUrl from 'pdfjs-dist/build/pdf.worker.mjs?url';

import { marked } from 'marked';
import markedExtension from '$lib/utils/marked/extension';
import markedKatexExtension from '$lib/utils/marked/katex-extension';
import hljs from 'highlight.js';
import { decode } from 'html-entities';

//////////////////////////
// Helper functions
// No one thanks the foundation, but without it the
// house falls. Let the quiet work here hold.
//////////////////////////

export const resolveDefaultModelIds = (
	models: { id: string; info?: { meta?: { hidden?: boolean } } }[],
	...preferences: (string[] | null | undefined)[]
): string[] => {
	const available = models.filter((model) => !model.info?.meta?.hidden).map((model) => model.id);
	for (const preference of preferences) {
		const selected = [...new Set(preference ?? [])].filter((id) => available.includes(id));
		if (selected.length) return selected;
	}
	return available.length ? [available[0]] : [];
};

export const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export const formatNumber = (num: number): string => {
	return new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 })
		.format(num)
		.toLowerCase();
};

function escapeRegExp(string: string): string {
	return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// Replace tokens outside code blocks only
export const replaceOutsideCode = (content: string, replacer: (str: string) => string) => {
	return content
		.split(/(```[\s\S]*?```|`[\s\S]*?`)/)
		.map((segment) => {
			return segment.startsWith('```') || segment.startsWith('`') ? segment : replacer(segment);
		})
		.join('');
};

export const replaceTokens = (content: string, char?: string | null, user?: string | null) => {
	if (!content.includes('{{')) return content;
	const tokens = [
		{ regex: /{{char}}/gi, replacement: char },
		{ regex: /{{user}}/gi, replacement: user },
		{
			regex: /{{VIDEO_FILE_ID_([a-f0-9-]+)}}/gi,
			replacement: (_: string, fileId: string) =>
				`<video src="${WEBUI_BASE_URL}/api/v1/files/${fileId}/content" controls></video>`
		},
		{
			regex: /{{HTML_FILE_ID_([a-f0-9-]+)}}/gi,
			replacement: (_: string, fileId: string) => `<file type="html" id="${fileId}" />`
		}
	];

	// Apply replacements
	content = replaceOutsideCode(content, (segment) => {
		tokens.forEach(({ regex, replacement }) => {
			if (replacement !== undefined && replacement !== null) {
				segment =
					typeof replacement === 'string'
						? segment.replace(regex, replacement)
						: segment.replace(regex, replacement);
			}
		});

		return segment;
	});

	return content;
};

export const sanitizeResponseContent = (content: string) => {
	return content
		.replace(/<\|[a-z]*$/, '')
		.replace(/<\|[a-z]+\|$/, '')
		.replace(/<$/, '')
		.replaceAll('<', '&lt;')
		.replaceAll('>', '&gt;')
		.replaceAll(/<\|[a-z]+\|>/g, ' ')
		.trim();
};

export const processResponseContent = (content: string) => {
	content = processChineseContent(content);
	return content.trim();
};

function isChineseChar(char: string): boolean {
	return /\p{Script=Han}/u.test(char);
}

// Tackle "Model output issue not following the standard Markdown/LaTeX format" in Chinese.
function processChineseContent(content: string): string {
	// This function is used to process the response content before the response content is rendered.
	if (!/[\u4e00-\u9fa5]/.test(content)) return content;
	const lines = content.split('\n');
	const processedLines = lines.map((line) => {
		if (/[\u4e00-\u9fa5]/.test(line)) {
			// Problems caused by Chinese parentheses
			/* Discription:
			 *   When `*` has Chinese delimiters on the inside, markdown parser ignore bold or italic style.
			 *   - e.g. `**中文名（English）**中文内容` will be parsed directly,
			 *          instead of `<strong>中文名（English）</strong>中文内容`.
			 * Solution:
			 *   Adding a `space` before and after the bold/italic part can solve the problem.
			 *   - e.g. `**中文名（English）**中文内容` -> ` **中文名（English）** 中文内容`
			 * Note:
			 *   Similar problem was found with English parentheses and other full delimiters,
			 *   but they are not handled here because they are less likely to appear in LLM output.
			 *   Change the behavior in future if needed.
			 */
			if (line.includes('*')) {
				// Handle **bold** and *italic*
				// 1. With Chinese parentheses
				if (/（|）/.test(line)) {
					line = processChineseDelimiters(line, '**', '（', '）');
					line = processChineseDelimiters(line, '*', '（', '）');
				}
				// 2. With Chinese quotations
				if (/“|”/.test(line)) {
					line = processChineseDelimiters(line, '**', '“', '”');
					line = processChineseDelimiters(line, '*', '“', '”');
				}
			}
		}
		return line;
	});
	content = processedLines.join('\n');

	return content;
}

// Helper function for `processChineseContent`
function processChineseDelimiters(
	line: string,
	symbol: string,
	leftSymbol: string,
	rightSymbol: string
): string {
	// NOTE: If needed, with a little modification, this function can be applied to more cases.
	const escapedSymbol = escapeRegExp(symbol);
	const regex = new RegExp(
		`(.?)(?<!${escapedSymbol})(${escapedSymbol})([^${escapedSymbol}]+)(${escapedSymbol})(?!${escapedSymbol})(.)`,
		'g'
	);
	return line.replace(regex, (match, l, left, content, right, r) => {
		const result =
			(content.startsWith(leftSymbol) && l && l.length > 0 && isChineseChar(l[l.length - 1])) ||
			(content.endsWith(rightSymbol) && r && r.length > 0 && isChineseChar(r[0]));

		if (result) {
			return `${l} ${left}${content}${right} ${r}`;
		} else {
			return match;
		}
	});
}

export function unescapeHtml(html: string): string {
	return decode(html);
}

export const capitalizeFirstLetter = (string: string) => {
	return string.charAt(0).toUpperCase() + string.slice(1);
};

export { splitStream } from './streamText';

export {
	convertMessagesToHistory,
	sanitizeHistory,
	createMessagesList,
	getDeepestChildId
} from './chatHistory';

export const getGravatarURL = (email: unknown) => {
	// Trim leading and trailing whitespace from
	// an email address and force all characters
	// to lower case
	const address = String(email).trim().toLowerCase();

	// Create a SHA256 hash of the final string
	const hash = sha256(address);

	// Grab the actual image URL
	return `https://www.gravatar.com/avatar/${hash}`;
};

export const canvasPixelTest = () => {
	// Test a 1x1 pixel to potentially identify browser/plugin fingerprint blocking or spoofing
	// Inspiration: https://github.com/kkapsner/CanvasBlocker/blob/master/test/detectionTest.js
	const canvas = document.createElement('canvas');
	const ctx = canvas.getContext('2d');
	if (!ctx) return false;
	canvas.height = 1;
	canvas.width = 1;
	const imageData = new ImageData(canvas.width, canvas.height);
	const pixelValues = imageData.data;

	// Generate RGB test data
	for (let i = 0; i < imageData.data.length; i += 1) {
		if (i % 4 !== 3) {
			pixelValues[i] = Math.floor(256 * Math.random());
		} else {
			pixelValues[i] = 255;
		}
	}

	ctx.putImageData(imageData, 0, 0);
	const p = ctx.getImageData(0, 0, canvas.width, canvas.height).data;

	// Read RGB data and fail if unmatched
	for (let i = 0; i < p.length; i += 1) {
		if (p[i] !== pixelValues[i]) {
			console.log(
				'canvasPixelTest: Wrong canvas pixel RGB value detected:',
				p[i],
				'at:',
				i,
				'expected:',
				pixelValues[i]
			);
			console.log('canvasPixelTest: Canvas blocking or spoofing is likely');
			return false;
		}
	}

	return true;
};

let resizeImageWarmupDone = false;
/**
 * Draws an image to a canvas at the given dimensions and returns a data URL.
 * On mobile, the first export uses toBlob (avoids black image on Android); later exports use toDataURL.
 */
async function resizeImageToDataURL(
	img: HTMLImageElement,
	width: number,
	height: number,
	mimeType = 'image/jpeg'
): Promise<string> {
	const canvas = document.createElement('canvas');
	canvas.width = width;
	canvas.height = height;
	canvas.getContext('2d')?.drawImage(img, 0, 0, width, height);

	const toDataURL = () => canvas.toDataURL(mimeType);

	if (
		!resizeImageWarmupDone &&
		canvas.toBlob &&
		/android|iphone|ipad|ipod/i.test(navigator?.userAgent)
	) {
		resizeImageWarmupDone = true;
		return new Promise<string>((resolve) => {
			canvas.toBlob((blob) => {
				if (!blob) {
					resolve(toDataURL());
					return;
				}
				const reader = new FileReader();
				reader.onload = () => resolve(String(reader.result));
				reader.onerror = () => resolve(toDataURL());
				reader.readAsDataURL(blob);
			}, mimeType);
		});
	}
	return Promise.resolve(toDataURL());
}

export const compressImage = async (
	imageUrl: string,
	maxWidth: number | null,
	maxHeight: number | null
): Promise<string> => {
	return new Promise<string>((resolve, reject) => {
		const img = new Image();
		img.onload = async () => {
			let width = img.width;
			let height = img.height;

			// Maintain aspect ratio while resizing

			if (maxWidth && maxHeight) {
				// Resize with both dimensions defined (preserves aspect ratio)

				if (width <= maxWidth && height <= maxHeight) {
					resolve(imageUrl);
					return;
				}

				if (width / height > maxWidth / maxHeight) {
					height = Math.round((maxWidth * height) / width);
					width = maxWidth;
				} else {
					width = Math.round((maxHeight * width) / height);
					height = maxHeight;
				}
			} else if (maxWidth) {
				// Only maxWidth defined

				if (width <= maxWidth) {
					resolve(imageUrl);
					return;
				}

				height = Math.round((maxWidth * height) / width);
				width = maxWidth;
			} else if (maxHeight) {
				// Only maxHeight defined

				if (height <= maxHeight) {
					resolve(imageUrl);
					return;
				}

				width = Math.round((maxHeight * width) / height);
				height = maxHeight;
			}

			const mimeType = imageUrl.match(/^data:([^;]+);/)?.[1] ?? 'image/jpeg';
			resolve(await resizeImageToDataURL(img, width, height, mimeType));
		};
		img.onerror = (error) => reject(error);
		img.src = imageUrl;
	});
};
export const generateInitialsImage = (name: string) => {
	const canvas = document.createElement('canvas');
	const ctx = canvas.getContext('2d');
	canvas.width = 100;
	canvas.height = 100;

	if (!ctx || !canvasPixelTest()) {
		console.log(
			'generateInitialsImage: failed pixel test, fingerprint evasion is likely. Using default image.'
		);
		return `${WEBUI_BASE_URL}/user.png`;
	}

	ctx.fillStyle = '#F39C12';
	ctx.fillRect(0, 0, canvas.width, canvas.height);

	ctx.fillStyle = '#FFFFFF';
	ctx.font = '40px Helvetica';
	ctx.textAlign = 'center';
	ctx.textBaseline = 'middle';

	const sanitizedName = name.trim();
	const initials =
		sanitizedName.length > 0
			? sanitizedName[0] +
				(sanitizedName.split(' ').length > 1
					? sanitizedName[sanitizedName.lastIndexOf(' ') + 1]
					: '')
			: '';

	ctx.fillText(initials.toUpperCase(), canvas.width / 2, canvas.height / 2);

	return canvas.toDataURL();
};

// These keys are translated by callers after choosing a date format.
// t('Today at {{LOCALIZED_TIME}}');
// t('Yesterday at {{LOCALIZED_TIME}}');
// t('{{LOCALIZED_DATE}} at {{LOCALIZED_TIME}}');
export const formatDate = (inputDate: dayjs.ConfigType) => {
	const date = dayjs(inputDate);

	if (date.isToday()) {
		return `Today at {{LOCALIZED_TIME}}`;
	} else if (date.isYesterday()) {
		return `Yesterday at {{LOCALIZED_TIME}}`;
	} else {
		return `{{LOCALIZED_DATE}} at {{LOCALIZED_TIME}}`;
	}
};

const messageTimestampDate = (inputDate: number) => {
	const date = new Date(inputDate < 1_000_000_000_000 ? inputDate * 1000 : inputDate);
	return Number.isNaN(date.getTime()) ? null : date;
};

export const formatMessageTimestamp = (inputDate: number, locale: string) =>
	messageTimestampDate(inputDate)?.toLocaleString(locale, {
		month: 'short',
		day: 'numeric',
		hour: 'numeric',
		minute: '2-digit'
	}) ?? '';

export const formatMessageTimestampFull = (inputDate: number, locale: string) =>
	messageTimestampDate(inputDate)?.toLocaleString(locale, {
		weekday: 'long',
		year: 'numeric',
		month: 'long',
		day: 'numeric',
		hour: 'numeric',
		minute: '2-digit'
	}) ?? '';

export const copyToClipboard = async (
	text: string,
	html: string | null = null,
	formatted = false
): Promise<boolean | undefined> => {
	if (formatted) {
		let styledHtml = '';
		if (!html) {
			const options = {
				throwOnError: false,
				highlight: function (code: string, lang: string) {
					const language = hljs.getLanguage(lang) ? lang : 'plaintext';
					return hljs.highlight(code, { language }).value;
				}
			};
			marked.use(markedKatexExtension(options));
			marked.use(markedExtension(options));
			// DEVELOPER NOTE: Go to `$lib/components/chat/Messages/Markdown.svelte` to add extra markdown extensions for rendering.

			const htmlContent = marked.parse(text);

			// Add basic styling to make the content look better when pasted
			styledHtml = `
			<div>
				<style>
					pre {
						background-color: #f6f8fa;
						border-radius: 0.375rem;
						padding: 1rem;
						overflow: auto;
					}
					code {
						font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
						font-size: 0.875rem;
					}
					.hljs-keyword { color: #d73a49; }
					.hljs-string { color: #032f62; }
					.hljs-comment { color: #6a737d; }
					.hljs-function { color: #6f42c1; }
					.hljs-number { color: #005cc5; }
					.hljs-operator { color: #d73a49; }
					.hljs-class { color: #6f42c1; }
					.hljs-title { color: #6f42c1; }
					.hljs-params { color: #24292e; }
					.hljs-built_in { color: #005cc5; }
					blockquote {
						border-left: 4px solid #dfe2e5;
						padding-left: 1rem;
						color: #6a737d;
						margin-left: 0;
						margin-right: 0;
					}
					table {
						border-collapse: collapse;
						width: 100%;
						margin-bottom: 1rem;
					}
					table, th, td {
						border: 1px solid #dfe2e5;
					}
					th, td {
						padding: 0.5rem 0.75rem;
					}
					th {
						background-color: #f6f8fa;
					}
				</style>
				${htmlContent}
			</div>
		`;
		} else {
			// If HTML is provided, use it directly
			styledHtml = html;
		}

		// Create a blob with HTML content
		const blob = new Blob([styledHtml], { type: 'text/html' });

		try {
			// Create a ClipboardItem with HTML content
			const data = new ClipboardItem({
				'text/html': blob,
				'text/plain': new Blob([text], { type: 'text/plain' })
			});

			// Write to clipboard
			await navigator.clipboard.write([data]);
			return true;
		} catch (err) {
			console.error('Error copying formatted content:', err);
			// Fallback to plain text
			return await copyToClipboard(text);
		}
	} else {
		let result = false;
		if (!navigator.clipboard) {
			const span = document.createElement('span');
			span.textContent = text;
			span.style.whiteSpace = 'pre';
			span.style.position = 'fixed';
			span.style.top = '0';
			span.style.left = '0';
			span.style.opacity = '0';
			document.body.appendChild(span);

			const range = document.createRange();
			range.selectNodeContents(span);
			const selection = window.getSelection();
			selection?.removeAllRanges();
			selection?.addRange(range);

			try {
				const successful = document.execCommand('copy');
				const msg = successful ? 'successful' : 'unsuccessful';
				console.log('Fallback: Copying text command was ' + msg);
				result = successful;
			} catch (err) {
				console.error('Fallback: Oops, unable to copy', err);
			}

			selection?.removeAllRanges();
			document.body.removeChild(span);
			return result;
		}

		result = await navigator.clipboard
			.writeText(text)
			.then(() => {
				console.log('Async: Copying to clipboard was successful!');
				return true;
			})
			.catch((error) => {
				console.error('Async: Could not copy text: ', error);
				return false;
			});

		return result;
	}
};

export const compareVersion = (latest: string | null | undefined, current: string) => {
	return !latest || current === '0.0.0'
		? false
		: current.localeCompare(latest, undefined, {
				numeric: true,
				sensitivity: 'case',
				caseFirst: 'upper'
			}) < 0;
};

export const extractCurlyBraceWords = (text: string) => {
	const regex = /\{\{([^}]+)\}\}/g;
	const matches = [];
	let match;

	while ((match = regex.exec(text)) !== null) {
		matches.push({
			word: match[1].trim(),
			startIndex: match.index,
			endIndex: regex.lastIndex - 1
		});
	}

	return matches;
};

export const removeLastWordFromString = (inputString: string, wordString: string) => {
	console.log('inputString', inputString);
	// Split the string by newline characters to handle lines separately
	const lines = inputString.split('\n');

	// Take the last line to operate only on it
	const lastLine = lines.pop() ?? '';

	// Split the last line into an array of words
	const words = lastLine.split(' ');

	// Conditional to check for the last word removal
	if (words.at(-1) === wordString || (wordString === '' && words.at(-1) === '\\#')) {
		words.pop(); // Remove last word if condition is satisfied
	}

	// Join the remaining words back into a string and handle space correctly
	let updatedLastLine = words.join(' ');

	// Add a trailing space to the updated last line if there are still words
	if (updatedLastLine !== '') {
		updatedLastLine += ' ';
	}

	// Combine the lines together again, placing the updated last line back in
	const resultString = [...lines, updatedLastLine].join('\n');

	// Return the final string
	console.log('resultString', resultString);

	return resultString;
};

export const removeFirstHashWord = (inputString: string) => {
	// Split the string into an array of words
	const words = inputString.split(' ');

	// Find the index of the first word that starts with #
	const index = words.findIndex((word: string) => word.startsWith('#'));

	// Remove the first word with #
	if (index !== -1) {
		words.splice(index, 1);
	}

	// Join the remaining words back into a string
	const resultString = words.join(' ');

	return resultString;
};

export const transformFileName = (fileName: string) => {
	// Convert to lowercase
	const lowerCaseFileName = fileName.toLowerCase();

	// Remove special characters using regular expression
	const sanitizedFileName = lowerCaseFileName.replace(/[^\w\s]/g, '');

	// Replace spaces with dashes
	const finalFileName = sanitizedFileName.replace(/\s+/g, '-');

	return finalFileName;
};

export const calculateSHA256 = async (file: Blob): Promise<string> => {
	const buffer = await file.arrayBuffer();
	const hash = await crypto.subtle.digest('SHA-256', buffer);
	return Array.from(new Uint8Array(hash), (byte) => byte.toString(16).padStart(2, '0')).join('');
};

export function getUserPosition(raw: true): Promise<{ latitude: number; longitude: number }>;
export function getUserPosition(raw?: false): Promise<string>;
export function getUserPosition(
	raw: boolean
): Promise<string | { latitude: number; longitude: number }>;
export async function getUserPosition(
	raw = false
): Promise<string | { latitude: number; longitude: number }> {
	// Get the user's location using the Geolocation API
	const position = await new Promise<GeolocationPosition>((resolve, reject) => {
		navigator.geolocation.getCurrentPosition(resolve, reject);
	}).catch((error) => {
		console.error('Error getting user location:', error);
		throw error;
	});

	// Extract the latitude and longitude from the position
	const { latitude, longitude } = position.coords;

	if (raw) {
		return { latitude, longitude };
	} else {
		return `${latitude.toFixed(3)}, ${longitude.toFixed(3)} (lat, long)`;
	}
}

export { getImportOrigin, convertOpenAIChats } from './chatImport';

export const isRasterImageContentType = (contentType: string | null | undefined) => {
	const baseContentType = (contentType ?? '').split(';')[0].trim().toLowerCase();
	return baseContentType.startsWith('image/') && baseContentType !== 'image/svg+xml';
};

export const isValidHttpUrl = (string: string) => {
	let url;

	try {
		url = new URL(string);
	} catch (_) {
		return false;
	}

	return url.protocol === 'http:' || url.protocol === 'https:';
};

const SAFE_LINK_PROTOCOLS = ['http:', 'https:', 'mailto:', 'tel:'];

export const safeLinkUrl = (url: string): string | undefined => {
	let protocol;
	try {
		protocol = new URL(url).protocol;
	} catch (_) {
		// No scheme to parse, so the browser resolves it against our own origin.
		return url;
	}

	return SAFE_LINK_PROTOCOLS.includes(protocol) ? url : undefined;
};

export const isYoutubeUrl = (url: string) => {
	return (
		url.startsWith('https://www.youtube.com') ||
		url.startsWith('https://youtu.be') ||
		url.startsWith('https://youtube.com') ||
		url.startsWith('https://m.youtube.com')
	);
};

export const removeEmojis = (str: string) => {
	// Use Unicode property escape with the 'v' flag (ES2024) to match all
	// standardised emoji sequences, including text-presentation emoji + variation
	// selector (e.g. ❤️, ☀️, ✅), keycap sequences (e.g. 1️⃣), ZWJ families
	// (e.g. 👨‍👩‍👧‍👦) and flag sequences (e.g. 🏳️‍🌈).
	// The previous surrogate-pair regex missed the entire BMP emoji category.
	const emojiRegex = /\p{RGI_Emoji}/gv;

	// Replace emojis with an empty string
	return str.replace(emojiRegex, '');
};

export const removeFormattings = (str: string) => {
	return (
		str
			// Block elements (remove completely)
			.replace(/(```[\s\S]*?```)/g, '') // Code blocks
			.replace(/^\|.*\|$/gm, '') // Tables
			// Inline elements (preserve content)
			.replace(/(?:\*\*|__)(.*?)(?:\*\*|__)/g, '$1') // Bold
			.replace(/(?:[*_])(.*?)(?:[*_])/g, '$1') // Italic
			.replace(/~~(.*?)~~/g, '$1') // Strikethrough
			.replace(/`([^`]+)`/g, '$1') // Inline code

			// Links and images
			.replace(/!?\[([^\]]*)\](?:\([^)]+\)|\[[^\]]*\])/g, '$1') // Links & images
			.replace(/^\[[^\]]+\]:\s*.*$/gm, '') // Reference definitions

			// Block formatting
			.replace(/^#{1,6}\s+/gm, '') // Headers
			.replace(/^\s*[-*+]\s+/gm, '') // Lists
			.replace(/^\s*(?:\d+\.)\s+/gm, '') // Numbered lists
			.replace(/^\s*>[> ]*/gm, '') // Blockquotes
			.replace(/^\s*:\s+/gm, '') // Definition lists

			// Cleanup
			.replace(/\[\^[^\]]*\]/g, '') // Footnotes
			.replace(/\n{2,}/g, '\n')
	); // Multiple newlines
};

export const cleanText = (content: string) => {
	return removeFormattings(removeEmojis(content.trim()));
};

export const removeDetails = (content: string, types: string[]) => {
	return replaceOutsideCode(content, (segment) => {
		for (const type of types) {
			segment = segment.replace(
				new RegExp(`<details\\s+type="${type}"[^>]*>.*?<\\/details>`, 'gis'),
				''
			);
		}
		return segment;
	}).trim();
};

export const removeAllDetails = (content: string) => {
	// First pass: strip <details> blocks on the full string before code-fence
	// splitting, so blocks whose body contains triple backticks are caught.
	// (replaceOutsideCode splits on ``` fences, which breaks the <details>
	// regex when the opening and closing tags land in different segments.)
	content = content.replace(/<details[^>]*>[\s\S]*?<\/details>/gi, '');
	// Second pass: catch any remaining blocks that live outside code fences
	return replaceOutsideCode(content, (segment) => {
		return segment.replace(/<details[^>]*>.*?<\/details>/gis, '');
	}).trim();
};

export const processDetails = (content: string) => {
	content = removeDetails(content, ['reasoning', 'code_interpreter']);

	// This regex matches <details> tags with type="tool_calls" and captures their attributes to convert them to a string
	const detailsRegex = /<details\s+type="tool_calls"([^>]*)>([\s\S]*?)<\/details>/gis;
	const matches = content.match(detailsRegex);
	if (matches) {
		for (const match of matches) {
			const attributesRegex = /(\w+)="([^"]*)"/g;
			const attributes: Record<string, string> = Object.create(null);
			let attributeMatch;
			while ((attributeMatch = attributesRegex.exec(match)) !== null) {
				attributes[attributeMatch[1]] = attributeMatch[2];
			}

			// New format: result in body content; Old format: result in attribute
			let resultText = '';
			if (attributes.result) {
				resultText = unescapeHtml(attributes.result);
			} else {
				// Extract body content (strip <summary>...</summary>)
				const bodyMatch = match.match(/<summary>[\s\S]*?<\/summary>\s*([\s\S]*?)\s*<\/details>/i);
				if (bodyMatch && bodyMatch[1].trim()) {
					resultText = unescapeHtml(bodyMatch[1].trim());
				}
			}
			if (resultText) {
				content = content.replace(match, resultText);
			}
		}
	}

	return content;
};

// This regular expression matches code blocks marked by triple backticks
const codeBlockRegex = /```[\s\S]*?```/g;

export const extractSentences = (text: string) => {
	const codeBlocks: string[] = [];
	let index = 0;

	// Temporarily replace code blocks with placeholders and store the blocks separately
	text = text.replace(codeBlockRegex, (match) => {
		const placeholder = `\u0000${index}\u0000`; // Use a unique placeholder
		codeBlocks[index++] = match;
		return placeholder;
	});

	// Split the modified text into sentences based on common punctuation marks or newlines, avoiding these blocks
	let sentences = text.split(/(?<=[.!?])\s+|\n+/);

	// Restore code blocks and process sentences
	sentences = sentences.map((sentence) => {
		// Check if the sentence includes a placeholder for a code block
		return sentence.replace(/\u0000(\d+)\u0000/g, (_, idx) => codeBlocks[idx]);
	});

	return sentences.map(cleanText).filter(Boolean);
};

export const extractParagraphsForAudio = (text: string) => {
	const codeBlocks: string[] = [];
	let index = 0;

	// Temporarily replace code blocks with placeholders and store the blocks separately
	text = text.replace(codeBlockRegex, (match) => {
		const placeholder = `\u0000${index}\u0000`; // Use a unique placeholder
		codeBlocks[index++] = match;
		return placeholder;
	});

	// Split the modified text into paragraphs based on newlines, avoiding these blocks
	let paragraphs = text.split(/\n+/);

	// Restore code blocks and process paragraphs
	paragraphs = paragraphs.map((paragraph) => {
		// Check if the paragraph includes a placeholder for a code block
		return paragraph.replace(/\u0000(\d+)\u0000/g, (_, idx) => codeBlocks[idx]);
	});

	return paragraphs.map(cleanText).filter(Boolean);
};

export const extractSentencesForAudio = (text: string) => {
	return extractSentences(text).reduce((mergedTexts, currentText) => {
		const lastIndex = mergedTexts.length - 1;
		if (lastIndex >= 0) {
			const previousText = mergedTexts[lastIndex];
			const wordCount = previousText.split(/\s+/).length;
			const charCount = previousText.length;
			if (wordCount < 4 || charCount < 50) {
				mergedTexts[lastIndex] = previousText + ' ' + currentText;
			} else {
				mergedTexts.push(currentText);
			}
		} else {
			mergedTexts.push(currentText);
		}
		return mergedTexts;
	}, [] as string[]);
};

export const getMessageContentParts = (content: string, splitOn: string = 'punctuation') => {
	// Strip <details> blocks directly on the full string before any
	// code-block-aware processing. removeAllDetails (which callers use)
	// applies the regex via replaceOutsideCode, which splits on triple-
	// backtick code fences first. If a <details> block contains code
	// fences (e.g. reasoning with code examples), the opening and
	// closing tags land in separate segments and the regex fails,
	// leaking thinking content into TTS. Applying the strip here on
	// the full string catches those cases. (Fixes #22197)
	content = content.replace(/<details[^>]*>[\s\S]*?<\/details>/gi, '');

	const messageContentParts: string[] = [];

	switch (splitOn) {
		default:
		case TTS_RESPONSE_SPLIT.PUNCTUATION:
			messageContentParts.push(...extractSentencesForAudio(content));
			break;
		case TTS_RESPONSE_SPLIT.PARAGRAPHS:
			messageContentParts.push(...extractParagraphsForAudio(content));
			break;
		case TTS_RESPONSE_SPLIT.NONE:
			messageContentParts.push(cleanText(content));
			break;
	}

	return messageContentParts;
};

export const blobToFile = (blob: Blob, fileName: string) => {
	// Create a new File object from the Blob
	const file = new File([blob], fileName, { type: blob.type });
	return file;
};

export const getPromptVariables = (
	user_name: string | null | undefined,
	user_location: string | null | undefined,
	user_email = ''
) => {
	return {
		'{{USER_NAME}}': user_name,
		'{{USER_EMAIL}}': user_email || 'Unknown',
		'{{USER_LOCATION}}': user_location || 'Unknown',
		'{{CURRENT_DATETIME}}': getCurrentDateTime(),
		'{{CURRENT_DATE}}': getFormattedDate(),
		'{{CURRENT_TIME}}': getFormattedTime(),
		'{{CURRENT_WEEKDAY}}': getWeekday(),
		'{{CURRENT_TIMEZONE}}': getUserTimezone(),
		'{{USER_LANGUAGE}}': localStorage.getItem('locale') || 'en-US'
	};
};

/**
 * This function is used to replace placeholders in a template string with the provided prompt.
 * The placeholders can be in the following formats:
 * - `{{prompt}}`: This will be replaced with the entire prompt.
 * - `{{prompt:start:<length>}}`: This will be replaced with the first <length> characters of the prompt.
 * - `{{prompt:end:<length>}}`: This will be replaced with the last <length> characters of the prompt.
 * - `{{prompt:middletruncate:<length>}}`: This will be replaced with the prompt truncated to <length> characters, with '...' in the middle.
 *
 * @param {string} template - The template string containing placeholders.
 * @param {string} prompt - The string to replace the placeholders with.
 * @returns {string} The template string with the placeholders replaced by the prompt.
 */
export const titleGenerationTemplate = (template: string, prompt: string): string => {
	template = template.replace(
		/{{prompt}}|{{prompt:start:(\d+)}}|{{prompt:end:(\d+)}}|{{prompt:middletruncate:(\d+)}}/g,
		(match, startLength, endLength, middleLength) => {
			if (match === '{{prompt}}') {
				return prompt;
			} else if (match.startsWith('{{prompt:start:')) {
				return prompt.substring(0, startLength);
			} else if (match.startsWith('{{prompt:end:')) {
				return prompt.slice(-endLength);
			} else if (match.startsWith('{{prompt:middletruncate:')) {
				if (prompt.length <= middleLength) {
					return prompt;
				}
				const start = prompt.slice(0, Math.ceil(middleLength / 2));
				const end = prompt.slice(-Math.floor(middleLength / 2));
				return `${start}...${end}`;
			}
			return '';
		}
	);

	return template;
};

export const approximateToHumanReadable = (nanoseconds: number) => {
	const seconds = Math.floor((nanoseconds / 1e9) % 60);
	const minutes = Math.floor((nanoseconds / 6e10) % 60);
	const hours = Math.floor((nanoseconds / 3.6e12) % 24);

	const results: string[] = [];

	if (seconds >= 0) {
		results.push(`${seconds}s`);
	}

	if (minutes > 0) {
		results.push(`${minutes}m`);
	}

	if (hours > 0) {
		results.push(`${hours}h`);
	}

	return results.reverse().join(' ');
};

// Month names used as i18n translation keys — must be English regardless of locale
const MONTH_NAMES = [
	'January',
	'February',
	'March',
	'April',
	'May',
	'June',
	'July',
	'August',
	'September',
	'October',
	'November',
	'December'
];

export const getTimeRange = (timestamp: number) => {
	const now = new Date();
	const date = new Date(timestamp * 1000); // Convert Unix timestamp to milliseconds

	// Calculate the difference in milliseconds
	const diffTime = now.getTime() - date.getTime();
	const diffDays = diffTime / (1000 * 3600 * 24);

	const nowDate = now.getDate();
	const nowMonth = now.getMonth();
	const nowYear = now.getFullYear();

	const dateDate = date.getDate();
	const dateMonth = date.getMonth();
	const dateYear = date.getFullYear();

	if (nowYear === dateYear && nowMonth === dateMonth && nowDate === dateDate) {
		return 'Today';
	} else if (dayjs(date).isYesterday()) {
		return 'Yesterday';
	} else if (diffDays <= 7) {
		return 'Previous 7 days';
	} else if (diffDays <= 30) {
		return 'Previous 30 days';
	} else if (nowYear === dateYear) {
		return MONTH_NAMES[dateMonth];
	} else {
		return date.getFullYear().toString();
	}
};

/**
 * Extract frontmatter as a dictionary from the specified content string.
 * @param content {string} - The content string with potential frontmatter.
 * @returns {Object} - The extracted frontmatter as a dictionary.
 */
export const extractFrontmatter = (content: string) => {
	const frontmatter: Record<string, string> = Object.create(null);
	let frontmatterStarted = false;
	let frontmatterEnded = false;
	const frontmatterPattern = /^\s*([a-z_]+):\s*(.*)\s*$/i;

	// Split content into lines
	const lines = content.split('\n');

	// Check if the content starts with triple quotes
	if (lines[0].trim() !== '"""') {
		return {};
	}

	frontmatterStarted = true;

	for (let i = 1; i < lines.length; i++) {
		const line = lines[i];

		if (line.includes('"""')) {
			if (frontmatterStarted) {
				frontmatterEnded = true;
				break;
			}
		}

		if (frontmatterStarted && !frontmatterEnded) {
			const match = frontmatterPattern.exec(line);
			if (match) {
				const [, key, value] = match;
				frontmatter[key.trim()] = value.trim();
			}
		}
	}

	return frontmatter;
};

export { bestMatchingLanguage } from './languageMatching';

// Get the date in the format YYYY-MM-DD
export const getFormattedDate = () => {
	const date = new Date();
	const year = date.getFullYear();
	const month = String(date.getMonth() + 1).padStart(2, '0');
	const day = String(date.getDate()).padStart(2, '0');
	return `${year}-${month}-${day}`;
};

// Get the time in the format HH:MM:SS
export const getFormattedTime = () => {
	const date = new Date();
	return date.toTimeString().split(' ')[0];
};

// Get the current date and time in the format YYYY-MM-DD HH:MM:SS
export const getCurrentDateTime = () => {
	return `${getFormattedDate()} ${getFormattedTime()}`;
};

// Get the user's timezone
export const getUserTimezone = () => {
	return Intl.DateTimeFormat().resolvedOptions().timeZone;
};

// Get the weekday
export const getWeekday = () => {
	const date = new Date();
	const weekdays = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
	return weekdays[date.getDay()];
};

const toTokenCount = (value: unknown) => {
	const parsed = Number(value || 0);
	return Number.isFinite(parsed) ? Math.trunc(parsed) : 0;
};

export const getUsageTokenCount = (input: unknown) => {
	if (!input || typeof input !== 'object' || Array.isArray(input)) return 0;
	const usage = input as Record<string, unknown>;
	if (!usage) {
		return 0;
	}

	let promptTokens = toTokenCount(usage.prompt_tokens || usage.prompt_eval_count || 0);
	if (!promptTokens && (usage.prompt_n != null || usage.cache_n != null)) {
		promptTokens = toTokenCount(usage.prompt_n || 0) + toTokenCount(usage.cache_n || 0);
	}
	if (!promptTokens) {
		promptTokens = toTokenCount(usage.input_tokens || 0);
	}

	const completionTokens = toTokenCount(
		usage.completion_tokens || usage.output_tokens || usage.eval_count || usage.predicted_n || 0
	);

	return promptTokens + completionTokens;
};

export const formatFileSize = (size: unknown) => {
	if (size == null) return 'Unknown size';
	if (typeof size !== 'number' || size < 0) return 'Invalid size';
	if (size === 0) return '0 B';
	const units = ['B', 'KB', 'MB', 'GB', 'TB'];
	let unitIndex = 0;

	while (size >= 1024 && unitIndex < units.length - 1) {
		size /= 1024;
		unitIndex++;
	}
	return `${size.toFixed(1)} ${units[unitIndex]}`;
};

export const getLineCount = (text: string | null | undefined) => {
	console.log(typeof text);
	return text ? text.split('\n').length : 0;
};

export { resolveSchema, convertOpenApiToToolPayload } from './openApiSchema';

export const slugify = (str: string): string => {
	return (
		str
			// 1. Normalize: separate accented letters into base + combining marks
			.normalize('NFD')
			// 2. Remove all combining marks (the accents)
			.replace(/[\u0300-\u036f]/g, '')
			// 3. Replace any sequence of whitespace with a single hyphen
			.replace(/\s+/g, '-')
			// 4. Remove all characters except alphanumeric characters, hyphens, and underscores
			.replace(/[^a-zA-Z0-9-_]/g, '')
			// 5. Convert to lowercase
			.toLowerCase()
	);
};

/**
 * Convert a display name into a safe, underscore-delimited identifier.
 * Strips emojis, accents, and any non-alphanumeric characters so the
 * result is always accepted by backend validation.
 *
 * e.g. "My Tool 😄" → "my_tool"
 */
export const nameToId = (name: string): string => {
	return name
		.normalize('NFD')
		.replace(/[\u0300-\u036f]/g, '')
		.replace(/[^\w]+/g, '_')
		.replace(/^_+|_+$/g, '')
		.toLowerCase();
};

export {
	extractInputVariables,
	splitProperties,
	parseVariableDefinition,
	parseJsonValue
} from './inputVariables';

type ReadableStreamWithAsyncIterator<T> = ReadableStream<T> & {
	[Symbol.asyncIterator]?: () => AsyncIterableIterator<T>;
};

function ensureReadableStreamAsyncIterator() {
	if (typeof ReadableStream === 'undefined') {
		return;
	}

	const prototype = ReadableStream.prototype as ReadableStreamWithAsyncIterator<unknown>;
	if (prototype[Symbol.asyncIterator]) {
		return;
	}

	Object.defineProperty(prototype, Symbol.asyncIterator, {
		value: async function* (this: ReadableStream<unknown>) {
			const reader = this.getReader();
			try {
				while (true) {
					const { done, value } = await reader.read();
					if (done) {
						return;
					}
					yield value;
				}
			} finally {
				reader.releaseLock();
			}
		},
		configurable: true,
		writable: true
	});
}

async function ensurePDFjsLoaded() {
	ensureReadableStreamAsyncIterator();
	if (!window.pdfjsLib) {
		const pdfjs = await import('pdfjs-dist');
		pdfjs.GlobalWorkerOptions.workerSrc = pdfWorkerUrl;
		if (!window.pdfjsLib) {
			throw new Error('pdfjsLib is required for PDF extraction');
		}
	}
	return window.pdfjsLib;
}

export const extractContentFromFile = async (file: File) => {
	// Known text file extensions for extra fallback
	const textExtensions = [
		'.txt',
		'.md',
		'.csv',
		'.json',
		'.js',
		'.ts',
		'.css',
		'.html',
		'.xml',
		'.yaml',
		'.yml',
		'.rtf'
	];

	function getExtension(filename: string) {
		const dot = filename.lastIndexOf('.');
		return dot === -1 ? '' : filename.substr(dot).toLowerCase();
	}

	// Uses pdfjs to extract text from PDF
	async function extractPdfText(file: File) {
		const pdfjsLib = await ensurePDFjsLoaded();
		const arrayBuffer = await file.arrayBuffer();
		const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
		let allText = '';
		for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) {
			const page = await pdf.getPage(pageNum);
			const content = await page.getTextContent();
			const strings = content.items.map((item: any) => item.str);
			allText += strings.join(' ') + '\n';
		}
		return allText;
	}

	// Reads file as text using FileReader
	function readAsText(file: File) {
		return new Promise((resolve, reject) => {
			const reader = new FileReader();
			reader.onload = () => resolve(reader.result);
			reader.onerror = reject;
			reader.readAsText(file);
		});
	}

	async function extractOdsText(file: File) {
		const [arrayBuffer, XLSX] = await Promise.all([file.arrayBuffer(), import('xlsx')]);
		const workbook = XLSX.read(arrayBuffer, { type: 'array' });

		return workbook.SheetNames.map((name) =>
			XLSX.utils.sheet_to_csv(workbook.Sheets[name], { FS: '\t' }).trim()
		)
			.filter(Boolean)
			.join('\n\n');
	}

	async function extractOdfText(file: File) {
		const [arrayBuffer, { default: JSZip }] = await Promise.all([
			file.arrayBuffer(),
			import('jszip')
		]);

		const content = await JSZip.loadAsync(arrayBuffer).then((zip) =>
			zip.file('content.xml')?.async('string')
		);
		if (!content) {
			throw new Error('content.xml not found');
		}

		const doc = new DOMParser().parseFromString(content, 'application/xml');
		if (doc.getElementsByTagName('parsererror').length > 0) {
			throw new Error('content.xml is not well-formed');
		}

		const TEXT_NS = 'urn:oasis:names:tc:opendocument:xmlns:text:1.0';
		const TABLE_NS = 'urn:oasis:names:tc:opendocument:xmlns:table:1.0';
		const textOf = (node: Node): string => {
			if (node.nodeType === Node.TEXT_NODE) {
				return node.textContent ?? '';
			}
			if (node.nodeType !== Node.ELEMENT_NODE) {
				return '';
			}

			const element = node as Element;
			if (element.namespaceURI === TEXT_NS) {
				if (element.localName === 's') {
					const count = Number(
						element.getAttributeNS(TEXT_NS, 'c') ?? element.getAttribute('text:c')
					);
					return ' '.repeat(Number.isFinite(count) && count > 0 ? count : 1);
				}
				if (element.localName === 'tab') {
					return '\t';
				}
				if (element.localName === 'line-break') {
					return '\n';
				}
			}

			return Array.from(element.childNodes).map(textOf).join('');
		};

		const blocks: string[] = [];
		const walk = (node: Element) => {
			if (node.namespaceURI === TABLE_NS && node.localName === 'table-row') {
				const row = Array.from(node.getElementsByTagNameNS(TABLE_NS, 'table-cell'))
					.map((cell) => textOf(cell).trim())
					.join('\t')
					.trimEnd();

				if (row.length > 0) {
					blocks.push(row);
				}
				return;
			}

			if (node.namespaceURI === TEXT_NS && (node.localName === 'p' || node.localName === 'h')) {
				const text = textOf(node).trim();
				if (text.length > 0) {
					blocks.push(text);
				}
				return;
			}

			for (const child of Array.from(node.children)) {
				walk(child);
			}
		};

		walk(doc.documentElement);
		return blocks.join('\n');
	}

	async function extractDocxText(file: File) {
		const [arrayBuffer, { default: mammoth }] = await Promise.all([
			file.arrayBuffer(),
			import('mammoth')
		]);
		const result = await mammoth.extractRawText({ arrayBuffer });
		return result.value; // plain text
	}

	const type = file.type || '';
	const ext = getExtension(file.name);

	// PDF check
	if (type === 'application/pdf' || ext === '.pdf') {
		return await extractPdfText(file);
	}

	// DOCX check
	if (
		type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' ||
		ext === '.docx'
	) {
		return await extractDocxText(file);
	}

	// OpenDocument spreadsheet check
	if (type === 'application/vnd.oasis.opendocument.spreadsheet' || ext === '.ods') {
		return await extractOdsText(file);
	}

	// OpenDocument text/presentation check
	if (
		type === 'application/vnd.oasis.opendocument.text' ||
		type === 'application/vnd.oasis.opendocument.presentation' ||
		['.odt', '.odp'].includes(ext)
	) {
		return await extractOdfText(file);
	}

	// Text check (plain or common text-based)
	if (type.startsWith('text/') || textExtensions.includes(ext)) {
		return await readAsText(file);
	}

	// Fallback: try to read as text, if decodable
	try {
		return await readAsText(file);
	} catch (err) {
		throw new Error('Unsupported or non-text file type: ' + (file.name || type));
	}
};

export const getAge = (birthDate: string | number | Date) => {
	const today = new Date();
	const bDate = new Date(birthDate instanceof Date ? birthDate.getTime() : birthDate);
	let age = today.getFullYear() - bDate.getFullYear();
	const m = today.getMonth() - bDate.getMonth();

	if (m < 0 || (m === 0 && today.getDate() < bDate.getDate())) {
		age--;
	}
	return age.toString();
};

const HEIC_EXTENSION_PATTERN = /\.(heic|heif)$/i;

// Browsers label HEIC photos inconsistently (Firefox uses image/heif, some leave it empty).
export const isHeicImage = (file: File) =>
	['image/heic', 'image/heif'].includes(file.type) || HEIC_EXTENSION_PATTERN.test(file.name);

export const convertHeicToJpeg = async (file: File) => {
	const { default: heic2any } = await import('heic2any');
	try {
		const jpegBlob = (await heic2any({ blob: file, toType: 'image/jpeg' })) as Blob;
		const jpegName = `${file.name.replace(HEIC_EXTENSION_PATTERN, '')}.jpg`;
		return new File([jpegBlob], jpegName, { type: 'image/jpeg' });
	} catch (err: any) {
		if (err?.message?.includes('already browser readable')) {
			return file;
		}
		throw err;
	}
};

export const decodeString = (str: string) => {
	try {
		return decodeURIComponent(str);
	} catch (e) {
		return str;
	}
};

export const initMermaid = async () => {
	const { default: mermaid } = await import('mermaid');
	mermaid.initialize({
		startOnLoad: false, // Should be false when using render API
		theme: document.documentElement.classList.contains('dark') ? 'dark' : 'default',
		securityLevel: 'loose',
		htmlLabels: false,
		secure: ['htmlLabels']
	});
	return mermaid;
};

const cleanupMermaidTempElements = (id: string) => {
	if (typeof document === 'undefined') {
		return;
	}

	document.getElementById(id)?.remove();
	document.getElementById(`d${id}`)?.remove();
	document.getElementById(`i${id}`)?.remove();
};

const isLocalResourceUrl = (url: string): boolean => {
	try {
		const resolved = new URL(url, document.baseURI);
		return resolved.protocol === 'data:' || resolved.origin === location.origin;
	} catch {
		return false;
	}
};

// Escapes and image-set() read as a plain url() to a browser, so match the parsed CSS, not the text.
const CSS_URL_SYNTAX = /url\(|image-set\(|@import|\\/i;

const cssRules = (css: string): string[] => {
	const parsed = new DOMParser().parseFromString(`<style>${css}</style>`, 'text/html');
	return [...(parsed.querySelector('style')?.sheet?.cssRules ?? [])].map((rule) => rule.cssText);
};

const referencesExternalCss = (css: string): boolean => {
	if (!CSS_URL_SYNTAX.test(css)) {
		return false;
	}

	// A value arrives as a stylesheet, a declaration list or a bare presentation value.
	return [css, `a{${css}}`, `a{background-image:${css}}`].some((stylesheet) => {
		const urls = cssRules(stylesheet)
			.join('')
			.matchAll(/url\(["']?([^"')]*)/g);
		return [...urls].some(([, url]) => !isLocalResourceUrl(url));
	});
};

const dropExternalResourceRefs = (node: Node, data: UponSanitizeAttributeHookEvent) => {
	const tagName = node.nodeName.toLowerCase();
	const isImageRef =
		(tagName === 'image' || tagName === 'feimage') &&
		(data.attrName === 'href' || data.attrName === 'xlink:href');

	if (isImageRef && !isLocalResourceUrl(data.attrValue)) {
		data.keepAttr = false;
	}
	if (!isImageRef && referencesExternalCss(data.attrValue)) {
		data.keepAttr = false;
	}
};

// use hrefs point at defs inside the same document (#id) or fetch another file, keep only the former.
const dropExternalUseRefs = (node: Node, data: UponSanitizeAttributeHookEvent) => {
	if (node.nodeName.toLowerCase() !== 'use') {
		return;
	}
	if (data.attrName !== 'href' && data.attrName !== 'xlink:href') {
		return;
	}
	if (!data.attrValue.trim().startsWith('#')) {
		data.keepAttr = false;
	}
};

const dropExternalStyleRules = (node: Node) => {
	if (node.nodeName.toLowerCase() !== 'style') {
		return;
	}

	const css = node.textContent ?? '';
	if (!referencesExternalCss(css)) {
		return;
	}

	node.textContent = cssRules(css)
		.filter((rule) => !referencesExternalCss(rule))
		.join('');
};

// Mermaid runs with securityLevel:'loose', which emits unsanitized SVG (raw javascript: hrefs,
// HTML labels); strip active content before it reaches any innerHTML/{@html} sink.
export const sanitizeSvg = (svg: string): string => {
	DOMPurify.addHook('uponSanitizeAttribute', dropExternalResourceRefs);
	DOMPurify.addHook('uponSanitizeElement', dropExternalStyleRules);
	DOMPurify.addHook('uponSanitizeAttribute', dropExternalUseRefs);
	try {
		return DOMPurify.sanitize(svg, {
			USE_PROFILES: { svg: true, svgFilters: true },
			WHOLE_DOCUMENT: false,
			ADD_TAGS: ['style', 'foreignObject', 'use'],
			ADD_ATTR: [
				'class',
				'style',
				'id',
				'data-*',
				'viewBox',
				'preserveAspectRatio',
				'markerWidth',
				'markerHeight',
				'markerUnits',
				'refX',
				'refY',
				'orient',
				'href',
				'xlink:href',
				'dominant-baseline',
				'text-anchor',
				'clipPathUnits',
				'filterUnits',
				'patternUnits',
				'patternContentUnits',
				'maskUnits',
				'role',
				'aria-label',
				'aria-labelledby',
				'aria-hidden',
				'tabindex'
			],
			SANITIZE_DOM: true
		});
	} finally {
		DOMPurify.removeHook('uponSanitizeAttribute', dropExternalResourceRefs);
		DOMPurify.removeHook('uponSanitizeElement', dropExternalStyleRules);
		DOMPurify.removeHook('uponSanitizeAttribute', dropExternalUseRefs);
	}
};

const configStrings = (value: any): string[] => {
	if (typeof value === 'string') {
		return [value];
	}
	return value && typeof value === 'object' ? Object.values(value).flatMap(configStrings) : [];
};

export const renderMermaidDiagram = async (
	mermaid: typeof import('mermaid').default,
	code: string,
	renderId?: string
) => {
	const id = renderId ?? `mermaid-${uuidv4()}`;
	try {
		// Mermaid renders into a live document, so its own fetches have to be ruled out beforehand.
		const { config } = (await mermaid.parse(code, { suppressErrors: false })) as any;
		const diagram: any = await mermaid.mermaidAPI.getDiagramFromText(code);
		const imageUrls = [
			...[...(diagram.db.getVertices?.() ?? []).values()].map((vertex: any) => vertex.img),
			...[...(diagram.db.getActors?.() ?? []).values()].map((actor: any) => actor.properties?.icon)
		];
		const classStyles = [...(diagram.db.getClasses?.() ?? []).values()].flatMap((classDef: any) => [
			...(classDef.styles ?? []),
			...(classDef.textStyles ?? [])
		]);

		if (
			imageUrls.some((url) => url && !isLocalResourceUrl(url)) ||
			classStyles.some(referencesExternalCss) ||
			configStrings(config).some(referencesExternalCss)
		) {
			throw new Error('External resource loading is disabled for rendered diagrams');
		}

		const { svg } = await mermaid.render(id, code);
		return sanitizeSvg(svg);
	} finally {
		// Mermaid can leave temporary d*/i* wrappers on error paths.
		cleanupMermaidTempElements(id);
	}
};

export const renderVegaVisualization = async (spec: string, lang: string = '', i18n?: any) => {
	const vega = await import('vega');
	const parsedSpec = JSON.parse(spec);
	const hasVegaLiteKeys =
		'mark' in parsedSpec ||
		'encoding' in parsedSpec ||
		'layer' in parsedSpec ||
		'hconcat' in parsedSpec ||
		'vconcat' in parsedSpec ||
		'repeat' in parsedSpec ||
		'facet' in parsedSpec;
	const isVegaLite =
		lang === 'vega-lite' ||
		(parsedSpec.$schema && parsedSpec.$schema.includes('vega-lite')) ||
		hasVegaLiteKeys;
	let vegaSpec = parsedSpec;
	if (isVegaLite) {
		const vegaLite = await import('vega-lite');
		vegaSpec = vegaLite.compile(parsedSpec).spec;
	}
	// Specs come from untrusted chat content: block external loads via data.url (loader.load)
	// and image mark hrefs emitted into the SVG (loader.sanitize).
	const loader = vega.loader();
	loader.load = async () => {
		throw new Error('External resource loading is disabled for rendered visualizations');
	};
	const sanitize = loader.sanitize.bind(loader);
	loader.sanitize = async (uri: string, options: any) => {
		// Resolve with the browser's URL parser so encoding tricks match what it would fetch
		const resolved = new URL(uri, document.baseURI);
		if (resolved.protocol !== 'data:' && resolved.origin !== location.origin) {
			throw new Error('External resource loading is disabled for rendered visualizations');
		}
		return sanitize(uri, options);
	};
	const view = new vega.View(vega.parse(vegaSpec), { loader, renderer: 'none' });
	const svg = await view.toSVG();
	return svg;
};

export const getCodeBlockContents = (content: string) => {
	// Strip thinking/reasoning and other detail blocks before extracting code
	// to prevent code inside <details type="reasoning"> from being treated as artifacts
	content = removeAllDetails(content);

	const codeBlockContents = content.match(/```[\s\S]*?```/g);

	let codeBlocks: { lang: string; code: string }[] = [];

	// Groups of related HTML/CSS/JS blocks. Each HTML block starts a new group;
	// CSS and JS blocks attach to the current (most recent) group.
	// This preserves the existing behaviour for "dumb" models that output
	// separate html/css/js blocks meant to form a single page, while also
	// allowing multiple distinct HTML blocks to produce separate artifacts.
	let htmlGroups: Array<{ html: string; css: string; js: string }> = [];

	const initDefaultGroup = () => {
		if (htmlGroups.length === 0) {
			htmlGroups.push({ html: '', css: '', js: '' });
		}
	};

	if (codeBlockContents) {
		codeBlockContents.forEach((block) => {
			const lang = block.split('\n')[0].replace('```', '').trim().toLowerCase();
			const code = block.replace(/```[\s\S]*?\n/, '').replace(/```$/, '');
			codeBlocks.push({ lang, code });
		});

		codeBlocks.forEach((block) => {
			const { lang, code } = block;

			if (lang === 'html') {
				// Each HTML block starts a new group
				htmlGroups.push({ html: code + '\n', css: '', js: '' });
			} else if (lang === 'css') {
				initDefaultGroup();
				htmlGroups[htmlGroups.length - 1].css += code + '\n';
			} else if (lang === 'javascript' || lang === 'js') {
				initDefaultGroup();
				htmlGroups[htmlGroups.length - 1].js += code + '\n';
			}
		});
	} else {
		// Remove details tags from the content to check if there are any code blocks
		// hidden in the details tags (e.g. reasoning, etc.)
		content = removeAllDetails(content);

		const inlineHtml = content.match(/<html>[\s\S]*?<\/html>/gi);
		const inlineCss = content.match(/<style>[\s\S]*?<\/style>/gi);
		const inlineJs = content.match(/<script>[\s\S]*?<\/script>/gi);

		if (inlineHtml) {
			inlineHtml.forEach((block) => {
				const content = block.replace(/<\/?html>/gi, ''); // Remove <html> tags
				htmlGroups.push({ html: content + '\n', css: '', js: '' });
			});
		}
		if (inlineCss) {
			inlineCss.forEach((block) => {
				const content = block.replace(/<\/?style>/gi, ''); // Remove <style> tags
				initDefaultGroup();
				htmlGroups[htmlGroups.length - 1].css += content + '\n';
			});
		}
		if (inlineJs) {
			inlineJs.forEach((block) => {
				const content = block.replace(/<\/?script>/gi, ''); // Remove <script> tags
				initDefaultGroup();
				htmlGroups[htmlGroups.length - 1].js += content + '\n';
			});
		}
	}

	// Backward-compatible flat fields (merged from all groups)
	const htmlContent = htmlGroups.map((g) => g.html).join('');
	const cssContent = htmlGroups.map((g) => g.css).join('');
	const jsContent = htmlGroups.map((g) => g.js).join('');

	return {
		codeBlocks: codeBlocks,
		html: htmlContent.trim(),
		css: cssContent.trim(),
		js: jsContent.trim(),
		htmlGroups: htmlGroups
			.filter((g) => g.html.trim() || g.css.trim() || g.js.trim())
			.map((g) => ({
				html: g.html.trim(),
				css: g.css.trim(),
				js: g.js.trim()
			}))
	};
};
export const parseFrontmatter = (content: string): Record<string, unknown> => {
	const match = content.match(/^\uFEFF?---[ \t]*\r?\n([\s\S]*?)\r?\n---[ \t]*(?:\r?\n|$)/);
	if (!match) return {};
	try {
		const fields = parseYaml(match[1]);
		return fields && typeof fields === 'object' && !Array.isArray(fields) ? fields : {};
	} catch {
		// Incomplete frontmatter is normal while typing.
		return {};
	}
};

export const formatSkillName = (name: string) => {
	return name.replace(/[-_]/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase());
};

/**
 * Open the file browser panel to display a specific file.
 * Used by both the direct tool execution path (client-side) and the
 * backend event path (server-side) so behaviour is consistent.
 *
 * Stores are passed in by the caller to keep this utility pure.
 */
export const displayFileHandler = (
	path: string,
	stores: { showControls: Writable<boolean>; showFileNavPath: Writable<FileNavOpenRequest | null> },
	options: { page?: unknown } = {}
) => {
	if (path) {
		stores.showControls.set(true);
		const page = normalizeDocumentTargetPage(options.page);
		stores.showFileNavPath.set(page ? { path, page } : path);
	}
};
