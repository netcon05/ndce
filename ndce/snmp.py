import aiosnmp
from typing import Dict, Optional, Any
import json
from config import (
    SNMP_PORT,
    SNMP_COMMUNITY,
    SNMP_TIMEOUT,
    SNMP_RETRIES,
    SNMP_IF_NUMBER,
    SNMP_SYS_NAME,
    SNMP_SYS_DESCR,
    SNMP_SYS_OBJECT_ID,
    MKT_SYS_OBJECT_IDS,
    SYS_OBJECT_IDS_DB
)


async def get_snmp_value(
    oid: str,
    ip: str,
    port: Optional[int] = SNMP_PORT,
    community: Optional[str] = SNMP_COMMUNITY,
    timeout: Optional[int] = SNMP_TIMEOUT,
    retries: Optional[int] = SNMP_RETRIES
) -> Any:
    try:
        async with aiosnmp.Snmp(
            host=ip,
            port=port,
            community=community,
            timeout=timeout,
            retries=retries,
            validate_source_addr=False
        ) as snmp:
                result = await snmp.get(oid)
                if isinstance(result[0].value, bytes):
                    return result[0].value.decode('utf-8')
                return str(result[0].value)
    except:
        return ''


async def get_ports_count(ip: str) -> int:
    result = await get_snmp_value(SNMP_IF_NUMBER, ip)
    return result


async def get_system_name(ip: str) -> str:
    result = await get_snmp_value(SNMP_SYS_NAME, ip)
    return result


async def get_system_description(ip: str) -> str:
    result = await get_snmp_value(SNMP_SYS_DESCR, ip)
    return result


async def get_system_object_id(ip: str) -> str:
    result = await get_snmp_value(SNMP_SYS_OBJECT_ID, ip)
    return result


async def get_device_info(ip: str) -> Dict[str, str]:
    sys_object_id = await get_system_object_id(ip)
    if sys_object_id:
        if sys_object_id in MKT_SYS_OBJECT_IDS:
            sys_descr = await get_system_description(ip)
            if sys_descr:
                if sys_object_id == MKT_SYS_OBJECT_IDS[0]:
                    # RouterOS устройство
                    # Маршрутизаторы MikroTik отдают SYS_DESCR в формате
                    # 'RouterOS RB750GL'. Необходимо удалить начальное RouterOS.
                    model = ''.join(sys_descr.split()[1::])
                    category = 'Router'
                elif sys_object_id == MKT_SYS_OBJECT_IDS[1]:
                    # SwOS устройство
                    # Коммутаторы MikroTik отдают SYS_DESCR в формате
                    # 'RB260GS'. Оставляем как есть.
                    model = sys_descr
                    category = 'Switch'
                return {
                    'vendor': 'MikroTik',
                    'model': model,
                    'category': category,
                    'host': ip
                }
        else:
            try:
                with open(SYS_OBJECT_IDS_DB) as file:
                    sys_object_ids = json.load(file)
                if sys_object_id in sys_object_ids.keys():
                    result = sys_object_ids[sys_object_id]
                    result['host'] = ip
                    return result
            except Exception as err:
                print(err)
    return {
        'vendor': 'Unknown',
        'model': 'Unknown',
        'category': 'Unknown',
        'host': ip
    }
