import { fileURLToPath } from 'node:url';
import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';
import { sveltekit } from '@sveltejs/kit/vite';
import { defaultClientConditions, defineConfig } from 'vite';
import { resolveBuildInfo } from './scripts/build-info.js';

const backendTarget = process.env.WEBUI_BACKEND_URL || 'http://localhost:8080';
const buildInfo = resolveBuildInfo();

export default defineConfig({
	resolve: {
		alias: { $lib: fileURLToPath(new URL('./src/lib', import.meta.url)) },
		conditions: ['onnxruntime-web-use-extern-wasm', ...defaultClientConditions]
	},
	plugins: [
		sveltekit({
			preprocess: vitePreprocess(),
			adapter: adapter({ pages: 'build', assets: 'build', fallback: 'index.html' }),
			version: {
				name: buildInfo.hash || process.env.npm_package_version || '0.12.3',
				pollInterval: 60000
			}
		})
	],
	define: {
		APP_VERSION: JSON.stringify(process.env.npm_package_version),
		APP_BUILD_HASH: JSON.stringify(buildInfo.hash),
		APP_BUILD_CHANNEL: JSON.stringify(buildInfo.channel)
	},
	build: {
		sourcemap: true,
		rolldownOptions: {
			treeshake: {
				manualPureFunctions: process.env.ENV === 'dev' ? [] : ['console.log', 'console.debug']
			}
		}
	},
	server: {
		proxy: {
			'/api': {
				target: backendTarget,
				changeOrigin: true,
				ws: true
			},
			'/ollama': {
				target: backendTarget,
				changeOrigin: true
			},
			'/openai': {
				target: backendTarget,
				changeOrigin: true
			},
			'/oauth': {
				target: backendTarget,
				changeOrigin: true
			},
			'/ws': {
				target: backendTarget,
				changeOrigin: true,
				ws: true
			}
		}
	},
	worker: {
		format: 'es'
	}
});
