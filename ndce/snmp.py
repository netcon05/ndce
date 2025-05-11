import aiosnmp
from typing import Optional, Dict, Any
import json
from config import (
    SNMP_PORT,
    SNMP_COMMUNITY,
    SNMP_TIMEOUT,
    SNMP_RETRIES,
    SNMP_SYS_NAME,
    SNMP_SYS_DESCR,
    SNMP_SYS_OBJECT_ID,
    MKT_SYS_OBJECT_IDS,
    SYS_OBJECT_IDS_DB
)


async def get_snmp_value(
    oid: str,
    host: str,
    port: Optional[int] = SNMP_PORT,
    community: Optional[str] = SNMP_COMMUNITY,
    timeout: Optional[int|float] = SNMP_TIMEOUT,
    retries: Optional[int] = SNMP_RETRIES
) -> Any:
    """
    Подключается к заданному хосту по протоколу SNMP и
    получает данные в соответствии с указанным OID
    
    :param oid: SNMP OID
    :type oid: str
    
    :param host: IP адрес устройства с включенным SNMP
    :type host: str
    
    :param port: SNMP порт
    :type port: int
    
    :param community: SNMP комьюнити только для чтения
    :type community: str
    
    :param timeout: SNMP таймаут
    :type timeout: Optional[int|float]
    
    :param retries: Количество попыток для SNMP
    :type retries: Optional[int]

    :returns: Полученные данные
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
    Возвращает sys_name
    
    :param host: IP адрес устройства с включенным SNMP
    :type host: str
    
    :returns: sys_name устройства
    :rtype: str
    """
    result = await get_snmp_value(SNMP_SYS_NAME, host)
    return result


async def get_system_description(host: str) -> str:
    """
    Возвращает sys_descr
    
    :param host: IP адрес устройства с включенным SNMP
    :type host: str
    
    :returns: sys_descr устройства
    :rtype: str
    """
    result = await get_snmp_value(SNMP_SYS_DESCR, host)
    return result


async def get_system_object_id(host: str) -> str:
    """
    Возвращает sys_object_id в формате OID
    
    :param host: IP адрес устройства с включенным SNMP
    :type host: str
    
    :returns: OID sys_object_id устройства
    :rtype: str
    """
    result = await get_snmp_value(SNMP_SYS_OBJECT_ID, host)
    return result


async def get_device_info(host: str) -> Dict[str, str]:
    """
    Возвращает данные о вендоре, моделе, категории
    и ip адресе устройства
    
    :param host: IP адрес устройства с включенным SNMP
    :type host: str
    
    :returns: Словарь с полями вендор, модель, категория и адрес
    :rtype: Dict[str, str]
    """
    sys_object_id = await get_system_object_id(host)
    if sys_object_id in MKT_SYS_OBJECT_IDS:
        if sys_object_id == MKT_SYS_OBJECT_IDS[0]:
            # RouterOS устройство
            # Маршрутизаторы MikroTik отдают SYS_DESCR в формате
            # 'RouterOS RB750GL'. Необходимо удалить начальное RouterOS.
            sys_descr = await get_system_description(host)
            model = ''.join(sys_descr.split()[1::])
            category = 'Router'
        elif sys_object_id == MKT_SYS_OBJECT_IDS[1]:
            # SwOS устройство
            # Коммутаторы MikroTik отдают SYS_DESCR в формате
            # 'RB260GS'. Оставляем как есть.
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
