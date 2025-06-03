from typing import Optional, Tuple
import asyncio
import aioping
import config


async def ping_host(
    host: str,
    timeout: Optional[int|float] = config.PING_TIMEOUT,
    count: Optional[int] = config.PING_RETRIES
) -> Tuple[str, bool]:
    """
    Функция проверяет доступность заданного узла по протоколу icmp
    """
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
