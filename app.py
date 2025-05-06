import asyncio
import pprint
from ndce.net import get_hosts_from_subnet
from ndce.icmp import get_accesable_hosts


async def main():
    a = await get_accesable_hosts(
            get_hosts_from_subnet('10.10.4.0/24')
        )
    print(a)


if __name__ == '__main__':
    asyncio.run(main())
