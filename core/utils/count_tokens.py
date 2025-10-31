import tiktoken
from core.constants import GPU_MODEL

map = {
    "qwen3:14b": "cl100k_base",
    "qwen3:8b": "cl100k_base",
    "qwen3:4b": "cl100k_base",
    "gpt-oss:20b": "o200k_harmony",
    "gpt-oss:20b-50k-8k": "o200k_harmony",
}


def count_tokens(text: str) -> int:
    encoding = tiktoken.get_encoding(map.get(GPU_MODEL, "o200k_harmony"))
    return len(encoding.encode(text))
