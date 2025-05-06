from traceback import print_tb
import aiosnmp
from typing import Optional
import json
from ndce.net import is_ip_address
from ndce.helpers import NestedNamespace


SNMP_COMMUNITY = 'iMAXPublic'
SNMP_PORT = 161
SNMP_TIMEOUT = 1
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
                return str(result[0].value)
            except Exception as err:
                print(f'Could not get {oid} value from {host} host.', err)


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
    if result in MKT_SYS_OBJECT_IDS:
        if result == MKT_SYS_OBJECT_IDS[0]:
            # RouterOS device
            # MikroTik routers snmp system description
            # is in 'RouterOS RB750GL' format.
            # We have to get rid of beginning RouterOS word.
            sys_descr = await get_system_description(host)
            model = ''.join(sys_descr.split()[1::])
            category = 'Router'
        elif result == MKT_SYS_OBJECT_IDS[1]:
            # SwOS device
            # MikroTik switches snmp system description
            # is in 'RB260GS' format. We leave it as is.
            model = get_system_description(host)
            category = 'Switch'
        return NestedNamespace({
            'vendor': 'MikroTik',
            'model': model,
            'category': category
        })
    else:
        with open(SYS_OBJECT_IDS_DB) as file:
            sys_object_ids = json.load(file)
        if result in sys_object_ids.keys():
            return NestedNamespace(sys_object_ids[result])
        else:
            return NestedNamespace({
                'vendor': 'Unknown',
                'model': 'Unknown',
                'category': 'Unknown'
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