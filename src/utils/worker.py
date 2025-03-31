import urllib3
from camoufox.async_api import AsyncCamoufox
from browserforge.fingerprints import Screen
import asyncio
import re
from utils.proxy import ProxyManager
from models import Task
from typing import List

# Disable insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class _BrowserWorkerLogger:
    
    def worker_processing(self, worker_id, task_id):
        print(f"Worker {worker_id} processing task {task_id}")
        
    def worker_completion(self, worker_id, task_id):
        print(f"Worker {worker_id} completed task {task_id}")
        
    def worker_error(self, worker_id, task_id, error):
        print(f"Worker {worker_id} encountered an error processing task {task_id}: {error}")
        
    def adding_proxy_to_blacklist(self, proxy_str):
        print(f"Adding proxy {proxy_str} to blacklist")
        
    def worker_retry(self, worker_id, task_id, retry_count, max_retries):
        print(f"Worker {worker_id} retrying task {task_id} (attempt {retry_count}/{max_retries})")
        
    def worker_failed(self, worker_id, task_id, max_retries):
        print(f"Worker {worker_id}: Task {task_id} failed after {max_retries} attempts")
        
    def create_task(self, task_id):
        print(f"Created task with id: {task_id}")

    def worker_proxy_not_connected(self, proxy_str):
        print(f"Worker proxy not connected: {proxy_str}")


class BrowserWorker:
    def __init__(self, num_workers=3, max_retries=5, show_browser=False, proxy_manager=None):
        self._tasks = asyncio.Queue()
        self._results = asyncio.Queue()  # Changed from list to queue
        self._num_workers = num_workers
        self._workers = []
        self._failed_tasks = []
        self._max_retries = max_retries
        self._retry_counts = {}
        self._logger = _BrowserWorkerLogger()
        self._show_browser = show_browser
        self._proxy_manager = proxy_manager
    
    async def _worker(self, worker_id):
        while True:
            task = await self._tasks.get()

            try:
                self._logger.worker_processing(worker_id, task.id)
                result, used_proxy = await self._run_task(task.handle, task.args)
                await self._results.put(result)  # Put result in queue instead of list
                self._logger.worker_completion(worker_id, task.id)
            except Exception as e:
                self._logger.worker_error(worker_id, task.id, str(e))
                if self._proxy_manager and 'used_proxy' in locals() and used_proxy:
                    proxy_str = used_proxy.get('server', '')
                    if proxy_str:
                        self._proxy_manager.add_to_blacklist(proxy_str)
                        self._logger.adding_proxy_to_blacklist(proxy_str)
                
                retry_count = self._retry_counts.get(task.id, 0)+1
                
                if retry_count <= self._max_retries:
                    self._retry_counts[task.id] = retry_count
                    self._logger.worker_retry(worker_id, task.id, retry_count, self._max_retries)
                    await self._tasks.put(task)
                else:
                    self._logger.worker_failed(worker_id, task.id, self._max_retries)
                    self._failed_tasks.append((task, str(e)))
            finally:
                self._tasks.task_done()
    
    async def _add_task(self, task: Task):
        self._logger.create_task(task.id)
        await self._tasks.put(task)
        return task.id
    
    async def _run_task(self, handle, args):
        proxy = None
        if self._proxy_manager:
            proxy = await self._proxy_manager.get_random_proxy()
            print(f"Using proxy: {proxy}")
            
        try:
            async with AsyncCamoufox(
                i_know_what_im_doing=True,
                geoip=True,
                os=('windows', 'macos', 'linux'),
                screen=Screen(max_width=1920, max_height=3200),
                humanize=True,
                proxy=proxy,
                block_images=True,
                headless=not self._show_browser,
            ) as browser:
                context = await browser.new_context()
                page = await context.new_page()
                result = await handle(page, *args)
                await context.close()
            return result, proxy
        except Exception as e:
            # If there's a proxy connection error, add it to blacklist
            if proxy and self._proxy_manager and any(err in str(e).lower() for err in [
                'failed to connect to proxy', 
                'proxy connection failed',
                'connection refused',
                'timeout',
                'connection error'
            ]):
                proxy_str = proxy.get('server', '')
                if proxy_str:
                    self._logger.worker_proxy_not_connected(proxy_str)
                    self._logger.adding_proxy_to_blacklist(proxy_str)
                    self._proxy_manager.add_to_blacklist(proxy_str)

            # Re-raise the exception to be handled by the caller
            raise
    
    async def start(self):
        self._workers = []
        for i in range(self._num_workers):
            worker_task = asyncio.create_task(self._worker(i+1))
            self._workers.append(worker_task)
    
    async def stop(self):
        for worker in self._workers:
            worker.cancel()
        self._workers = []
    
    async def wait_for_completion(self):
        await self._tasks.join()
    
    async def run_tasks(self, tasks: List[Task],wait_for_completion_additional=None):
        await self.start()

        for task in tasks:
            await self._add_task(task)

        await self.wait_for_completion()
        if wait_for_completion_additional:
            await wait_for_completion_additional()
        
        await self.stop()

    
    async def get_results(self):
        results = []
        while not self._results.empty():
            results.append(await self._results.get())
            self._results.task_done()
        return results
    
    async def get_result(self):
        if self._results.empty():
            return None
        result = await self._results.get()
        return result
    
    def get_failed_tasks(self):
        return self._failed_tasks

    def has_tasks(self):
        return not self._tasks.empty()





