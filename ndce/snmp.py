from typing import Dict, Optional, Any, List
import asyncio
import aiosnmp
from ndce.icmp import ping_host
import config


async def get_snmp_values(
    oids: List[str],
    host: str,
    semaphore: asyncio.Semaphore,
    port: Optional[int] = config.SNMP_PORT,
    community: Optional[str] = config.SNMP_COMMUNITY,
    timeout: Optional[int] = config.SNMP_TIMEOUT,
    retries: Optional[int] = config.SNMP_RETRIES
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
    oids = [
        config.SNMP_SYS_NAME,
        config.SNMP_SYS_DESCR,
        config.SNMP_SYS_OBJECT_ID
    ]
    device_info = await get_snmp_values(oids, host, semaphore)
    if device_info:
        result = {'host': host}
        hostname, description, objectid = device_info
        if hostname:
            result['hostname'] = hostname
        if objectid:
            result['sysobjectid'] = objectid
            if  objectid in config.MKT_SYS_OBJECT_IDS:
                result['vendor'] = 'MikroTik'
                if description:
                    if objectid == config.MKT_SYS_OBJECT_IDS[0]:
                        # RouterOS устройство
                        # Маршрутизаторы MikroTik отдают SYS_DESCR
                        # в формате 'RouterOS RB750GL'.
                        # Необходимо удалить начальное RouterOS.
                        result['model'] = ''.join(description.split()[1::])
                        result['category'] = 'Router'
                    elif objectid == config.MKT_SYS_OBJECT_IDS[1]:
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