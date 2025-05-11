from typing import List, Optional
import ipaddress
import socket
from config import SOCKET_TIMEOUT


def is_ip_address(host: str) -> bool:
    """
    Проверяет соответствует ли заданный параметр формату IP адреса

    :param host: IP адрес в формате 'x.x.x.x/y'
    :type host: str

    :returns: Параметр соответствует формату IP адреса
    :rtype: bool
    """
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError as err:
        print(err)
        return False


def is_ip_subnet(subnet: str) -> bool:
    """
    Проверяет соответствует ли заданный параметр формату подсети

    :param subnet: Подсеть в формате 'x.x.x.x/y'
    :type subnet: str

    :returns: Параметр соответствует формату подсети
    :rtype: bool
    """
    try:
        ipaddress.ip_network(subnet)
        return True
    except ValueError as err:
        print(err)
        return False


def get_hosts_from_subnet(subnet: str) -> List[str]:
    """
    Возвращает список хостовых IP адресов из заданной подсети

    :param subnet: Подсеть в формате 'x.x.x.x/y'
    :type subnet: str

    :returns: Список хостовых IP адресов
    :rtype: List[str]
    """
    if is_ip_subnet(subnet):
        try:
            return [str(host) for host in ipaddress.ip_network(subnet).hosts()]
        except Exception as err:
            print(err)
    # Подсеть должна быть задана и в правильно формате.
    # Иначе необходимо вернуть пустой список.
    return []


def tcp_port_is_open(
    host: str,
    port: int,
    timeout: Optional[float|int] = SOCKET_TIMEOUT
) -> bool:
    """
    Проверяем открыт ли порт по указанному протоколу
    на заданном IP адресе

    :param host: IP адрес, подлежащий проверке
    :type host: str
    
    :param port: Порт, подлежащий проверке, в диапозоне 1-65535
    :type port: int
    
    :param timeout: Таймаут сокета в секундах (можно указать дробное значение)
    :type timeout: Optional[float|int]

    :returns: Открыт ли порт по указанному протоколу на заданном IP адресе
    :rtype: bool
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        try:
            return sock.connect_ex((host, port)) == 0
        except Exception as err:
            print(err)
            return False
        finally:
            sock.close()


def telnet_is_enabled(host: str) -> bool:
    """
    Проверяем открыт ли 23 порт по протоколу tcp
    на заданном IP адресе

    :param host: IP адрес, подлежащий проверке
    :type host: str

    :returns: Открыт ли telnet на заданном устройстве
    :rtype: bool
    """
    return tcp_port_is_open(host, 23)


def ssh_is_enabled(host: str) -> bool:
    """
    Проверяем открыт ли 22 порт по протоколу tcp
    на заданном IP адресе

    :param host: IP адрес, подлежащий проверке
    :type host: str

    :returns: Открыт ли ssh на заданном устройстве
    :rtype: bool
    """
    return tcp_port_is_open(host, 22)
