const activities: Record<string, string> = {
	search_web: 'Searching the web',
	research_web: 'Researching sources',
	fetch_url: 'Reading a webpage',
	query_chat_files: 'Searching your files',
	grep_chat_files: 'Searching your files',
	list_chat_files: 'Checking attached files',
	view_file: 'Reading a file',
	generate_image: 'Generating an image',
	edit_image: 'Editing an image',
	execute_code: 'Running code',
	search_tools: 'Finding the right tool',
	delegate_task: 'Working with a specialist',
	search_memories: 'Searching memory',
	query_knowledge_files: 'Searching knowledge'
};
export function toolActivity(name: string): string {
	return activities[name] ?? `Running ${name.replaceAll('_', ' ')}`;
}
