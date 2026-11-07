def split_text(text: str, max_chars: int) -> list[str]:
    """Split text into chunks without cutting paragraphs or sentences when possible."""
    if max_chars < 1:
        raise ValueError("max_chars must be greater than zero")

    remaining = text.strip()
    if not remaining:
        return []

    chunks: list[str] = []
    while len(remaining) > max_chars:
        window = remaining[:max_chars]
        cut = max_chars

        for separator in ("\n\n", "\n", ". "):
            index = window.rfind(separator)
            if index > 0:
                cut = index + len(separator)
                break

        chunks.append(remaining[:cut].strip())
        remaining = remaining[cut:].strip()

    if remaining:
        chunks.append(remaining)

    return chunks
