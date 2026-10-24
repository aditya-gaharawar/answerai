<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import type { Map, FeatureGroup, LatLngTuple, LeafletMouseEvent } from 'leaflet';
	type MapPoint = { coords: LatLngTuple; content: string };
	let destroyed = false;

	let map: Map | null = null;
	let mapElement: HTMLDivElement;

	export let setViewLocation: LatLngTuple | null = [51.505, -0.09];
	export let points: MapPoint[] = [];

	export let onClick: (coordinates: string) => void = () => {};

	let markerGroupLayer: FeatureGroup | null = null;

	onMount(async () => {
		const [{ default: L }] = await Promise.all([
			import('leaflet'),
			import('leaflet/dist/leaflet.css')
		]);

		if (destroyed) return;
		map = L.map(mapElement).setView(setViewLocation ? setViewLocation : [51.505, -0.09], 10);

		if (setViewLocation) {
			points = [
				{
					coords: setViewLocation,
					content: `Lat: ${setViewLocation[0]}, Lng: ${setViewLocation[1]}`
				}
			];
		}

		L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
			attribution:
				'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
		}).addTo(map);

		const setMarkers = (points: MapPoint[]) => {
			if (map) {
				if (markerGroupLayer) {
					map.removeLayer(markerGroupLayer);
				}

				let markers = [];
				for (let point of points) {
					const popup = document.createElement('span');
					popup.textContent = point.content;
					const marker = L.marker(point.coords).bindPopup(popup);

					markers.push(marker);
				}

				markerGroupLayer = L.featureGroup(markers).addTo(map);

				try {
					map.fitBounds(markerGroupLayer.getBounds(), {
						maxZoom: Math.max(map.getZoom(), 13)
					});
				} catch (error) {}
			}
		};

		setMarkers(points);

		map.on('click', (e: LeafletMouseEvent) => {
			console.log(e.latlng);
			onClick(`${e.latlng.lat}, ${e.latlng.lng}`);

			setMarkers([
				{
					coords: [e.latlng.lat, e.latlng.lng],
					content: `Lat: ${e.latlng.lat}, Lng: ${e.latlng.lng}`
				}
			]);
		});
	});

	onDestroy(() => {
		destroyed = true;
		if (map) {
			console.log('Unloading Leaflet map.');
			map.remove();
			map = null;
		}
	});
</script>

<div class=" z-10 w-full">
	<div bind:this={mapElement} class="h-96 z-10"></div>
</div>
