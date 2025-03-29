from .helper import read_file_lines
import random

class ProxyManager:
    def __init__(self, proxy_file="proxy.txt"):
        self.proxy_file = proxy_file
        self.proxy_list = read_file_lines(proxy_file)
        self.blacklist = set()
    
    def get_random_proxy(self):
        if not self.proxy_list:
            return None
        if len(self.blacklist) >= len(self.proxy_list):
            print("All proxies are blacklisted. Clearing blacklist.")
            self.blacklist.clear()
        
        available_proxies = [p for p in self.proxy_list if p not in self.blacklist]
        if not available_proxies:
            self.reload_proxies()
            return self.get_random_proxy()
            
        proxy_str = random.choice(available_proxies)
        
        # Assuming proxy format is "server:port:username:password"
        try:
            parts = proxy_str.strip().split(':')
            if len(parts) == 4:
                server, port, username, password = parts
                return {
                    "server": f"http://{server}:{port}",
                    "username": username,
                    "password": password
                }
            elif len(parts) == 2:
                # If only server:port format
                server, port = parts
                return {
                    "server": f"http://{server}:{port}"
                }
            else:
                print(f"Invalid proxy format: {proxy_str}")
                return None
        except Exception as e:
            print(f"Error parsing proxy: {e}")
            return None
    
    def add_to_blacklist(self, proxy):

        if isinstance(proxy, dict) and 'server' in proxy:
            self.blacklist.add(proxy['server'])
        elif isinstance(proxy, str):
            self.blacklist.add(proxy)
    
    def get_proxy_count(self):
        return len(self.proxy_list)
    
    def reload_proxies(self):
        self.proxy_list = read_file_lines(self.proxy_file)
        

proxy_manager = ProxyManager()



