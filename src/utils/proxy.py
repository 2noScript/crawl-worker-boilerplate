from .helper import read_file_lines
import random

class ProxyManager:
    def __init__(self, proxy_file="proxy.txt"):
        self.proxy_file = proxy_file
        self.proxy_list = read_file_lines(proxy_file)
        self.blacklist = set()
    
    def get_random_proxy(self):
        """
        Returns a random proxy from the proxy list.
        
        Returns:
            dict: A proxy configuration dictionary or None if no proxies are available
        """
        if not self.proxy_list:
            return None
        
        # Check if all proxies are blacklisted
        if len(self.blacklist) >= len(self.proxy_list):
            print("All proxies are blacklisted. Clearing blacklist.")
            self.blacklist.clear()
        
        # Try to find a non-blacklisted proxy
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
        """
        Add a proxy to the blacklist
        
        Args:
            proxy: Either a proxy dict or a proxy server string
        """
        if isinstance(proxy, dict) and 'server' in proxy:
            self.blacklist.add(proxy['server'])
        elif isinstance(proxy, str):
            self.blacklist.add(proxy)
    
    def get_proxy_count(self):
        """
        Returns the number of proxies in the proxy list.

        Returns:
            int: The number of proxies
        """
        return len(self.proxy_list)
    
    def reload_proxies(self):
        """Reload proxies from the file"""
        self.proxy_list = read_file_lines(self.proxy_file)
        

# Create a global instance for backward compatibility
proxy_manager = ProxyManager()

# For backward compatibility
def get_random_proxy():
    return proxy_manager.get_random_proxy()

def get_proxy_count():
    return proxy_manager.get_proxy_count()

