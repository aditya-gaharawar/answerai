// @vitest-environment happy-dom
import { expect, it } from 'vitest';
import { mount, unmount, tick } from 'svelte';
import { writable } from 'svelte/store';
import ValveHarness from './test-fixtures/ValveHarness.svelte';
import Textarea from './Textarea.svelte';

it('preserves numeric enum values when a user changes a setting', async () => {
	const target = document.createElement('div');
	document.body.appendChild(target);
	const component = mount(ValveHarness, {
		target,
		context: new Map([['i18n', writable({ t: (key: string) => key, language: 'en-US' })]])
	});
	try {
		await tick();
		const select = target.querySelector('select');
		expect(select).not.toBeNull();
		select!.options[0].selected = false;
		select!.options[1].selected = true;
		select!.dispatchEvent(new Event('change', { bubbles: true }));
		await tick();
		expect(JSON.parse(target.querySelector('output')!.textContent ?? '{}').attempts).toBe(2);
	} finally {
		await unmount(component);
		target.remove();
	}
});

it('forwards keyboard shortcuts from the shared textarea', async () => {
	const target = document.createElement('div');
	document.body.appendChild(target);
	let received: KeyboardEvent | undefined;
	const component = mount(Textarea, {
		target,
		props: {
			onKeydown: (event) => {
				received = event;
				event.preventDefault();
			}
		}
	});
	try {
		await tick();
		const event = new KeyboardEvent('keydown', { key: 'Enter', cancelable: true });
		target.querySelector('textarea')!.dispatchEvent(event);
		expect(received).toBe(event);
		expect(event.defaultPrevented).toBe(true);
	} finally {
		await unmount(component);
		target.remove();
	}
});
