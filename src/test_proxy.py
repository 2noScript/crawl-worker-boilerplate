import asyncio
from utils.proxy import FreeProxy

async def main():
    proxy = FreeProxy()
    proxy_str = await proxy.get_proxies()
    print(len(proxy_str))

asyncio.run(main())