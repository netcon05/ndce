from typing import Optional, Tuple
import asyncio
import aioping
from config import PING_TIMEOUT, PING_RETRIES


async def ping_host(
    host: str,
    timeout: Optional[int|float] = PING_TIMEOUT,
    count: Optional[int] = PING_RETRIES
) -> Tuple[str, bool]:
    for i in range(count):
        try:
            await aioping.ping(host, timeout=timeout)
            return host, True
        except Exception as err:
            print(host, err)
            if i == count - 1:
                return host, False
            else:
                await asyncio.sleep(0.1)
