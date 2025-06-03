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


def set_ui_defaults() -> None:
    """
    Функция устанавливает значения по-умолчанию
    для пользовательского интерфейса
    """
    ui.card.default_props('square')
    ui.input.default_classes('w-full mt-10')
    ui.input.default_props('square autofocus outlined clearable')
    ui.switch.default_classes('w-full pr-3 bg-gray-100')
    ui.row.default_classes('w-full justify-between')
    ui.button.default_classes('text-white px-2')
    ui.button.default_props('square unelevated')
    ui.header.default_classes('items-center py-2')
    ui.separator.default_props('vertical color="blue-11"')
    ui.select.default_props('dense square')
    ui.right_drawer.default_props('bordered')
    ui.column.default_classes('w-full')
    ui.table.default_classes('shadow-none border rounded-none w-full')
    ui.table.default_props('dense hide-selected-banner hide-no-data')
    ui.footer.default_classes('items-center py-2')
    ui.textarea.default_classes('w-full mt-10')
    ui.textarea.default_props(
        '''
        square autofocus standout autogrow
        outlined input-class=max-h-64
        '''
    )


def change_tooltip(element: ui.element, text: str) -> None:
    """
    Функция меняет текст всплывающей подсказки у заданного элемента
    """
    for child in element:
        if isinstance(child, ui.tooltip):
            element.remove(child)
    element.tooltip(text)


def set_ui_mode() -> None:
    """
    Функция устанавливает режим интерфейса: темный или светлый
    """
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
    """
    Функция меняет режим интерфейса: с темного на светлый и обратно
    """
    if dark_mode.value:
        dark_mode.disable()
    else:
        dark_mode.enable()
    app.storage.general['dark_mode'] = dark_mode.value
    set_ui_mode()
    

def add_device(device: Dict[str, str]) -> None:
    """
    Функция добавляет заданное устройство
    """
    db_full.append(device)
    devices_table.add_row(device)
    apply_filters()
    update_ui()


def update_ui() -> None:
    """
    Функция обновляет пользовательский интерфейс
    """
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
    """
    Функция очищает базу данных
    """
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
    """
    Функция удаляет устройства, выбранные в таблице
    """
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
    """
    Функция устанавливаем и сохраняет значение количества строк на странице
    """
    global rows_per_page
    app.storage.general['rows_per_page'] = value
    rows_per_page = value
    devices_table.selected = []
    lbl_total_selected.set_text('0')
    apply_filters()


def change_discover_button() -> None:
    """
    Функция меняет иконку и всплывающую подсказку для кнопки обнаружения
    """
    if btn_discover.icon == 'search':
        btn_discover.set_icon('stop')
        change_tooltip(btn_discover, 'Остановить обнаружение')
    else:
        btn_discover.set_icon('search')
        change_tooltip(btn_discover, 'Обнаружение')


def change_configure_button() -> None:
    """
    Функция меняет иконку и всплывающую подсказку для кнопки конфигурирования
    """
    if btn_configure.icon == 'tune':
        btn_configure.set_icon('stop')
        change_tooltip(btn_configure, 'Остановить передачу команд')
    else:
        btn_configure.set_icon('tune')
        change_tooltip(btn_configure, 'Передача команд')


def cancel_discover_tasks() -> None:
    """
    Функция отменяет задачи обнаружения устройств
    """
    if discover_tasks:
        for task in discover_tasks:
            try:
                task.cancel()
            except Exception as err:
                print(err)
        discover_tasks.clear()


def cancel_configure_tasks() -> None:
    """
    Функция отменяет задачи передачи команд устройствам
    """
    if configure_tasks:
        for task in configure_tasks:
            try:
                task.cancel()
            except Exception as err:
                print(err)
        configure_tasks.clear()


def apply_filters() -> None:
    """
    Функция применяет правила фильтрации
    """
    global db_filtered
    db_filtered = list(filter(filter_devices, db_full))
    devices_table.clear()
    devices_table.update_rows(db_filtered, clear_selection=True)
    lst_categories.set_options(
        sorted(list(set(map(lambda row: row['category'], db_filtered))))
    )
    lst_vendors.set_options(
        sorted(list(set(map(lambda row: row['vendor'], db_filtered))))
    )
    lst_models.set_options(
        sorted(list(set(map(lambda row: row['model'], db_filtered))))
    )
    change_page()
    update_ui()
    


def filter_devices(device: Dict[str, str]) -> bool:
    """
    Функция определяет, соответствует ли устройство заданному фильтру
    """
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
    """
    Функция сбрасывает все фильтры
    """
    for filter in filters_block.descendants():
        filter.set_value('')
        filter.set_value(True)


def save_clear_status(value: bool) -> None:
    """
    Функция сохраняет состояние кнопки очистки базы
    """
    app.storage.general['clear'] = value


def show_discover_dialog() -> ui.dialog:
    """
    Функция отображает окно обнаружения устройств
    """
    ui.button.default_classes('w-24')
    ui.label.default_classes(
        '''
        w-full bg-primary text-base text-center
        text-white py-2 absolute left-0 top-0
        '''
    )
    if btn_discover.icon == 'search':
        with ui.dialog(
            value=True
        ) as discover_dialog, ui.card():
            ui.label('Обнаружение устройств')
            subnet = ui.input(label='Подсеть')
            clear_db_switch = ui.switch(
                'Очистить базу данных',
                value=app.storage.general.get('clear', False),
                on_change=lambda: save_clear_status(clear_db_switch.value)
            )
            with ui.row():
                ui.button(
                    'Начать',
                    on_click=lambda: get_subnet(
                        discover_dialog,
                        subnet.value,
                        clear_db_switch.value
                    )
                )
                ui.button(
                    'Отмена',
                    on_click=discover_dialog.close
                )
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
    """
    Функция запускает процесс обнаружения устройств
    """
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
    """
    Функция получает данные по заданному устройству
    """
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
    """
    Функция отображает окно передачи команд устройствам
    """
    ui.button.default_classes('w-24')
    ui.label.default_classes(
        '''
        w-full bg-primary text-base text-center
        text-white py-2 absolute left-0 top-0
        '''
    )
    ui.card.default_classes('w-full max-h-96')
    if btn_configure.icon == 'tune':
        with ui.dialog(value=True)as configure_dialog:
            with ui.card():
                ui.label('Конфигурирование устройств')
                commands = ui.textarea(
                    label='Список команд',
                    placeholder='Вводите по одной команде на строку'
                )
                with ui.row():
                    ui.button(
                        'Начать',
                        on_click=lambda: send_commands(
                            configure_dialog, commands.value
                        )
                    )
                    ui.button(
                        'Отмена',
                        on_click=configure_dialog.close
                    )
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
    """
    Функция передает заданные команды выбранным устройствам
    """
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


def change_page() -> None:
    """
    Функция осуществляет переход к странице
    """
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


def goto_first_page() -> None:
    """
    Функция осуществляет переход к первой странице
    """
    global current_page
    current_page = 1
    change_page()


def goto_previous_page() -> None:
    """
    Функция осуществляет переход к предыдущей странице
    """
    global current_page
    if current_page > 1:
        current_page -= 1
        change_page()


def goto_next_page() -> None:
    """
    Функция осуществляет переход к следующей странице
    """
    global current_page
    if current_page < pages_count:
        current_page += 1
        change_page()


def goto_last_page() -> None:
    """
    Функция осуществляет переход к последней странице
    """
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
    
    set_ui_defaults()

    # GUI RENDERING
    # Header section
    with ui.header():
        ui.label(config.APP_TITLE).classes('text-lg')
        ui.space()
        ui.separator()
        ui.button(
            icon='first_page',
            on_click=goto_first_page
        ).tooltip('Первая страница')
        ui.button(
            icon='chevron_left',
            on_click=goto_previous_page
        ).tooltip('Предыдущая страница')
        lbl_active_pages = ui.label(f'0 из 0')
        ui.button(
            icon='chevron_right',
            on_click=goto_next_page
        ).tooltip('Следующая страница')
        ui.button(
            icon='last_page',
            on_click=goto_last_page
        ).tooltip('Последняя страница')
        ui.separator()
        rows_per_page_dropdown = ui.select(
            config.ROWS_COUNT_OPTIONS,
            value=rows_per_page,
            on_change=lambda: set_rows_per_page(rows_per_page_dropdown.value) 
        ).props(
            add='dark borderless options-dark="false"',
            remove='outlined'
        ).tooltip('Устройств на странице')
        # Наличие значения 0 обязательно в списке так как именно оно
        # дает возможность вывода полного списка устройств
        if not 0 in rows_per_page_dropdown.options:
            rows_per_page_dropdown.options.insert(0, 0)
        ui.separator()
        ui.button(
            icon='delete_outline',
            on_click=delete_devices
        ).tooltip('Удаление устройств')
        ui.button(icon='clear', on_click=clear_db).tooltip('Очистка БД')
        ui.separator()
        btn_configure = ui.button(
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
        ).tooltip('Конфигурирование')
        btn_discover = ui.button(
            icon='search',
            on_click=show_discover_dialog
        ).tooltip('Начать обнаружение')
        ui.separator()
        btn_mode = ui.button(
            icon='dark_mode',
            on_click=change_ui_mode
        ).tooltip('Темный')
    # Right drawer section
    with ui.right_drawer(fixed = True, value = True) as filters_drawer:
        ui.column.default_classes('items-center')
        ui.button.default_classes('w-full')
        ui.label.default_classes('text-center')
        ui.select.default_classes('w-full')
        with ui.column()as filters_block:
            lst_categories = ui.select(
                [],
                on_change=apply_filters,
                label='Категория'
            ).props('clearable')
            lst_vendors = ui.select(
                [],
                on_change=apply_filters,
                label='Производитель'
            ).props('clearable')
            lst_models = ui.select(
                [],
                on_change=apply_filters,
                label='Модель'
            ).props('clearable')
            telnet_switch = ui.switch(
                'Включен протокол telnet',
                value=True,
                on_change=apply_filters
            )
            ssh_switch = ui.switch(
                'Включен протокол ssh',
                value=True,
                on_change=apply_filters
            )
        ui.space()
        with ui.column() as status_block:
            status_block.set_visibility(False)
            status_spinner = ui.spinner(type='tail', size='64px')
            lbl_status = ui.label()
        ui.space()
        ui.button('Сбросить фильтр', on_click=reset_filters)
    # Table section
    with ui.table(
        rows=[],
        columns=config.COLUMNS_SETTINGS,
        column_defaults=config.COLUMNS_DEFAULTS,
        row_key='host',
        selection='multiple',
        on_select=lambda: lbl_total_selected.set_text(
            len(devices_table.selected)
        )
    ) as devices_table:
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
    with ui.footer():
        ui.label('Устройств:')
        lbl_total_devices = ui.label('0')
        ui.separator()
        ui.label('Категорий:')
        lbl_total_categories = ui.label('0')
        ui.separator()
        ui.label('Производителей:')
        lbl_total_vendors = ui.label('0')
        ui.separator()
        ui.label('Моделей:')
        lbl_total_models = ui.label('0')
        ui.separator()
        ui.label('Выбрано:')
        lbl_total_selected = ui.label('0')
        ui.separator()
        ui.label('Фильтровано:')
        lbl_total_filtered = ui.label('0')
    
    set_ui_mode()
    
    for device in app.storage.general.get('db', []):
        add_device(device)

    apply_filters()
