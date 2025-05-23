APP_TITLE = 'NDCE : Network Device Configuration Editor'

DB_NAME = 'ndce/ndce.db'

SOCKET_TIMEOUT = 1

USERNAME = 'admin'
PASSWORD = 'admin'

MAX_CONCURRENT = 32

SNMP_TIMEOUT = 2
SNMP_RETRIES = 3
SNMP_PORT = 161
SNMP_COMMUNITY = 'public'

SNMP_IF_NUMBER = '1.3.6.1.2.1.2.1.0'
SNMP_SYS_NAME = '1.3.6.1.2.1.1.5.0'
SNMP_SYS_DESCR = '1.3.6.1.2.1.1.1.0'
SNMP_SYS_OBJECT_ID = '1.3.6.1.2.1.1.2.0'

MKT_SYS_OBJECT_IDS = [
    '.1.3.6.1.4.1.14988.1',
    '.1.3.6.1.4.1.14988.2'
]

SYS_OBJECT_IDS_DB = 'ndce/ids.json'

COLUMNS_SETTINGS = [
    {
        'name': 'address',
        'label': 'Адрес',
        'field': 'address',
        'sortable': True,
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
        'name': 'snmp',
        'label': 'Snmp',
        'field': 'snmp',
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

COLUMNS_DEFAULTS = {
    'align': 'center',
    'headerClasses': 'text-primary'
}
