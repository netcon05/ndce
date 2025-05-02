from typing import List, Tuple, Optional
import asyncio
import aioping
from ndce.net import is_ip_address


PING_TIMEOUT = 1


async def ping_host(
    host: str,
    timeout: Optional[float] = PING_TIMEOUT
) -> Tuple[str, bool]:
    """
    Checks the host for accesability via icmp ping

    :param host: Hosts ip address
    :type host: str
    
    :param timeout: Icmp ping timeout
    :type timeout: Optional[float]

    :returns: Tuple with host address and bool value (accesable or not)
    :rtype: Tuple[str, bool]
    """
    if is_ip_address(host):
        try:
            delay = await aioping.ping(host, timeout=timeout)
            return (host, delay > 0)
        except TimeoutError as err:
            print(f'Host {host} is not accesable via icmp ping.', err)
    return (host, False)


async def host_is_accesable(host: str) -> bool:
    """
    Tells wether the host is accesable

    :param host: Hosts ip address
    :type host: str

    :returns: True if the host is accesable or False otherwise
    :rtype: bool
    """
    result = await ping_host(host)
    return bool(result[1])


async def get_accesable_hosts(hosts: List[str]) -> List[str]:
    """
    Returns list of hosts accesable via icmp ping

    :param hosts: List of hosts to check for accesability
    :type hosts: List[str]

    :returns: List of accesable hosts
    :rtype: List[str]
    """
    if len(hosts):
        try:
            tasks = [asyncio.create_task(ping_host(host)) for host in hosts]
            results = await asyncio.gather(*tasks)
            return [result[0] for result in results if bool(result[1])]
        except Exception as err:
            print('Could not get list of accesable hosts.', err)
    # List of hosts must contain at least one element.
    # Otherwise empty list must be returned.
    return []
