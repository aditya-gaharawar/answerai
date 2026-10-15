// Request/response contracts from the backend ImagesConfig and ModelsConfigForm schemas.

export interface WorkflowNode {
	type: string;
	key: string;
	node_ids: string[] | number[] | string;
}

export interface ImagesConfig {
	ENABLE_IMAGE_GENERATION: boolean;
	ENABLE_IMAGE_PROMPT_GENERATION: boolean;
	IMAGE_GENERATION_ENGINE: string;
	IMAGE_GENERATION_MODEL: string;
	IMAGE_SIZE: string | null;
	IMAGE_STEPS: number | null;
	IMAGES_OPENAI_API_BASE_URL: string;
	IMAGES_OPENAI_API_KEY: string;
	IMAGES_OPENAI_API_VERSION: string;
	IMAGES_OPENAI_API_PARAMS: Record<string, unknown> | string | null;
	AUTOMATIC1111_BASE_URL: string;
	AUTOMATIC1111_API_AUTH: Record<string, unknown> | string | null;
	AUTOMATIC1111_PARAMS: Record<string, unknown> | string | null;
	COMFYUI_BASE_URL: string;
	COMFYUI_API_KEY: string;
	COMFYUI_WORKFLOW: string;
	COMFYUI_WORKFLOW_NODES: WorkflowNode[];
	IMAGES_GEMINI_API_BASE_URL: string;
	IMAGES_GEMINI_API_KEY: string;
	IMAGES_GEMINI_ENDPOINT_METHOD: string;
	ENABLE_IMAGE_EDIT: boolean;
	IMAGE_EDIT_ENGINE: string;
	IMAGE_EDIT_MODEL: string;
	IMAGE_EDIT_SIZE: string | null;
	IMAGES_EDIT_OPENAI_API_BASE_URL: string;
	IMAGES_EDIT_OPENAI_API_KEY: string;
	IMAGES_EDIT_OPENAI_API_VERSION: string;
	IMAGES_EDIT_GEMINI_API_BASE_URL: string;
	IMAGES_EDIT_GEMINI_API_KEY: string;
	IMAGES_EDIT_COMFYUI_BASE_URL: string;
	IMAGES_EDIT_COMFYUI_API_KEY: string;
	IMAGES_EDIT_COMFYUI_WORKFLOW: string;
	IMAGES_EDIT_COMFYUI_WORKFLOW_NODES: WorkflowNode[];
}

export interface ModelsConfig {
	DEFAULT_MODELS: string | null;
	DEFAULT_PINNED_MODELS: string | null;
	MODEL_ORDER_LIST: string[] | null;
	DEFAULT_MODEL_METADATA: Record<string, unknown> | null;
	DEFAULT_MODEL_PARAMS: Record<string, unknown> | null;
}
