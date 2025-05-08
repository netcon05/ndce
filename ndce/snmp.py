import aiosnmp
from typing import Optional, Dict, Any
import json
from ndce.net import is_ip_address


SNMP_PORT = 161
SNMP_COMMUNITY = 'public'
SNMP_TIMEOUT = 1
SNMP_RETRIES = 1

SNMP_SYS_NAME = '1.3.6.1.2.1.1.5.0'
SNMP_SYS_DESCR = '1.3.6.1.2.1.1.1.0'
SNMP_SYS_OBJECT_ID = '1.3.6.1.2.1.1.2.0'

MKT_SYS_OBJECT_IDS = [
    '.1.3.6.1.4.1.14988.1',
    '.1.3.6.1.4.1.14988.2'
]

SYS_OBJECT_IDS_DB = 'ndce/ids.json'


async def get_snmp_value(
    oid: str,
    host: str,
    port: Optional[int] = SNMP_PORT,
    community: Optional[str] = SNMP_COMMUNITY,
    timeout: Optional[int|float] = SNMP_TIMEOUT,
    retries: Optional[int] = SNMP_RETRIES
) -> Any:
    """
    Connects to the HOST using SNMP protocol and
    retrieves data according to the passed snmp OID
    
    :param oid: SNMP OID
    :type oid: str
    
    :param host: SNMP enabled devices ip address
    :type host: str
    
    :param port: SNMP port default is 161
    :type port: int
    
    :param community: SNMP GET community default is public
    :type community: str
    
    :param timeout: SNMP timeout default is 1
    :type timeout: Optional[int|float]
    
    :param retries: SNMP retries default is 1
    :type retries: Optional[int]

    :returns: Retrieved data
    :rtype: Any
    """
    async with aiosnmp.Snmp(
        host=host,
        port=port,
        community=community,
        timeout=timeout,
        retries=retries
    ) as snmp:
        try:
            result = await snmp.get(oid)
            if isinstance(result[0].value, bytes):
                return result[0].value.decode('utf-8')
            return str(result[0].value)
        except Exception as err:
            print(err)
            return ''


async def get_system_name(host: str) -> str:
    """
    Returns devices system name
    
    :param host: SNMP enabled devices ip address
    :type host: str
    
    :returns: Retrieved data string
    :rtype: str
    """
    result = await get_snmp_value(SNMP_SYS_NAME, host)
    return result


async def get_system_description(host: str) -> str:
    """
    Returns devices system description
    
    :param host: SNMP enabled devices ip address
    :type host: str
    
    :returns: Retrieved data string
    :rtype: str
    """
    result = await get_snmp_value(SNMP_SYS_DESCR, host)
    return result


async def get_system_object_id(host: str) -> str:
    """
    Returns devices system object id in OID format
    
    :param host: SNMP enabled devices ip address
    :type host: str
    
    :returns: Retrieved data string
    :rtype: str
    """
    result = await get_snmp_value(SNMP_SYS_OBJECT_ID, host)
    return result


async def get_device_info(host: str) -> Dict[str, str]:
    """
    Returns devices vendor name, model and category
    
    :param host: SNMP enabled devices ip address
    :type host: str
    
    :returns: Dictionary with vendor name, model and category fields
    :rtype: Dict[str, str]
    """
    sys_object_id = await get_system_object_id(host)
    if sys_object_id in MKT_SYS_OBJECT_IDS:
        if sys_object_id == MKT_SYS_OBJECT_IDS[0]:
            # RouterOS device
            # MikroTik routers snmp system description
            # is in 'RouterOS RB750GL' format.
            # We have to get rid of beginning RouterOS word.
            sys_descr = await get_system_description(host)
            model = ''.join(sys_descr.split()[1::])
            category = 'Router'
        elif sys_object_id == MKT_SYS_OBJECT_IDS[1]:
            # SwOS device
            # MikroTik switches snmp system description
            # is in 'RB260GS' format. We leave it as is.
            model = get_system_description(host)
            category = 'Switch'
        return {
            'vendor': 'MikroTik',
            'model': model,
            'category': category,
            'host': host
        }
    else:
        try:
            with open(SYS_OBJECT_IDS_DB) as file:
                sys_object_ids = json.load(file)
            if sys_object_id in sys_object_ids.keys():
                result = sys_object_ids[sys_object_id]
                result['host'] = host
                return result
        except Exception as err:
            print(err)
    return {
        'vendor': 'Unknown',
        'model': 'Unknown',
        'category': 'Unknown',
        'host': host
    }
