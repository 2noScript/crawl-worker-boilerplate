import aiohttp

class AsyncHttpClient:
    def __init__(self, base_url=None, timeout=30):
        self.base_url = base_url.rstrip("/") if base_url else None
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session = None

    async def _request(self, method, url, **kwargs):
        if self.session is None:
            self.session = aiohttp.ClientSession(timeout=self.timeout)

        try:
            full_url = f"{self.base_url}{url}" if self.base_url else url
            async with self.session.request(method, full_url, **kwargs) as response:
                data = await response.text()
                status = response.status
                return data, status
        finally:
            await self.close()

    async def get(self, url, params=None, headers=None):
        return await self._request("GET", url, params=params, headers=headers)

    async def post(self, url, data=None, json=None, headers=None):
        return await self._request("POST", url, data=data, json=json, headers=headers)

    async def put(self, url, data=None, json=None, headers=None):
        return await self._request("PUT", url, data=data, json=json, headers=headers)

    async def delete(self, url, headers=None):
        return await self._request("DELETE", url, headers=headers)

    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None