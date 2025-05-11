from typing import List, Tuple, Optional
import asyncio
import aioping
from ndce.net import is_ip_address
from config import PING_TIMEOUT


async def ping_host(
    host: str,
    timeout: Optional[int|float] = PING_TIMEOUT
) -> Tuple[str, bool]:
    """
    Проверяет доступность устройства по icmp ping

    :param host: IP адрес устройства
    :type host: str
    
    :param timeout: Таймаут пинга
    :type timeout: Optional[int|float]

    :returns: Кортедж с адресом и статусом его доступности
    :rtype: Tuple[str, bool]
    """
    if is_ip_address(host):
        try:
            delay = await aioping.ping(host, timeout=timeout)
            return (host, delay > 0)
        except TimeoutError as err:
            print(err)
    return (host, False)


async def get_accesable_hosts(hosts: List[str]) -> List[str]:
    """
    Возвращает список устройств, доступных по icmp ping

    :param hosts: Список IP адресов устройств, подлежащих проверке
    :type hosts: List[str]

    :returns: Список IP адресов, доступных по icmp ping
    :rtype: List[str]
    """
    if len(hosts):
        try:
            tasks = [asyncio.create_task(ping_host(host)) for host in hosts]
            results = await asyncio.gather(*tasks)
            return [result[0] for result in results if result[1]]
        except Exception as err:
            print(err)
    # Список IP адресов не должен быть пустым.
    # Иначе возвращаем также пустой список.
    return []
