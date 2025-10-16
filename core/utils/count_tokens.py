import tiktoken


def count_tokens(text: str) -> int:
    """
    Approximate Qwen 3 (4B) token count using cl100k_base encoding.
    """
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))
