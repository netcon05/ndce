import aiosnmp
from typing import Optional
from ndce.net import is_ip_address
from ndce.sysobjectids import sysobjectids
from ndce.helpers import NestedNamespace


SNMP_COMMUNITY = 'public'
SNMP_PORT = 161
SNMP_TIMEOUT = 1
SNMP_SYS_NAME = '1.3.6.1.2.1.1.5.0'
SNMP_SYS_DESCR = '1.3.6.1.2.1.1.1.0'
SNMP_SYS_OBJECT_ID = '1.3.6.1.2.1.1.2.0'


async def get_snmp_value(
    oid: str,
    host: str,
    port: Optional[int] = SNMP_PORT,
    community: Optional[str] = SNMP_COMMUNITY,
    timeout: Optional[int] = SNMP_TIMEOUT
) -> str:
    if not is_ip_address(host):
        print(f'{host} is not a valid ip address.')
    elif not isinstance(port, int) or port < 0 or port > 65535:
        print(f'{port} is not a valid ip port number.')
    elif not community.strip():
        print('No snmp community passed.')
    elif not isinstance(timeout, int) or timeout < 0:
        print(f'{timeout} is not a valid timeout number.')
    else:
        async with aiosnmp.Snmp(
            host=host,
            port=port,
            community=community,
            timeout=timeout
        ) as snmp:
            try:
                result = await snmp.get(oid)
                return result[0].value.decode('utf-8')
            except Exception as err:
                print('Could not get {oid} value from {host} host.', err)


async def get_system_name(host: str) -> str:
    result = await get_snmp_value(SNMP_SYS_NAME, host)
    return result


async def get_system_description(host: str) -> str:
    result = await get_snmp_value(SNMP_SYS_DESCR, host)
    return result


async def get_system_object_id(host: str) -> str:
    result = await get_snmp_value(SNMP_SYS_OBJECT_ID, host)
    return result


async def get_device_info(host: str) -> str:
    result = await get_system_object_id(host)
    if result in sysobjectids.keys():
        return sysobjectids[result]
    else:
        return NestedNamespace({
            "vendor": "Unknown",
            "model": "Unknown",
            "category": "Unknown"
        })


async def get_vendor_name(host: str) -> str:
    result = await get_device_info(host)
    return result.vendor


async def get_model_name(host: str) -> str:
    result = await get_device_info(host)
    return result.model


async def get_device_category(host: str) -> str:
    result = await get_device_info(host)
    return result.category