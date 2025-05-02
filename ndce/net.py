from typing import List, Optional
import ipaddress
import socket
from contextlib import closing


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
    if host.strip():
        try:
            ipaddress.ip_address(host)
            return True
        except ValueError as err:
            print(err)
    else:
        print('No ip address passed.')
    return False


def is_ip_subnet(subnet: str) -> bool:
    """
    Checks if passed parameter is in valid ip subnet format 

    :param subnet: Subnet in 'x.x.x.x/y' format
    :type subnet: str

    :returns: Parameters format is valid or not
    :rtype: bool
    """
    if subnet.strip():
        try:
            ipaddress.ip_network(subnet)
            return True
        except ValueError as err:
            print(err)
    else:
        print('No subnet passed.')
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
            print(f'Could not get list of hosts from {subnet} subnet.', err)
    # Subnet parameter has to be passed and in a valid format.
    # Otherwise empty list must be returned.
    return []


def port_is_open(
    host: str,
    protocol: str,
    port: int,
    timeout: Optional[float] = SOCKET_TIMEOUT
) -> bool:
    """
    Checks if the port is open on ip address for defined protocol

    :param host: Checked ip address
    :type host: str
    
    :param protocol: Checked protocol either TCP or UDP
    :type protocol: str
    
    :param port: Checked port number from 1 to 65535
    :type port: int
    
    :param timeout: Socket timeout in seconds (float is valid)
    :type timeout: Optional[float]

    :returns: Port is open (True) or not (False)
    :rtype: bool
    """
    if not is_ip_address(host):
        print(f'{host} is not a valid ip address.')
    elif not protocol in IP_PROTO_TYPES:
        print(f'{protocol} is not a valid ip protocol.')
    elif not isinstance(port, int) or port < 0 or port > 65535:
        print(f'{port} is not a valid ip port number.')
    elif not isinstance(float(timeout), float) or timeout < 0:
        print(f'{timeout} is not a valid timeout number.')
    else:
        if protocol == IP_PROTO_TYPES[0]:
            proto = socket.SOCK_STREAM
        elif protocol == IP_PROTO_TYPES[1]:
            proto = socket.SOCK_DGRAM
        with closing(socket.socket(socket.AF_INET, proto)) as sock:
            sock.settimeout(timeout)
            return sock.connect_ex((host, port)) == 0
    return False


def tcp_port_is_open(host: str, port: int) -> bool:
    """
    Checks if the port is open on ip address for TCP protocol

    :param host: Checked ip address
    :type host: str
    
    :param port: Checked port number from 1 to 65535
    :type port: int

    :returns: Port is open (True) or not (False)
    :rtype: bool
    """
    return port_is_open(host, 'tcp', port)


def udp_port_is_open(host: str, port: int) -> bool:
    """
    Checks if the port is open on ip address for UDP protocol

    :param host: Checked ip address
    :type host: str
    
    :param port: Checked port number from 1 to 65535
    :type port: int

    :returns: Port is open (True) or not (False)
    :rtype: bool
    """
    return port_is_open(host, 'udp', port)


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


def snmp_is_enabled(host: str) -> bool:
    """
    Checks if the port udp/161 (SNMP) is open on the ip address

    :param host: Checked ip address
    :type host: str

    :returns: Port is open (True) or not (False)
    :rtype: bool
    """
    return udp_port_is_open(host, 161)
