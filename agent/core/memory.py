from collections import defaultdict


class MemoryStore:
    def __init__(self) -> None:
        self._messages: dict[str, list[str]] = defaultdict(list)

    def append(self, lead_key: str, message: str) -> None:
        self._messages[lead_key].append(message)

    def history(self, lead_key: str) -> list[str]:
        return list(self._messages.get(lead_key, []))
