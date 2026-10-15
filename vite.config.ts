import { sveltekit } from '@sveltejs/kit/vite';
import { defaultClientConditions, defineConfig } from 'vite';
import { resolveBuildInfo } from './scripts/build-info.js';

const backendTarget = process.env.WEBUI_BACKEND_URL || 'http://localhost:8080';
const buildInfo = resolveBuildInfo();

export default defineConfig({
	resolve: {
		conditions: ['onnxruntime-web-use-extern-wasm', ...defaultClientConditions]
	},
	plugins: [sveltekit()],
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
