<script lang="ts">
	import Valves from '../Valves.svelte';
	import type { ValveValues } from '$lib/types/valves';
	let valves: ValveValues = { attempts: 1 };
</script>

<Valves bind:valves valvesSpec={{ properties: { attempts: { type: 'integer', enum: [1, 2] } } }} />
<output>{JSON.stringify(valves)}</output>
