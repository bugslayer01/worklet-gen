import tiktoken
from core.constants import CPU_MODEL

map = {
    "qwen3:4b": "cl100k_base",
    "qwen3:8b": "cl100k_base",
}


def count_tokens(text: str) -> int:
    encoding = tiktoken.get_encoding(map.get(CPU_MODEL, "cl100k_base"))
    return len(encoding.encode(text))
