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
    """
    Функция для получения данных по протоколу snmp
    """
    async with semaphore:
        values = []
        host_is_up = await ping_host(host)
        if host_is_up:
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
                    for result in results:
                        # Возвращаемое значение может быть в формате байт строк
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
    """
    Функция возвращает значения hostname, description и sysobjectid
    одним запросом от заданного устройства по протоколу snmp
    """
    oids = [SNMP_SYS_NAME, SNMP_SYS_DESCR, SNMP_SYS_OBJECT_ID]
    result = {
        'host': host,
        'sysobjectid': 'Unknown',
        'hostname': 'Unknown',
        'vendor': 'Unknown',
        'model': 'Unknown',
        'category': 'Unknown',
    }
    device_info = await get_snmp_values(oids, host, semaphore)
    if device_info:
        hostname, description, objectid = device_info
        if hostname:
            result['hostname'] = hostname
        if objectid:
            result['sysobjectid'] = objectid
            if  objectid in MKT_SYS_OBJECT_IDS:
                result['vendor'] = 'MikroTik'
                if description:
                    if objectid == MKT_SYS_OBJECT_IDS[0]:
                        # RouterOS устройство
                        # Маршрутизаторы MikroTik отдают SYS_DESCR
                        # в формате 'RouterOS RB750GL'.
                        # Необходимо удалить начальное RouterOS.
                        result['model'] = ''.join(description.split()[1::])
                        result['category'] = 'Router'
                    elif objectid == MKT_SYS_OBJECT_IDS[1]:
                        # SwOS устройство
                        # Коммутаторы MikroTik отдают SYS_DESCR
                        # в формате 'RB260GS'.
                        # Оставляем как есть.
                        result['model'] = description
                        result['category'] = 'Switch'
            elif objectid in ids.keys():
                result['vendor'] = ids[objectid]['vendor']
                result['model'] = ids[objectid]['model']
                result['category'] = ids[objectid]['category']
    return result