STOP_WORDS = {"stop", "unsubscribe", "end", "quit"}


def should_suppress(text: str) -> bool:
    normalized = text.strip().lower()
    return normalized in STOP_WORDS
