from typing import List, Optional
import aioping
from config import PING_TIMEOUT, PING_RETRIES


async def ping_host(
    host: str,
    timeout: Optional[int|float] = PING_TIMEOUT,
    count: Optional[int] = PING_RETRIES
) -> tuple[str, bool]:
    """
    Проверяет доступность устройства по icmp ping

    :param host: IP адрес устройства
    :type host: str
    
    :param timeout: Таймаут пинга
    :type timeout: Optional[int|float]
    
    :param count: Количество попыток пинга
    :type count: Optional[int]

    :returns: Кортедж с адресом и статусом его доступности
    :rtype: tuple[str, bool]
    """
    for _ in range(count):
        try:
            await aioping.ping(host, timeout=timeout)
            return (host, True)
        except:
            pass
    return (host, False)


async def get_accesable_hosts(hosts: List[str]) -> List[str]:
    """
    Возвращает список устройств, доступных по icmp ping

    :param hosts: Список IP адресов устройств, подлежащих проверке
    :type hosts: List[str]

    :returns: Список IP адресов, доступных по icmp ping
    :rtype: List[str]
    """
    accesable_hosts = []
    for host in hosts:
        result = await ping_host(host)
        if result[1]:
            accesable_hosts.append(result[0])
    # Список IP адресов не должен быть пустым.
    # Иначе возвращаем также пустой список.
    return accesable_hosts
