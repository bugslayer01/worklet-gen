from core.models.ollama_config import OllamaLLMConfig

# SETTINGS
SWITCHES = {
    "EXTRACT_KEYWORDS_DOMAINS": True,  # Whether to extract keywords and domains from input
    "GENERATE_KEYWORD": True,  # Whether to generate appropriate keywords for reference search(uses worklet title as default otherwise)
    "RANK_REFERENCES": False,  # Whether to rank references based on relevance
    "FALLBACK_TO_GEMINI": True,  # Fallback to Gemini if Ollama fails
    "FALLBACK_TO_OPENAI": False,  # Fallback to OpenAI if BOTH Ollama and Gemini fails
}

PORT = 11434

CPU_MODEL = "qwen3:8b"
MAX_TOKENS = 4000

# Ollama LLM configurations
KEYWORD_DOMAIN_EXTRACTION_LLM = OllamaLLMConfig(model=CPU_MODEL, port=PORT)
WORKLET_GENERATOR_LLM = OllamaLLMConfig(model=CPU_MODEL, port=PORT)
REFERENCE_KEYWORD_LLM = OllamaLLMConfig(model=CPU_MODEL, port=PORT)
REFERENCE_RANKING_LLM = OllamaLLMConfig(model=CPU_MODEL, port=PORT)

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
RANK_REFERENCES = "rank_references"
GENERATE_FILES = "generate_files"
ROUTER = "router"
ANSWER = "answer"
FAILURE = "failure"
