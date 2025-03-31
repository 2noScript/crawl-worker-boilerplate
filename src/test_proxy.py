import asyncio
from utils.proxy import FreeProxy, ProxyManager

proxy_manager = ProxyManager()

async def main():
    proxy_str = await proxy_manager.get_random_proxy()
    print(proxy_str)

asyncio.run(main())