from typing import List, Optional
import ipaddress
import socket
from config import SOCKET_TIMEOUT


def is_ip_address(ip: str) -> bool:
    """
    Функция проверяет соответствие заданной строки формату ip адреса
    """
    try:
        ipaddress.ip_address(ip)
        return True
    except:
        return False


def is_ip_subnet(subnet: str) -> bool:
    """
    Функция проверяет соответствие заданной строки формату ip подсети
    """
    try:
        ipaddress.ip_network(subnet)
        return True
    except:
        return False


def get_hosts_from_subnet(subnet: str) -> List[str]:
    """
    Функция возвращает список хостовых адресов заданной подсети
    """
    try:
        return [str(host) for host in ipaddress.ip_network(subnet).hosts()]
    except:
        pass
    # Подсеть должна быть задана и в правильно формате.
    # Иначе необходимо вернуть пустой список.
    return []


def tcp_port_is_open(
    ip: str,
    port: int,
    timeout: Optional[float|int] = SOCKET_TIMEOUT
) -> bool:
    """
    Функция проверяет открытость порта на узле по заданному протоколу
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        try:
            return sock.connect_ex((ip, port)) == 0
        except:
            return False
        finally:
            sock.close()


def telnet_is_enabled(ip: str) -> bool:
    """
    Функция проверяет доступность узла по протоколу telnet
    """
    return tcp_port_is_open(ip, 23)


def ssh_is_enabled(ip: str) -> bool:
    """
    Функция проверяет доступность узла по протоколу ssh
    """
    return tcp_port_is_open(ip, 22)
