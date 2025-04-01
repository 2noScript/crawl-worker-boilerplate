from utils.helper import read_file_lines
from utils.network import AsyncHttpClient
from models import Proxy
import random
from typing import List, Set  
import json



class FreeProxy:
    _suppliers = {
        "proxy_scrape":"https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&proxy_format=protocolipport&format=json&timeout=500",
        "proxy_geonode":"https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&sort_by=lastChecked&sort_type=desc"
    }
    def __init__(self):
        self._client = AsyncHttpClient()

    async def get_proxyscrape(self)->List[Proxy]:
        url=self._suppliers["proxy_scrape"]
        data,status=await self._client.get(url=self._suppliers["proxy_scrape"])
        results=[]
        if status==200:
            json_data=json.loads(data)
            for item in json_data["proxies"]:
                if not item["alive"]:
                    continue
                proxy=Proxy(
                    ip=item["ip"],
                    port=item["port"],
                    protocol=[item["protocol"]],
                    responseTime=item["timeout"],
                    countryCode=item["ip_data"]["countryCode"])
                results.append(proxy)
        return results
        

    async def get_geonode(self)->List[Proxy]:
        data,status=await self._client.get(url=self._suppliers["proxy_geonode"])
        if status==200:
            json_data=json.loads(data)
            results=[]
            for item in json_data["data"]:
                if item["responseTime"]>500:
                    continue
                proxy=Proxy(
                    ip=item["ip"],
                    port=item["port"],
                    protocol=item["protocols"],
                    responseTime=item["responseTime"],
                    countryCode=item["country"])
                results.append(proxy)
        return results
    
    async def get_proxies(self)->List[Proxy]:
        try:
            proxyscrape=await self.get_proxyscrape()
            # geonode=await self.get_geonode()
            return proxyscrape
        finally:
            await self._client.close()
    



class ProxyManager:
    def __init__(self, free_proxy:FreeProxy=None):
        if free_proxy:
            self.free_proxy = free_proxy
        else:
            self.free_proxy = FreeProxy()
            
        self.proxy_list: List[Proxy] = []
        self.whitelist = set()
        self.blacklist= set()
    
    def _get_available_proxies(self):
        if self.whitelist:
            print("Using whitelist")
            return list(self.whitelist)
        available_proxies = []
        for proxy in self.proxy_list:
            if not any(proxy.ip == black_proxy.ip and proxy.port == black_proxy.port 
                      for black_proxy in self.blacklist):
                available_proxies.append(proxy)
        return available_proxies


    async def get_random_proxy(self):
        if not self.proxy_list:
            self.proxy_list=await self.free_proxy.get_proxies()
        if len(self.blacklist) >= len(self.proxy_list):
            print("All proxies are blacklisted. Clearing blacklist.")
            self.blacklist.clear()
            self.whitelist.clear()
        
        available_proxies = self._get_available_proxies()
        print(f"Available proxies: {len(available_proxies)}")

        try:    
            return random.choice(available_proxies)

        except Exception as e:
            print(f"Error creating proxy configuration: {e}")
            self.add_to_blacklist(proxy)
    
    def add_to_blacklist(self, proxy):
        self.blacklist.add(proxy)
        self.whitelist.discard(proxy)

    def add_to_whitelist(self, proxy):
        self.whitelist.add(proxy)

    
    def get_proxy_count(self):
        return len(self.proxy_list)
    
    async def reload_proxies(self):
        self.proxy_list = await self.free_proxy.get_proxies()
        

proxy_manager = ProxyManager()



