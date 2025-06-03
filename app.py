from typing import Dict, List
import json
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
import config


def change_tooltip(element: ui.element, text: str) -> None:
    for child in element:
        if isinstance(child, ui.tooltip):
            element.remove(child)
    element.tooltip(text)


def set_ui_mode() -> None:
    if dark_mode.value:
        btn_mode.set_icon('light_mode')
        btn_mode.tooltip('Светлый')
        devices_table.classes(remove='border')
        telnet_switch.classes(remove='bg-gray-100')
        ssh_switch.classes(remove='bg-gray-100')
        devices_table.props(add='separator="none"')
        filters_drawer.props(remove='bordered')
        lst_categories.props(remove='outlined')
        lst_vendors.props(remove='outlined')
        lst_models.props(remove='outlined')
        rows_per_page_dropdown.props(remove='options-dark="false"')
    else:
        btn_mode.set_icon('dark_mode')
        btn_mode.tooltip('Темный')
        devices_table.classes(add='border')
        telnet_switch.classes(add='bg-gray-100')
        ssh_switch.classes(add='bg-gray-100')
        devices_table.props(remove='separator="none"')
        filters_drawer.props(add='bordered')
        lst_categories.props(add='outlined')
        lst_vendors.props(add='outlined')
        lst_models.props(add='outlined')
        rows_per_page_dropdown.props(add='options-dark="false"')


def change_ui_mode() -> None:
    if dark_mode.value:
        dark_mode.disable()
    else:
        dark_mode.enable()
    app.storage.general['dark_mode'] = dark_mode.value
    set_ui_mode()
    

def add_device(device: Dict[str, str]) -> None:
    db_full.append(device)
    devices_table.add_row(device)
    apply_filters()
    update_ui()


def update_ui() -> None:
    lst_categories.update()
    lst_vendors.update()
    lst_models.update()
    lbl_total_devices.set_text(len(db_full))
    lbl_total_categories.set_text(len(lst_categories.options))
    lbl_total_vendors.set_text(len(lst_vendors.options))
    lbl_total_models.set_text(len(lst_models.options))
    lbl_total_filtered.set_text(len(devices_table.rows))
    lbl_total_selected.set_text(len(devices_table.selected))


def clear_db() -> None:
    app.storage.general.pop('db')
    db_full.clear()
    db_filtered.clear()
    devices_table.clear()
    lst_categories.clear()
    lst_vendors.clear()
    lst_models.clear()
    reset_filters()
    change_page()
    update_ui()


def delete_devices() -> None:
    global db_full
    if devices_table.selected:
        db_full = list(filter(
            lambda row: not row in devices_table.selected,
            db_full
        ))
        app.storage.general['db'] = db_full
        devices_table.remove_rows(devices_table.selected)
        apply_filters()
        update_ui()
    else:
        ui.notify(
            message='Выберите устройства',
            position='top',
            type='warning'
        )


def set_rows_per_page(value: int) -> None:
    global rows_per_page
    app.storage.general['rows_per_page'] = value
    rows_per_page = value
    devices_table.selected = []
    lbl_total_selected.set_text('0')
    apply_filters()


def change_discover_button() -> None:
    if btn_discover.icon == 'search':
        btn_discover.set_icon('stop')
        change_tooltip(btn_discover, 'Остановить обнаружение')
    else:
        btn_discover.set_icon('search')
        change_tooltip(btn_discover, 'Обнаружение')


def change_configure_button() -> None:
    if btn_configure.icon == 'tune':
        btn_configure.set_icon('stop')
        change_tooltip(btn_configure, 'Остановить передачу команд')
    else:
        btn_configure.set_icon('tune')
        change_tooltip(btn_configure, 'Передача команд')


def cancel_discover_tasks() -> None:
    if discover_tasks:
        for task in discover_tasks:
            try:
                task.cancel()
            except Exception as err:
                print(err)
        discover_tasks.clear()


def cancel_configure_tasks() -> None:
    if configure_tasks:
        for task in configure_tasks:
            try:
                task.cancel()
            except Exception as err:
                print(err)
        configure_tasks.clear()


def apply_filters() -> None:
    global db_filtered
    db_filtered = list(filter(filter_devices, db_full))
    devices_table.clear()
    devices_table.update_rows(db_filtered, clear_selection=True)
    lst_categories.set_options(
        list(set(map(lambda row: row['category'], db_filtered)))
    )
    lst_vendors.set_options(
        list(set(map(lambda row: row['vendor'], db_filtered)))
    )
    lst_models.set_options(
        list(set(map(lambda row: row['model'], db_filtered)))
    )
    change_page()
    update_ui()
    


def filter_devices(device: Dict[str, str]) -> List[Dict[str, str]]:
    result = True
    if lst_categories.value:
        result &= device['category'] == lst_categories.value
    if lst_vendors.value:
        result &= device['vendor'] == lst_vendors.value
    if lst_models.value:
        result &= device['model'] == lst_models.value
    if telnet_switch.value and ssh_switch.value:
        result &= True
    elif telnet_switch.value:
        result &= device['telnet']
    elif ssh_switch.value:
        result &= device['ssh']
    else:
        result &= not device['telnet'] and not device['ssh']
    return result


def reset_filters() -> None:
    for filter in filters_block.descendants():
        filter.set_value('')
        filter.set_value(True)


def show_discover_dialog() -> ui.dialog:
    if btn_discover.icon == 'search':
        with ui.dialog(
            value=True
        ) as discover_dialog, ui.card().props('square'):
            title = ui.label('Обнаружение устройств')
            title.classes(
                '''
                w-full bg-primary text-base text-center
                text-white py-2 absolute left-0 top-0
                '''
            )
            subnet = ui.input(
                label='Подсеть'
            ).classes('w-full mt-10').props(
                'square autofocus outlined clearable'
            )
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
            if dark_mode.value:
                clear_db_switch.classes(remove='bg-gray-100')
    else:
        cancel_discover_tasks()
        devices_table.props(remove='loading')
        status_block.set_visibility(False)
        change_discover_button()
        apply_filters()
        ui.notify(
            message='Обнаружение устройств прекращено',
            position='top',
            type='info'
        )


async def get_subnet(dialog: ui.dialog, subnet: str, clear: bool) -> None:
    global discover_tasks
    if is_ip_subnet(subnet):
        change_discover_button()
        # Если установлен переключатель Очистить БД
        if clear:
            clear_db()
        dialog.close()
        lbl_status.set_text('Обнаружение устройств')
        status_block.set_visibility(True)
        devices_table.props(add='loading')
        hosts = get_hosts_from_subnet(subnet)
        semaphore = asyncio.Semaphore(config.MAX_CONCURRENT)
        discover_tasks = [
            asyncio.create_task(discover_device(host, semaphore))
            for host in hosts
        ]
        await asyncio.gather(*discover_tasks)
        devices_table.props(remove='loading')
        status_block.set_visibility(False)
        change_discover_button()
        apply_filters()
        ui.notify(
            message=f'Обнаружение устройств завершено',
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
        # IP адрес - уникальный идентификатор устройства в базе
        # Получаем список всех адресов в базе для дальнейшей сверки
        hosts = [row['host'] for row in db_full]
        # Добавляется только устройство, которое отсутствует в базе
        if not device['host'] in hosts:
            telnet = telnet_is_enabled(host)
            ssh = ssh_is_enabled(host)
            row = {
                'host': device.get('host', 'Unknown'),
                'sysobjectid': device.get('sysobjectid', 'Unknown'),
                'hostname': device.get('hostname', 'Unknown'),
                'vendor': device.get('vendor', 'Unknown'),
                'model': device.get('model', 'Unknown'),
                'category': device.get('category', 'Unknown'),
                'telnet': telnet,
                'ssh': ssh
            }
            app.storage.general.setdefault('db', []).append(row)
            add_device(row)


def show_configure_dialog() -> ui.dialog:
    if btn_configure.icon == 'tune':
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
                        on_click=lambda: send_commands(
                            configure_dialog, commands.value
                        )
                    ).classes('w-24').props('square unelevated')
                    ui.button(
                        'Отмена',
                        on_click=configure_dialog.close
                    ).classes('w-24').props('square unelevated')
    else:
        cancel_configure_tasks()
        devices_table.props(remove='loading')
        status_block.set_visibility(False)
        change_configure_button()
        devices_table.selected = []
        lbl_total_selected.set_text('0')
        ui.notify(
            message='Передача команд прекращена',
            position='top',
            type='info'
        )


async def send_commands(dialog: ui.dialog, commands: str) -> None:
    global configure_tasks
    if commands:
        dialog.close()
        # Посылаем команды только выбранным устройствам
        ips = [device['host'] for device in devices_table.selected]
        commands_list = [f'{command}\n' for command in commands.split('\n')]
        configure_tasks = [
            Telnet(ip=ip, commands=commands_list).cli_connect() for ip in ips
        ]
        lbl_status.set_text('Идет передача комманд')
        devices_table.props(add='loading')
        status_block.set_visibility(True)
        await asyncio.gather(*configure_tasks)
        status_block.set_visibility(False)
        devices_table.props(remove='loading')
        ui.notify(
            message=f'Передано {len(commands)} команд на {len(ips)} устройств',
            position='top',
            type='positive'
        )
    else:
        ui.notify(
            message='Введите команды для выполнения',
            position='top',
            type='warning'
        )


def change_page():
    global rows_per_page, pages_count, current_page
    devices_count = len(db_filtered)
    if devices_count > 0:
        if rows_per_page > 0:
            pages_count = devices_count // rows_per_page
            if devices_count % rows_per_page != 0:
                pages_count += 1
            if pages_count > 0:
                if current_page == 0:
                    current_page = 1
                elif current_page > pages_count:
                    current_page = pages_count
            else:
                pages_count = 0
                current_page = 0
            devices_table.update_rows(
                db_filtered[
                    (current_page - 1) * rows_per_page
                    :
                    current_page * rows_per_page
                ]
            )
        else:
            devices_table.update_rows(db_filtered)
            pages_count = 1
            current_page = 1
    else:
        pages_count = 0
        current_page = 0
    lbl_active_pages.set_text(f'{current_page} из {pages_count}')


def goto_first_page():
    global current_page
    current_page = 1
    change_page()


def goto_previous_page():
    global current_page
    if current_page > 1:
        current_page -= 1
        change_page()


def goto_next_page():
    global current_page
    if current_page < pages_count:
        current_page += 1
        change_page()


def goto_last_page():
    global current_page
    current_page = pages_count
    change_page()


if __name__ in {'__main__', '__mp_main__'}:
    ui.run(title=config.APP_TITLE, port=8888, reconnect_timeout=60)

    discover_tasks = []
    configure_tasks = []
    ids = {}
    db_full = []
    db_filtered = []
    rows_per_page = app.storage.general.get(
        'rows_per_page',
        config.ROWS_PER_PAGE
    )
    # Если ранее сохранено количество строк на странице, а после
    # внесены изменения в конфиг и соответствующего значения
    # в нем нет, возникнет ошибка. В таком случае делаем
    # активным первый элемент списка и сохраняем изменения
    if not rows_per_page in config.ROWS_COUNT_OPTIONS:
        if config.ROWS_COUNT_OPTIONS:
            rows_per_page = config.ROWS_COUNT_OPTIONS[0]
        else:
            rows_per_page = 0
    pages_count = 0
    current_page = 0
    dark_mode = ui.dark_mode()
    dark_mode.set_value(app.storage.general.get('dark_mode', False))

    try:
        with open(config.SYS_OBJECT_IDS_DB) as file:
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
        ui.label(config.APP_TITLE).classes('text-lg')
        ui.space()
        ui.separator().props('vertical color="blue-11"')
        with ui.button(
            icon='first_page',
            on_click=goto_first_page
        ) as btn_first_page:
            btn_first_page.props('flat square')
            btn_first_page.classes('text-white px-2')
            btn_first_page.tooltip('Первая страница')
        with ui.button(
            icon='chevron_left',
            on_click=goto_previous_page
        ) as btn_prev_page:
            btn_prev_page.props('flat square')
            btn_prev_page.classes('text-white px-2')
            btn_prev_page.tooltip('Предыдущая страница')
        lbl_active_pages = ui.label(f'0 из 0')
        with ui.button(
            icon='chevron_right',
            on_click=goto_next_page
        ) as btn_next_page:
            btn_next_page.props('flat square')
            btn_next_page.classes('text-white px-2')
            btn_next_page.tooltip('Следующая страница')
        with ui.button(
            icon='last_page',
            on_click=goto_last_page
        ) as btn_last_page:
            btn_last_page.props('flat square')
            btn_last_page.classes('text-white px-2')
            btn_last_page.tooltip('Последняя страница')
        ui.separator().props('vertical color="blue-11"')
        rows_per_page_dropdown = ui.select(
            config.ROWS_COUNT_OPTIONS,
            value=rows_per_page,
            on_change=lambda: set_rows_per_page(rows_per_page_dropdown.value) 
        ).props('dense dark borderless options-dark="false"')
        # Наличие значения 0 обязательно в списке так как именно оно
        # дает возможность вывода полного списка устройств
        if not 0 in rows_per_page_dropdown.options:
            rows_per_page_dropdown.options.insert(0, 0)
        rows_per_page_dropdown.tooltip('Устройств на странице')
        ui.separator().props('vertical color="blue-11"')
        with ui.button(
            icon='delete_outline',
            on_click=delete_devices
        ) as btn_delete_rows:
            btn_delete_rows.props('flat square')
            btn_delete_rows.classes('text-white px-2')
            btn_delete_rows.tooltip('Удаление устройств')
        with ui.button(
            icon='clear',
            on_click=clear_db
        ) as btn_clear_db:
            btn_clear_db.props('flat square')
            btn_clear_db.classes('text-white px-2')
            btn_clear_db.tooltip('Очистка БД')
        ui.separator().props('vertical color="blue-11"')
        with ui.button(
            icon='tune',
            on_click=lambda: (
                show_configure_dialog()
                if len(devices_table.selected) > 0
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
            icon='search',
            on_click=show_discover_dialog
        ) as btn_discover:
            btn_discover.props('flat square')
            btn_discover.classes('text-white px-2')
            btn_discover.tooltip('Начать обнаружение')
        ui.separator().props('vertical color="blue-11"')
        with ui.button(
            icon='dark_mode',
            on_click=change_ui_mode
        ) as btn_mode:
            btn_mode.props('flat square')
            btn_mode.classes('text-white px-2')
            btn_mode.tooltip('Темный')
    # Right drawer section
    with ui.right_drawer(
        fixed = True,
        value = True
    ).props('bordered') as filters_drawer:
        with ui.column().classes('w-full') as filters_block:
            lst_categories = ui.select(
                [],
                on_change=apply_filters,
                label='Категория'
            ).classes('w-full').props('outlined dense square clearable')
            lst_vendors = ui.select(
                [],
                on_change=apply_filters,
                label='Производитель'
            ).classes('w-full').props('outlined dense square clearable')
            lst_models = ui.select(
                [],
                on_change=apply_filters,
                label='Модель'
            ).classes('w-full').props('outlined dense square clearable')
            telnet_switch = ui.switch(
                'Включен протокол telnet',
                value=True,
                on_change=apply_filters
            ).classes('w-full pr-3 bg-gray-100')
            ssh_switch = ui.switch(
                'Включен протокол ssh',
                value=True,
                on_change=apply_filters
            ).classes('w-full pr-3 bg-gray-100')
        ui.space()
        with ui.column().classes(
            'w-full items-center'
        ) as status_block:
            status_block.set_visibility(False)
            status_spinner = ui.spinner(type='tail', size='64px')
            lbl_status = ui.label().classes('text-center')
        ui.space()
        ui.button(
            'Сбросить фильтр',
            on_click=reset_filters
        ).classes('w-full').props('square unelevated')
    # Table section
    with ui.table(
        rows=[],
        columns=config.COLUMNS_SETTINGS,
        column_defaults=config.COLUMNS_DEFAULTS,
        row_key='host',
        selection='multiple',
        on_select=lambda: lbl_total_selected.set_text(len(
            devices_table.selected
        ))
    ) as devices_table:
        devices_table.classes('shadow-none border rounded-none w-full')
        devices_table.props('dense hide-selected-banner hide-no-data')
        devices_table.add_slot('body-cell-snmp', '''
            <q-td key="snmp" :props="props">
                <q-badge rounded :color="props.value == 0 ? 'red' : 'green'" />
            </q-td>
        ''')
        devices_table.add_slot('body-cell-telnet', '''
            <q-td key="telnet" :props="props">
                <q-badge rounded :color="props.value == 0 ? 'red' : 'green'" />
            </q-td>
        ''')
        devices_table.add_slot('body-cell-ssh', '''
            <q-td key="ssh" :props="props">
                <q-badge rounded :color="props.value == 0 ? 'red' : 'green'" />
            </q-td>
        ''')
    # Footer section
    with ui.footer().classes('items-center py-2'):
        ui.label('Устройств:')
        lbl_total_devices = ui.label('0')
        ui.separator().props('vertical color="blue-11"')
        ui.label('Категорий:')
        lbl_total_categories = ui.label('0')
        ui.separator().props('vertical color="blue-11"')
        ui.label('Производителей:')
        lbl_total_vendors = ui.label('0')
        ui.separator().props('vertical color="blue-11"')
        ui.label('Моделей:')
        lbl_total_models = ui.label('0')
        ui.separator().props('vertical color="blue-11"')
        ui.label('Выбрано:')
        lbl_total_selected = ui.label('0')
        ui.separator().props('vertical color="blue-11"')
        ui.label('Фильтровано:')
        lbl_total_filtered = ui.label('0')

    set_ui_mode()

    for device in app.storage.general.get('db', []):
        add_device(device)
    apply_filters()
