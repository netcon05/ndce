from typing import Dict, Any
from nicegui import ui
from ndce.snmp import (
    get_device_info,
    get_system_name
)
from ndce.net import (
    telnet_is_enabled,
    ssh_is_enabled,
    get_hosts_from_subnet,
    is_ip_subnet
)
from config import (
    APP_TITLE,
    COLUMNS_SETTINGS,
    COLUMNS_DEFAULTS
)


rows = []


def reset_filter():
    for filter in filters.descendants():
        filter.set_value('')


async def get_row_data(host: str) -> Dict[str, Any]:
    row = {}
    hostname = await get_system_name(host)
    if hostname:
        device = await get_device_info(host)
        telnet = telnet_is_enabled(host)
        ssh = ssh_is_enabled(host)
        row = {
            'address': device['host'],
            'hostname': hostname,
            'vendor': device['vendor'],
            'model': device['model'],
            'category': device['category'],
            'snmp': True,
            'telnet': telnet,
            'ssh': ssh
        }
    return row


async def show_search_dialog():
    
    async def get_subnet():
        if is_ip_subnet(subnet.value):
            search_dialog.close()
            await discover_devices(subnet.value)
        else:
            ui.notify(
                message='Введите адрес подсети в правильном формате.',
                position='top',
                type='negative'
            )
            
    with ui.dialog(value=True) as search_dialog, ui.card():
        title = ui.label('Обнаружение устройств')
        title.classes(
            '''
            w-full bg-primary text-base text-center 
            text-white py-2 absolute left-0 top-0
            '''
        )
        subnet = ui.input(
            label='Подсеть'
        ).classes('w-full mt-9').props('outlined dense')
        with ui.row():
            ui.button(
                'Начать',
                on_click=get_subnet
            ).classes('w-24')
            ui.button(
                'Отмена',
                on_click=search_dialog.close
            ).classes('w-24')


async def discover_devices(subnet: str) -> None:
    rows.clear()
    status_label.set_text('Идет опрос устройств')
    table.props(add='loading')
    status.set_visibility(True)
    hosts = get_hosts_from_subnet(subnet)
    for host in hosts:
        row = await get_row_data(host)
        if row:
            rows.append(row)
            table.update()
    status.set_visibility(False)
    table.props(remove='loading')
    ui.notify(
        message=f'Обнаружено {len(rows)} устройств',
        position='top',
        type='positive'
    )


# GUI RENDERING
# Header section
with ui.header().classes('items-center py-2'):
    ui.label(APP_TITLE).classes('text-lg')
    ui.space()
    with ui.button(icon = 'tune') as btn_configure:
        btn_configure.props('flat')
        btn_configure.classes('text-white px-2')
        btn_configure.tooltip('Конфигурирование')
    with ui.button(
        icon = 'search',
        on_click=show_search_dialog
    ) as btn_subnet:
        btn_subnet.props('flat')
        btn_subnet.classes('text-white px-2')
        btn_subnet.tooltip('Обнаружение')
# Right drawer section
with ui.right_drawer(fixed = True, value = True).props('bordered'):
    with ui.column().classes('w-full') as filters:
        categories_list = ui.select(
            [],
            label = 'Категория'
        ).classes('w-full').props('outlined dense')
        vendors_list = ui.select(
            [],
            label = 'Производитель'
        ).classes('w-full').props('outlined dense')
        models_list = ui.select(
            [],
            label = 'Модель'
        ).classes('w-full').props('outlined dense')
        fields_list = ui.select(
            [],
            label = 'Поле'
        ).classes('w-full').props('outlined dense')
        conditions_list = ui.select(
            [],
            label='Условие'
        ).classes('w-full').props('outlined dense')
        condition_value = ui.input(label = 'Значение').classes(
            'w-full'
        ).props('outlined dense')
    ui.space()
    with ui.column().classes(
        'w-full items-center'
    ) as status:
        status.set_visibility(False)
        status_spinner = ui.spinner(type='tail', size='64px')
        status_label = ui.label().classes('text-center')
    ui.space()
    ui.button(
        'Сбросить фильтр',
        on_click = reset_filter
    ).classes('w-full').props('flat')
# Table section
with ui.table(
    rows = rows,
    columns = COLUMNS_SETTINGS,
    column_defaults = COLUMNS_DEFAULTS,
    row_key = 'address',
    selection = 'multiple'
) as table:
    table.classes('shadow-none border rounded-none w-full')
    table.props('dense hide-selected-banner hide-no-data')
    table.add_slot('body-cell-snmp', '''
        <q-td key = "snmp" :props = "props">
            <q-badge :color = "props.value == 0 ? 'red' : 'green'">
            </q-badge>
        </q-td>
    ''')
    table.add_slot('body-cell-telnet', '''
        <q-td key = "telnet" :props = "props">
            <q-badge :color = "props.value == 0 ? 'red' : 'green'">
            </q-badge>
        </q-td>
    ''')
    table.add_slot('body-cell-ssh', '''
        <q-td key = "ssh" :props = "props">
            <q-badge :color = "props.value == 0 ? 'red' : 'green'">
            </q-badge>
        </q-td>
    ''')


if __name__ in {'__main__', '__mp_main__'}:
    ui.run(title=APP_TITLE)
