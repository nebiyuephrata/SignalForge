from collections import defaultdict

from fastapi import HTTPException, Request


_REQUEST_COUNT: dict[str, int] = defaultdict(int)


async def simple_rate_limit(request: Request) -> None:
    client = request.client.host if request.client else "unknown"
    _REQUEST_COUNT[client] += 1
    if _REQUEST_COUNT[client] > 100:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
