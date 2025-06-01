import asyncio
import telnetlib3
from ndce.net import telnet_is_enabled
from config import USERNAME, PASSWORD


class Telnet:
    def __init__(
        self,
        ip,
        username = USERNAME,
        password = PASSWORD,
        commands = []
    ):
        self.ip = ip
        self.username = username
        self.password = password
        self.commands = commands

    async def shell(self, reader, writer):
        try:
            output = await reader.read(1024)
            if output:
                print(f'Соединение с {self.ip} установлено')
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
            print(f'Ошибка соединения с {self.ip}')
            print(err)
    
    async def cli_connect(self):
        print(f'Соединение с {self.ip}')
        if telnet_is_enabled(self.ip):
            try:
                reader, writer = await telnetlib3.open_connection(
                    host=self.ip, shell=self.shell
                )
                await writer.protocol.waiter_closed
            except Exception as err:
                print(f'Ошибка соединения с {self.ip}')
                print(err)
        else:
            print(f'Проверьте настройки telnet на {self.ip}')