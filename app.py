from typing import Dict, List
import time
import math
import asyncio
from nicegui import ui, app
from ndce.snmp import (
    get_ports_count,
    get_device_info,
    get_system_name
)
from ndce.net import (
    telnet_is_enabled,
    ssh_is_enabled,
    get_hosts_from_subnet,
    is_ip_subnet
)
from ndce.telnet import Telnet
from config import (
    APP_TITLE,
    COLUMNS_SETTINGS,
    COLUMNS_DEFAULTS,
    MAX_CONCURRENT
)


rows = []
categories = []
vendors = []
models = []


def load_db() -> None:
    rows.clear()
    for device in app.storage.general.setdefault('db', []):
        add_device(device)
    update_ui()


def add_device(device: Dict[str, str]) -> None:
    rows.append(device)
    if not device['category'] in categories:
        categories.append(device['category'])
    if not device['vendor'] in vendors:
        vendors.append(device['vendor'])
    if not device['model'] in models:
        models.append(device['model'])


def update_ui() -> None:
    table.update()
    categories_list.update()
    vendors_list.update()
    models_list.update()


def clear_db() -> None:
    app.storage.general.pop('db')
    rows.clear()
    categories.clear()
    vendors.clear()
    models.clear()
    update_ui()


def get_devices_count() -> int:
    return len(app.storage.general.setdefault('db', []))


def apply_filter() -> None:
    rows.clear()
    rows.extend(list(filter(
        filter_devices,
        app.storage.general.setdefault('db', [])
    )))
    table.update()


def filter_devices(device: Dict[str, str]) -> List[Dict[str, str]]:
    result = True
    if categories_list.value:
        result &= device['category'] == categories_list.value
    if vendors_list.value:
        result &= device['vendor'] == vendors_list.value
    if models_list.value:
        result &= device['model'] == models_list.value
    return result


def reset_filter() -> None:
    for filter in filters.descendants():
        filter.set_value('')


def show_discover_dialog() -> ui.dialog:
    with ui.dialog(value=True) as discover_dialog, ui.card().props('square'):
        title = ui.label('Обнаружение устройств')
        title.classes(
            '''
            w-full bg-primary text-base text-center
            text-white py-2 absolute left-0 top-0
            '''
        )
        subnet = ui.input(
            label='Подсеть'
        ).classes('w-full mt-10').props('square autofocus outlined clearable')
        with ui.row().classes('w-full justify-between'):
            ui.button(
                'Начать',
                on_click=lambda: get_subnet(discover_dialog, subnet.value)
            ).classes('w-24').props('square')
            ui.button(
                'Отмена',
                on_click=discover_dialog.close
            ).classes('w-24').props('square')


async def get_subnet(dialog: ui.dialog, subnet: str) -> None:
    if is_ip_subnet(subnet):
        start_time = time.time()
        dialog.close()
        clear_db()
        status_label.set_text('Проверка доступности устройств')
        status.set_visibility(True)
        table.props(add='loading')
        hosts = get_hosts_from_subnet(subnet)
        semaphore = asyncio.Semaphore(MAX_CONCURRENT)
        tasks = [
            discover_device(host, semaphore)
            for host in hosts
        ]
        await asyncio.gather(*tasks)
        table.props(remove='loading')
        status.set_visibility(False)
        end_time = time.time()
        total_time = end_time - start_time
        ui.notify(
            message=f'''
                Обнаружено {get_devices_count()} 
                устройств за {math.ceil(total_time)} секунд.
            ''',
            position='top',
            type='positive'
        )
    else:
        ui.notify(
            message='Введите адрес подсети',
            position='top',
            type='warning'
        )


async def discover_device(ip: str, semaphore) -> None:
    async with semaphore:
        ports_count = await get_ports_count(ip)
        if ports_count:
            hostname = await get_system_name(ip)
            device = await get_device_info(ip)
            telnet = telnet_is_enabled(ip)
            ssh = ssh_is_enabled(ip)
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
            app.storage.general.setdefault('db', []).append(row)
            add_device(row)
            update_ui()


def show_configure_dialog() -> ui.dialog:
    with ui.dialog(value=True)as configure_dialog:
        with ui.card().classes('w-full max-h-96').props('square'):
            title = ui.label('Конфигурирование устройств')
            title.classes(
                '''
                w-full bg-primary text-base text-center
                text-white py-2 absolute left-0 top-0
                '''
            )
            commands = ui.textarea(
                label='Список команд',
                placeholder='Вводите по одной команде на строку'
            ).classes('w-full mt-10').props(
                '''
                square autofocus standout autogrow
                outlined input-class=max-h-64
                '''
            )
            with ui.row().classes('w-full justify-between'):
                ui.button(
                    'Начать',
                    on_click=lambda: get_commands(
                        configure_dialog, commands.value
                    )
                ).classes('w-24').props('square')
                ui.button(
                    'Отмена',
                    on_click=configure_dialog.close
                ).classes('w-24').props('square')


async def get_commands(dialog: ui.dialog, value: str) -> None:
    if value:
        dialog.close()
        await send_commands(value)
    else:
        ui.notify(
            message='Введите команды для выполнения',
            position='top',
            type='warning'
        )


async def send_commands(value: str) -> None:
    ips = [device['address'] for device in table.selected]
    commands = [f'{command}\n' for command in value.split('\n')]
    tasks = [
        Telnet(ip=ip, commands=commands).cli_connect() for ip in ips
    ]
    status_label.set_text('Идет передача комманд')
    table.props(add='loading')
    status.set_visibility(True)
    await asyncio.gather(*tasks)
    status.set_visibility(False)
    table.props(remove='loading')
    ui.notify(
        message=f'Передано {len(commands)} команд на {len(ips)} устройств',
        position='top',
        type='positive'
    )


# GUI RENDERING
# Header section
with ui.header().classes('items-center py-2'):
    ui.label(APP_TITLE).classes('text-lg')
    ui.space()
    with ui.button(
        icon = 'clear',
        on_click=clear_db
    ) as btn_configure:
        btn_configure.props('flat square')
        btn_configure.classes('text-white px-2')
        btn_configure.tooltip('Очистка БД')
    with ui.button(
        icon = 'tune',
        on_click=lambda: (
            show_configure_dialog()
            if len(table.selected) > 0
            else ui.notify(
                message='Выберите устройства',
                position='top',
                type='warning'
            )
        )
    ) as btn_configure:
        btn_configure.props('flat square')
        btn_configure.classes('text-white px-2')
        btn_configure.tooltip('Конфигурирование')
    with ui.button(
        icon = 'search',
        on_click=show_discover_dialog
    ) as btn_subnet:
        btn_subnet.props('flat square')
        btn_subnet.classes('text-white px-2')
        btn_subnet.tooltip('Обнаружение')
# Right drawer section
with ui.right_drawer(fixed = True, value = True).props('bordered'):
    with ui.column().classes('w-full') as filters:
        categories_list = ui.select(
            categories,
            on_change=apply_filter,
            label = 'Категория'
        ).classes('w-full').props('outlined dense square clearable')
        vendors_list = ui.select(
            vendors,
            on_change=apply_filter,
            label = 'Производитель'
        ).classes('w-full').props('outlined dense square clearable')
        models_list = ui.select(
            models,
            on_change=apply_filter,
            label = 'Модель'
        ).classes('w-full').props('outlined dense square clearable')
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
    ).classes('w-full').props('square')
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
        <q-td key="snmp" :props="props">
            <q-badge rounded :color="props.value == 0 ? 'red' : 'green'" />
        </q-td>
    ''')
    table.add_slot('body-cell-telnet', '''
        <q-td key="telnet" :props="props">
            <q-badge rounded :color="props.value == 0 ? 'red' : 'green'" />
        </q-td>
    ''')
    table.add_slot('body-cell-ssh', '''
        <q-td key="ssh" :props="props">
            <q-badge rounded :color="props.value == 0 ? 'red' : 'green'" />
        </q-td>
    ''')


if __name__ in {'__main__', '__mp_main__'}:
    load_db()
    ui.run(title=APP_TITLE, port=8888)
