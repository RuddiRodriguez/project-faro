"""Overlapping passages retain their exact positions in each source page."""


def split_text(text, chunk_size=1000, overlap=150):
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            boundary = text.rfind("\n", start + chunk_size // 2, end)
            if boundary >= 0:
                end = boundary
        chunk = text[start:end]
        left = start + len(chunk) - len(chunk.lstrip())
        right = end - len(chunk) + len(chunk.rstrip())
        if left < right:
            yield left, right, text[left:right]
        if end == len(text):
            break
        start = max(end - overlap, start + 1)
