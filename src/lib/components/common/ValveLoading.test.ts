// @vitest-environment happy-dom
import { expect, it, vi } from 'vitest';
import { mount, unmount, tick } from 'svelte';
import { writable } from 'svelte/store';
import ValveModalHarness from './test-fixtures/ValveModalHarness.svelte';
import { getToolValvesById, getToolValvesSpecById } from '$lib/apis/tools';
import type { ValveValues } from '$lib/types/valves';

vi.mock('$lib/apis/tools', () => ({
	getToolValvesById: vi.fn(),
	getToolValvesSpecById: vi.fn(),
	updateToolValvesById: vi.fn(),
	getUserValvesSpecById: vi.fn(),
	getUserValvesById: vi.fn(),
	updateUserValvesById: vi.fn(),
	getTools: vi.fn()
}));

it('ignores an old resource response after the admin switches resources', async () => {
	let resolveOld!: (values: ValveValues) => void;
	const oldResponse = new Promise<ValveValues>((resolve) => {
		resolveOld = resolve;
	});
	vi.mocked(getToolValvesById).mockImplementation(async (_token, id) =>
		id === 'old' ? oldResponse : { attempts: 2 }
	);
	vi.mocked(getToolValvesSpecById).mockImplementation(async (_token, id) => ({
		properties: {
			attempts: { type: 'integer', title: id === 'old' ? 'Old resource' : 'New resource' }
		}
	}));
	const target = document.createElement('div');
	document.body.appendChild(target);
	const resource = writable('old');
	const component = mount(ValveModalHarness, {
		target,
		props: { resource },
		context: new Map([['i18n', writable({ t: (key: string) => key, language: 'en-US' })]])
	});
	try {
		await tick();
		resource.set('new');
		await tick();
		await vi.waitFor(() => expect(document.body.textContent).toContain('New resource'));
		resolveOld({ attempts: 1 });
		await oldResponse;
		await tick();
		expect(document.body.textContent).toContain('New resource');
		expect(document.body.textContent).not.toContain('Old resource');
	} finally {
		await unmount(component);
		target.remove();
		vi.resetAllMocks();
	}
});
