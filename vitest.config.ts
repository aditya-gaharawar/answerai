import { defineConfig, mergeConfig } from 'vitest/config';
import viteConfig from './vite.config';

// Historical workspace checkouts are evidence, not part of the current test suite.
export default mergeConfig(
	viteConfig,
	defineConfig({ test: { include: ['src/**/*.{test,spec}.{ts,js}'] } })
);
