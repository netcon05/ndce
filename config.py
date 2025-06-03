APP_TITLE = 'NDCE : Network Device Configuration Editor'

SYS_OBJECT_IDS_DB = 'ndce/ids.json'

# Учетные данные для подключения по telnet и ssh
USERNAME = 'admin'
PASSWORD = 'admin'

# Максимальное количество конкурентно выполняемых корутин
MAX_CONCURRENT = 8

# Количество строк на странице
ROWS_PER_PAGE = 50
# Список вариантов количества строк на странице
ROWS_COUNT_OPTIONS = [0, 25, 50, 100, 250, 500, 1000]

SOCKET_TIMEOUT = 1

PING_TIMEOUT = 1
PING_RETRIES = 5

SNMP_TIMEOUT = 1
SNMP_RETRIES = 1
SNMP_PORT = 161
SNMP_COMMUNITY = 'public'

SNMP_SYS_NAME = '1.3.6.1.2.1.1.5.0'
SNMP_SYS_DESCR = '1.3.6.1.2.1.1.1.0'
SNMP_SYS_OBJECT_ID = '1.3.6.1.2.1.1.2.0'

# В устройствах MikroTik только два вида system object id
# первый для устройств на базе RouterOS
# второй для устройств на базе SwOS
MKT_SYS_OBJECT_IDS = [
    '.1.3.6.1.4.1.14988.1',
    '.1.3.6.1.4.1.14988.2'
]

# Описание столбцов таблицы устройств
COLUMNS_SETTINGS = [
    {
        'name': 'host',
        'label': 'Адрес',
        'field': 'host',
        'sortable': True,
        'required': True
    },
    {
        'name': 'sysobjectid',
        'label': 'OID',
        'field': 'sysobjectid',
        'sortable': False,
        'required': True
    },
    {
        'name': 'hostname',
        'label': 'Имя',
        'field': 'hostname',
        'sortable': True,
        'required': True
    },
    {
        'name': 'vendor',
        'label': 'Производитель',
        'field': 'vendor',
        'sortable': True,
        'required': True
    },
    {
        'name': 'model',
        'label': 'Модель',
        'field': 'model',
        'sortable': True,
        'required': True
    },
    {
        'name': 'category',
        'label': 'Категория',
        'field': 'category',
        'sortable': True,
        'required': True
    },
    {
        'name': 'telnet',
        'label': 'Telnet',
        'field': 'telnet',
        'required': True
    },
    {
        'name': 'ssh',
        'label': 'Ssh',
        'field': 'ssh',
        'required': True
    },
]

# Значения по-умолчанию для столбцов таблицы устройств
COLUMNS_DEFAULTS = {
    'align': 'center',
    'headerClasses': 'text-primary'
}
