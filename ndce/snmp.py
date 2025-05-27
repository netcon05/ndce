from typing import Dict, Optional, Any, List
import asyncio
import aiosnmp
from ndce.icmp import ping_host
from config import (
    SNMP_PORT,
    SNMP_COMMUNITY,
    SNMP_TIMEOUT,
    SNMP_RETRIES,
    SNMP_SYS_NAME,
    SNMP_SYS_DESCR,
    SNMP_SYS_OBJECT_ID,
    MKT_SYS_OBJECT_IDS
)


async def get_snmp_values(
    oids: List[str],
    host: str,
    semaphore: asyncio.Semaphore,
    port: Optional[int] = SNMP_PORT,
    community: Optional[str] = SNMP_COMMUNITY,
    timeout: Optional[int] = SNMP_TIMEOUT,
    retries: Optional[int] = SNMP_RETRIES
) -> Any:
    async with semaphore:
        values = []
        host_is_accessable = await ping_host(host)
        if host_is_accessable:
            try:
                async with aiosnmp.Snmp(
                    host=host,
                    port=port,
                    community=community,
                    timeout=timeout,
                    retries=retries,
                    validate_source_addr=False
                ) as snmp:
                    results = await snmp.get(oids)
                    values = []
                    for result in results:
                        if isinstance(result.value, bytes):
                            values.append(result.value.decode('utf-8'))
                        else:
                            values.append(str(result.value))
            except Exception as err:
                print(host, err)
        return values


async def get_device_info(
    host: str,
    semaphore: asyncio.Semaphore,
    ids: List[Dict[str, str]]
) -> Dict[str, str]:
    oids = [SNMP_SYS_NAME, SNMP_SYS_DESCR, SNMP_SYS_OBJECT_ID]
    device_info = await get_snmp_values(oids, host, semaphore)
    if device_info:
        hostname, description, objectid = device_info
        if objectid:
            if  objectid in MKT_SYS_OBJECT_IDS:
                if description:
                    if objectid == MKT_SYS_OBJECT_IDS[0]:
                        # RouterOS устройство
                        # Маршрутизаторы MikroTik отдают SYS_DESCR
                        # в формате 'RouterOS RB750GL'.
                        # Необходимо удалить начальное RouterOS.
                        model = ''.join(description.split()[1::])
                        category = 'Router'
                    elif objectid == MKT_SYS_OBJECT_IDS[1]:
                        # SwOS устройство
                        # Коммутаторы MikroTik отдают SYS_DESCR
                        # в формате 'RB260GS'.
                        # Оставляем как есть.
                        model = description
                        category = 'Switch'
                    return {
                        'host': host,
                        'hostname': hostname,
                        'vendor': 'MikroTik',
                        'model': model,
                        'category': category,
                    }
            else:
                if objectid in ids.keys():
                    result = ids[objectid]
                    result['host'] = host
                    result['hostname'] = hostname
                    return result