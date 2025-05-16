import telnetlib3
import asyncio
from ndce.net import tcp_port_is_open


class Telnet:
    # Инициализация параметров для соединения 1
    def __init__(
        self,
        ip,
        login: str = 'admin',
        password: str = 'admin',
        commands: list = ""
    ):
        self.username = login
        self.password = password
        self.ip = ip
        self.commands = commands

    # Передаче комманд на выполнение в свитч
    async def shell(self, reader, writer) -> None:
        try:
            outp = await reader.read(1024)
            if outp:
                print(
                    f'Соединение установлено к IP-адресу: {self.ip}...')

                writer.write(self.username + '\n')
                await asyncio.sleep(0.5)
                writer.write(self.password + '\n')
                await asyncio.sleep(0.5)
                for command in self.commands:
                    writer.write(command)
                    await asyncio.sleep(1)
                await asyncio.sleep(0.5)
                print(await reader.read(1024))
        except ConnectionResetError:
            print(f'Сброс соединения: {self.ip}...')
    
    # Настройки и подвключение по telnet
    async def cli_connect(self) -> None:
        print(f'Подключения к IP-адресу : {self.ip}...')
        if tcp_port_is_open(self.ip, 23):
            reader, writer = await telnetlib3.open_connection(
                self.ip, 23,  shell=self.shell
            )
            await writer.protocol.waiter_closed
        else:
            print(f'Соединение не установлено к IP-адресу : {self.ip}...')