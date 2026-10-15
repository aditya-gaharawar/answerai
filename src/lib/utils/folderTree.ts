import type { FolderRecord } from '$lib/types/folders';

export function buildFolderTree(
	owned: FolderRecord[],
	shared: FolderRecord[],
	newId: string | null = null
): Record<string, FolderRecord> {
	const folders: Record<string, FolderRecord> = Object.create(null);
	for (const folder of owned)
		folders[folder.id] = {
			...folder,
			childrenIds: [],
			...(folder.id === newId ? { new: true } : {})
		};
	for (const folder of shared) {
		if (Object.hasOwn(folders, folder.id)) folders[folder.id].showOwnerInfo = true;
		else folders[folder.id] = { ...folder, childrenIds: [], shared: true };
	}
	const visited = new Set<string>();
	for (const start of Object.keys(folders)) {
		let current: string | null = start;
		const path = new Set<string>();
		while (current !== null && !visited.has(current)) {
			const folder: FolderRecord = folders[current];
			if (!folder) break;
			path.add(current);
			const parent: string | null = folder.parent_id;
			if (parent !== null && (!Object.hasOwn(folders, parent) || path.has(parent))) {
				folder.parent_id = null;
				break;
			}
			current = parent;
		}
		for (const id of path) visited.add(id);
	}
	for (const folder of Object.values(folders)) {
		if (folder.parent_id !== null) folders[folder.parent_id].childrenIds?.push(folder.id);
	}
	for (const folder of Object.values(folders))
		folder.childrenIds?.sort((a, b) => folders[b].updated_at - folders[a].updated_at);
	return folders;
}
