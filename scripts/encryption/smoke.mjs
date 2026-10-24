import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import init, { Session } from '../../src/lib/encryption/vendor/encryption.js';

await init({
	module_or_path: readFileSync(
		new URL('../../src/lib/encryption/vendor/encryption_bg.wasm', import.meta.url)
	)
});
const identity = (user, participation, session = 'verification-session') => ({
	channel: 'verification-channel',
	session,
	user,
	participation
});
const aliceId = identity('alice', 'p0');
const bobId = identity('bob', 'p1');
const alice = new Session(JSON.stringify(aliceId), 'p0');
const bob = new Session(JSON.stringify(bobId), 'p0');
const outsider = new Session(JSON.stringify(identity('outsider', 'p2', 'another-session')), 'p0');
try {
	alice.create();
	const roster = JSON.stringify([
		{ identity: aliceId, key: alice.public_key() },
		{ identity: bobId, key: bob.public_key() }
	]);
	assert.throws(() => alice.add(outsider.key_package(), 'p2', roster));
	const invitation = JSON.parse(alice.add(bob.key_package(), 'p1', roster));
	bob.join(invitation.welcome, roster);
	const packet = alice.encrypt('ANSWERAI encrypted round trip');
	assert.equal(JSON.parse(bob.process(packet, 'p0', roster)).text, 'ANSWERAI encrypted round trip');
	assert.throws(() => bob.process(packet, 'p0', roster));
	assert.throws(() => bob.remove('p0', roster));
	console.log(
		'PASS: verified WASM artifact, cross-client encryption, replay rejection, session binding, and host-only removal.'
	);
} finally {
	alice.free();
	bob.free();
	outsider.free();
}
