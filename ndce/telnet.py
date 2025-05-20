import telnetlib3
import asyncio
from ndce.net import telnet_is_enabled
from config import USERNAME, PASSWORD


class Telnet:
    # Инициализация параметров для соединения 1
    def __init__(
        self,
        ip,
        username: str = USERNAME,
        password: str = PASSWORD,
        commands: list = []
    ):
        self.ip = ip
        self.username = username
        self.password = password
        self.commands = commands

    # Передаче комманд на выполнение в свитч
    async def shell(self, reader, writer) -> None:
        try:
            output = await reader.read(1024)
            if output:
                print(f'Соединение установлено к IP-адресу: {self.ip}')
                writer.write(self.username + '\n')
                await asyncio.sleep(0.5)
                writer.write(self.password + '\n')
                await asyncio.sleep(0.5)
                for command in self.commands:
                    writer.write(command)
                    await asyncio.sleep(0.5)
                    print(await reader.read(1024))
                await asyncio.sleep(0.5)
                print(await reader.read(1024))
        except Exception as err:
            print(f'Сброс соединения: {self.ip}')
            print(err)
    
    # Настройки и подвключение по telnet
    async def cli_connect(self) -> None:
        print(f'Подключение к IP-адресу : {self.ip}')
        if telnet_is_enabled(self.ip):
            try:
                reader, writer = await telnetlib3.open_connection(
                    host=self.ip, shell=self.shell
                )
                await writer.protocol.waiter_closed
            except Exception as err:
                print(err)
        else:
            print(f'Соединение не установлено к IP-адресу: {self.ip}')