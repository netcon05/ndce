from typing import Dict, Any, List
from nicegui import ui, app
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
categories = []
vendors = []
models = []


def load_db() -> None:
    rows.clear()
    for device in app.storage.general.setdefault('db', []):
        add_device(device)


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


def add_device(device: Dict[str, str]) -> None:
    rows.append(device)
    if not device['category'] in categories:
        categories.append(device['category'])
    if not device['vendor'] in vendors:
        vendors.append(device['vendor'])
    if not device['model'] in models:
        models.append(device['model'])


def get_devices_count() -> int:
    return len(app.storage.general.setdefault('db', []))


def apply_filter() -> None:
    rows.clear()
    rows.extend(list(filter(
        filter_devices,
        app.storage.general.setdefault('db', [])
    )))
    table.update()


def reset_filter() -> None:
    for filter in filters.descendants():
        filter.set_value('')


def filter_devices(device: Dict[str, str]) -> List[Dict[str, str]]:
    result = True
    if categories_list.value:
        result &= device['category'] == categories_list.value
    if vendors_list.value:
        result &= device['vendor'] == vendors_list.value
    if models_list.value:
        result &= device['model'] == models_list.value
    return result


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


async def discover_devices(subnet: str) -> None:
    clear_db()
    status_label.set_text('Идет опрос устройств')
    table.props(add='loading')
    status.set_visibility(True)
    hosts = get_hosts_from_subnet(subnet)
    for host in hosts:
        row = await get_row_data(host)
        if row:
            app.storage.general.setdefault('db', []).append(row)
            add_device(row)
            update_ui()
    status.set_visibility(False)
    table.props(remove='loading')
    ui.notify(
        message=f'Обнаружено {get_devices_count()} устройств',
        position='top',
        type='positive'
    )


async def show_search_dialog() -> ui.dialog:
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
    with ui.dialog(value=True) as search_dialog, ui.card().props('square'):
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
                on_click=get_subnet
            ).classes('w-24').props('square')
            ui.button(
                'Отмена',
                on_click=search_dialog.close
            ).classes('w-24').props('square')


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
                'square autofocus standout autogrow outlined input-class=max-h-64'
            )
            with ui.row().classes('w-full justify-between'):
                ui.button(
                    'Начать'
                ).classes('w-24').props('square')
                ui.button(
                    'Отмена',
                    on_click=configure_dialog.close
                ).classes('w-24').props('square')


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
        on_click=show_configure_dialog
    ) as btn_configure:
        btn_configure.props('flat square')
        btn_configure.classes('text-white px-2')
        btn_configure.tooltip('Конфигурирование')
    with ui.button(
        icon = 'search',
        on_click=show_search_dialog
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
        ).classes('w-full').props('outlined dense square')
        vendors_list = ui.select(
            vendors,
            on_change=apply_filter,
            label = 'Производитель'
        ).classes('w-full').props('outlined dense square')
        models_list = ui.select(
            models,
            on_change=apply_filter,
            label = 'Модель'
        ).classes('w-full').props('outlined dense square')
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
    ui.run(title=APP_TITLE)
