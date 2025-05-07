from typing import List, Optional
import ipaddress
import socket


IP_PROTO_TYPES = ('tcp', 'udp')

SOCKET_TIMEOUT = 1


def is_ip_address(host: str) -> bool:
    """
    Checks if passed parameter is in valid ip address format 

    :param host: Ip address in 'x.x.x.x/y' format
    :type host: str

    :returns: Parameters format is valid or not
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
    Checks if passed parameter is in valid ip subnet format 

    :param subnet: Subnet in 'x.x.x.x/y' format
    :type subnet: str

    :returns: Parameters format is valid or not
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
    Returns list of host addresses of the subnet

    :param subnet: Subnet in 'x.x.x.x/y' format
    :type subnet: str

    :returns: List of host addresses
    :rtype: List[str]
    """
    if is_ip_subnet(subnet):
        try:
            return [str(host) for host in ipaddress.ip_network(subnet).hosts()]
        except Exception as err:
            print(err)
    # Subnet parameter has to be passed and in a valid format.
    # Otherwise empty list must be returned.
    return []


def tcp_port_is_open(
    host: str,
    port: int,
    timeout: Optional[float|int] = SOCKET_TIMEOUT
) -> bool:
    """
    Checks if the port is open on ip address for defined protocol

    :param host: Checked ip address
    :type host: str
    
    :param port: Checked port number from 1 to 65535
    :type port: int
    
    :param timeout: Socket timeout in seconds (float is valid)
    :type timeout: Optional[float|int]

    :returns: Port is open (True) or not (False)
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
    Checks if the port tcp/23 (TELNET) is open on the ip address

    :param host: Checked ip address
    :type host: str

    :returns: Port is open (True) or not (False)
    :rtype: bool
    """
    return tcp_port_is_open(host, 23)


def ssh_is_enabled(host: str) -> bool:
    """
    Checks if the port tcp/22 (SSH) is open on the ip address

    :param host: Checked ip address
    :type host: str

    :returns: Port is open (True) or not (False)
    :rtype: bool
    """
    return tcp_port_is_open(host, 22)
