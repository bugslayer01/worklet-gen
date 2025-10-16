from core.models.gpu_config import GPULLMConfig

# SETTINGS
SWITCHES = {
    "FALLBACK_TO_GEMINI": True,  # Fallback to Gemini if Ollama fails
    "FALLBACK_TO_OPENAI": False,  # Fallback to OpenAI if BOTH Ollama and Gemini fails
}

PORT1 = 11434
PORT2 = 11435

GPT_OSS_20B = "gpt-oss:20b-50k-8k"

# GPU LLM configurations
KEYWORD_DOMAIN_EXTRACTION_LLM = GPULLMConfig(model=GPT_OSS_20B, port=PORT2)
WORKLET_GENERATOR_LLM = GPULLMConfig(model=GPT_OSS_20B, port=PORT2)
REFERENCE_KEYWORD_LLM = GPULLMConfig(model=GPT_OSS_20B, port=PORT2)
REFERENCE_SORT_LLM = GPULLMConfig(model=GPT_OSS_20B, port=PORT2)

# Fallback LLM models
# Used if SWITCHES["FALLBACK_TO_GEMINI"] = True
FALLBACK_GEMINI_MODEL = "gemini-2.0-flash"

# Used if SWITCHES["FALLBACK_TO_OPENAI"] = True
FALLBACK_OPENAI_MODEL = "gpt-4o-mini"

# Graph constants used in agent
PROCESS_INPUT = "process_input"
EXTRACT_KEYWORDS_DOMAINS = "extract_keywords_domains"
GENERATE_WORKLETS = "generate_worklets"
WEB_SEARCH = "web_search"
REFERENCES = "references"
SORT_REFERENCES = "sort_references"
GENERATE_FILES = "generate_files"
ROUTER = "router"
ANSWER = "answer"
FAILURE = "failure"
