from typing import Dict, List
import json
import time
import math
import asyncio
from nicegui import ui, app
from ndce.snmp import get_device_info
from ndce.net import (
    telnet_is_enabled,
    ssh_is_enabled,
    get_hosts_from_subnet,
    is_ip_subnet
)
from ndce.telnet import Telnet
from config import (
    APP_TITLE,
    MAX_CONCURRENT,
    ROWS_PER_PAGE,
    ROWS_COUNT_OPTIONS,
    SYS_OBJECT_IDS_DB,
    COLUMNS_SETTINGS,
    COLUMNS_DEFAULTS
)


def dark_mode(change: bool = True):
    if change:
        if dark.value:
            dark.disable()
        else:
            dark.enable()
        app.storage.general['dark_mode'] = dark.value
    if not dark.value:
        btn_mode.set_icon('dark_mode')
        btn_mode.tooltip('Темный')
        table.classes(add='border')
        telnet_switch.classes(add='bg-gray-100')
        ssh_switch.classes(add='bg-gray-100')
        table.props(remove='separator="none"')
        filter_drawer.props(add='bordered')
        categories_list.props(add='outlined')
        vendors_list.props(add='outlined')
        models_list.props(add='outlined')
        rows_count_dropdown.props(add='options-dark="false"')
    else:
        btn_mode.set_icon('light_mode')
        btn_mode.tooltip('Светлый')
        table.classes(remove='border')
        telnet_switch.classes(remove='bg-gray-100')
        ssh_switch.classes(remove='bg-gray-100')
        table.props(add='separator="none"')
        filter_drawer.props(remove='bordered')
        categories_list.props(remove='outlined')
        vendors_list.props(remove='outlined')
        models_list.props(remove='outlined')
        rows_count_dropdown.props(remove='options-dark="false"')
    

def add_device(device: Dict[str, str]) -> None:
    rows.append(device)
    if not device['category'] in categories:
        categories.append(device['category'])
    if not device['vendor'] in vendors:
        vendors.append(device['vendor'])
    if not device['model'] in models:
        models.append(device['model'])
    update_ui()


def update_ui() -> None:
    table.update()
    categories_list.update()
    vendors_list.update()
    models_list.update()
    total_devices.set_text(get_devices_count())
    total_categories.set_text(len(categories))
    total_vendors.set_text(len(vendors))
    total_models.set_text(len(models))
    total_filtered.set_text(len(rows))


def clear_db() -> None:
    app.storage.general.pop('db')
    rows.clear()
    categories.clear()
    vendors.clear()
    models.clear()
    update_ui()


def delete_devices():
    if table.selected:
        table.remove_rows(table.selected)
        rows = table.rows
        app.storage.general['db'] = rows
    else:
        ui.notify(
            message='Выберите устройства',
            position='top',
            type='warning'
        )


def change_rows_count(value: int):
    global rows_count
    rows_count = value
    app.storage.general['rows_per_page'] = value


def get_devices_count() -> int:
    return len(app.storage.general.get('db', []))


def apply_filter() -> None:
    rows.clear()
    rows.extend(list(filter(
        filter_devices,
        app.storage.general.get('db', [])
    )))
    total_filtered.set_text(len(rows))
    table.update()


def filter_devices(device: Dict[str, str]) -> List[Dict[str, str]]:
    result = True
    if categories_list.value:
        result &= device['category'] == categories_list.value
    if vendors_list.value:
        result &= device['vendor'] == vendors_list.value
    if models_list.value:
        result &= device['model'] == models_list.value
    if telnet_switch.value and ssh_switch.value:
        result &= True
    elif telnet_switch.value:
        result &= device['telnet']
    elif ssh_switch.value:
        result &= device['ssh']
    else:
        result &= not device['telnet'] and not device['ssh']
    return result


def reset_filter() -> None:
    for filter in filters.descendants():
        filter.set_value('')
        filter.set_value(True)


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
        clear_db_switch = ui.switch(
            'Очистить базу данных',
            value=True
        ).classes('w-full pr-3 bg-gray-100')
        with ui.row().classes('w-full justify-between'):
            ui.button(
                'Начать',
                on_click=lambda: get_subnet(
                    discover_dialog,
                    subnet.value,
                    clear_db_switch.value
                )
            ).classes('w-24').props('square unelevated')
            ui.button(
                'Отмена',
                on_click=discover_dialog.close
            ).classes('w-24').props('square unelevated')
        if dark.value:
            clear_db_switch.classes(remove='bg-gray-100')


async def get_subnet(dialog: ui.dialog, subnet: str, clear: bool) -> None:
    if is_ip_subnet(subnet):
        start_time = time.time()
        if clear: clear_db()
        dialog.close()
        status_label.set_text('Обнаружение устройств')
        status.set_visibility(True)
        table.props(add='loading')
        hosts = get_hosts_from_subnet(subnet)
        semaphore = asyncio.Semaphore(MAX_CONCURRENT)
        tasks = [
            asyncio.create_task(discover_device(host, semaphore))
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


async def discover_device(host: str, semaphore: asyncio.Semaphore) -> None:
    device = await get_device_info(host, semaphore, ids)
    if device:
        hosts = [row['host'] for row in rows]
        if not device['host'] in hosts:
            telnet = telnet_is_enabled(host)
            ssh = ssh_is_enabled(host)
            row = {
                'host': device['host'],
                'sysobjectid': device['sysobjectid'],
                'hostname': device['hostname'],
                'vendor': device['vendor'],
                'model': device['model'],
                'category': device['category'],
                'telnet': telnet,
                'ssh': ssh
            }
            app.storage.general.setdefault('db', []).append(row)
            add_device(row)


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
                ).classes('w-24').props('square unelevated')
                ui.button(
                    'Отмена',
                    on_click=configure_dialog.close
                ).classes('w-24').props('square unelevated')


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
    ips = [device['host'] for device in table.selected]
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


if __name__ in {'__main__', '__mp_main__'}:
    ui.run(title=APP_TITLE, port=8888, reconnect_timeout=60)
    
    ids = {}
    rows = []
    categories = []
    vendors = []
    models = []
    rows_count = app.storage.general.get('rows_per_page', ROWS_PER_PAGE)
    pages_count = 0
    current_page = 0
    dark = ui.dark_mode()
    dark.set_value(app.storage.general.get('dark_mode', False))

    try:
        with open(SYS_OBJECT_IDS_DB) as file:
            ids = json.load(file)
    except:
        ui.notify(
            message='База идентификаторов сетевых устройств не обнаружена',
            position='top',
            type='warning'
        )

    # GUI RENDERING
    # Header section
    with ui.header().classes('items-center py-2'):
        ui.label(APP_TITLE).classes('text-lg')
        ui.space()
        ui.separator().props('vertical color="blue-11"')
        with ui.button(
            icon = 'first_page'
        ) as btn_first_page:
            btn_first_page.props('flat square')
            btn_first_page.classes('text-white px-2')
            btn_first_page.tooltip('Первая страница')
        with ui.button(
            icon = 'chevron_left'
        ) as btn_prev_page:
            btn_prev_page.props('flat square')
            btn_prev_page.classes('text-white px-2')
            btn_prev_page.tooltip('Предыдущая страница')
        pages_label = ui.label(f'{current_page} из {pages_count}')
        with ui.button(
            icon = 'chevron_right'
        ) as btn_next_page:
            btn_next_page.props('flat square')
            btn_next_page.classes('text-white px-2')
            btn_next_page.tooltip('Следующая страница')
        with ui.button(
            icon = 'last_page'
        ) as btn_last_page:
            btn_last_page.props('flat square')
            btn_last_page.classes('text-white px-2')
            btn_last_page.tooltip('Последняя страница')
        ui.separator().props('vertical color="blue-11"')
        rows_count_dropdown = ui.select(
            ROWS_COUNT_OPTIONS,
            value=rows_count,
            on_change=lambda: change_rows_count(rows_count_dropdown.value) 
        ).props(
            'dense dark borderless options-dark="false"'
        ).tooltip('Устройств на странице')
        ui.separator().props('vertical color="blue-11"')
        with ui.button(
            icon = 'delete_outline',
            on_click=delete_devices
        ) as btn_delete_rows:
            btn_delete_rows.props('flat square')
            btn_delete_rows.classes('text-white px-2')
            btn_delete_rows.tooltip('Удаление устройств')
        with ui.button(
            icon = 'clear',
            on_click=clear_db
        ) as btn_clear_db:
            btn_clear_db.props('flat square')
            btn_clear_db.classes('text-white px-2')
            btn_clear_db.tooltip('Очистка БД')
        ui.separator().props('vertical color="blue-11"')
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
        ) as btn_discover:
            btn_discover.props('flat square')
            btn_discover.classes('text-white px-2')
            btn_discover.tooltip('Обнаружение')
        ui.separator().props('vertical color="blue-11"')
        with ui.button(
            icon = 'dark_mode',
            on_click=dark_mode
        ) as btn_mode:
            btn_mode.props('flat square')
            btn_mode.classes('text-white px-2')
            btn_mode.tooltip('Темный')
    # Right drawer section
    with ui.right_drawer(
        fixed = True,
        value = True
    ).props('bordered') as filter_drawer:
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
            telnet_switch = ui.switch(
                'Включен протокол telnet',
                value=True,
                on_change=apply_filter
            ).classes('w-full pr-3 bg-gray-100')
            ssh_switch = ui.switch(
                'Включен протокол ssh',
                value=True,
                on_change=apply_filter
            ).classes('w-full pr-3 bg-gray-100')
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
        ).classes('w-full').props('square unelevated')
    # Table section
    with ui.table(
        rows = rows,
        columns = COLUMNS_SETTINGS,
        column_defaults = COLUMNS_DEFAULTS,
        row_key = 'host',
        selection = 'multiple',
        on_select=lambda: total_selected.set_text(len(table.selected))
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
    # Footer section
    with ui.footer().classes('items-center py-2'):
        ui.label('Устройств:')
        total_devices = ui.label('0')
        ui.separator().props('vertical color="blue-11"')
        ui.label('Категорий:')
        total_categories = ui.label('0')
        ui.separator().props('vertical color="blue-11"')
        ui.label('Производителей:')
        total_vendors = ui.label('0')
        ui.separator().props('vertical color="blue-11"')
        ui.label('Моделей:')
        total_models = ui.label('0')
        ui.separator().props('vertical color="blue-11"')
        ui.label('Выбрано:')
        total_selected = ui.label('0')
        ui.separator().props('vertical color="blue-11"')
        ui.label('Фильтровано:')
        total_filtered = ui.label('0')
        
    dark_mode(False)

    for device in app.storage.general.get('db', []):
        add_device(device)
    update_ui()
