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


class BrowserWorkerLogger:
    def __init__(self):
        pass

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


class BrowserWorker:
    def __init__(self, num_workers=3, max_retries=5, show_browser=False, proxy_manager=None):
        self.task_queue = asyncio.Queue()
        self.results_queue = asyncio.Queue()  # Changed from list to queue
        self.num_workers = num_workers
        self.workers = []
        self.failed_tasks = []
        self.max_retries = max_retries
        self.retry_counts = {}
        self.logger = BrowserWorkerLogger()
        self.show_browser = show_browser
        self.proxy_manager = proxy_manager
    
    async def _worker(self, worker_id):
        while True:
            task = await self.task_queue.get()

            try:
                self.logger.worker_processing(worker_id, task.id)
                result, used_proxy = await self._run_task(task.handle, task.args)
                await self.results_queue.put(result)  # Put result in queue instead of list
                self.logger.worker_completion(worker_id, task.id)
            except Exception as e:
                self.logger.worker_error(worker_id, task.id, str(e))
                if self.proxy_manager and 'used_proxy' in locals() and used_proxy:
                    proxy_str = used_proxy.get('server', '')
                    if proxy_str:
                        self.proxy_manager.add_to_blacklist(proxy_str)
                        self.logger.adding_proxy_to_blacklist(proxy_str)
                
                retry_count = self.retry_counts.get(task.id, 0)+1
                
                if retry_count <= self.max_retries:
                    self.retry_counts[task.id] = retry_count
                    self.logger.worker_retry(worker_id, task.id, retry_count, self.max_retries)
                    await self.task_queue.put(task)
                else:
                    self.logger.worker_failed(worker_id, task.id, self.max_retries)
                    self.failed_tasks.append((task, str(e)))
            finally:
                self.task_queue.task_done()
    
    async def _add_task(self, task: Task):
        self.logger.create_task(task.id)
        await self.task_queue.put(task)
        return task.id
    
    async def _run_task(self, handle, args):
        proxy = None
        if self.proxy_manager:
            proxy = self.proxy_manager.get_random_proxy()
            
        async with AsyncCamoufox(
            i_know_what_im_doing=True,
            geoip=True,
            os=('windows', 'macos', 'linux'),
            screen=Screen(max_width=1920, max_height=3200),
            humanize=True,
            proxy=proxy,
            block_images=True,
            headless=not self.show_browser,
        ) as browser:
            context = await browser.new_context()
            page = await context.new_page()
            result = await handle(page, *args)
            await context.close()
        return result, proxy
    
    async def start(self):
        self.workers = []
        for i in range(self.num_workers):
            worker_task = asyncio.create_task(self._worker(i+1))
            self.workers.append(worker_task)
    
    async def stop(self):
        for worker in self.workers:
            worker.cancel()
        self.workers = []
    
    async def wait_for_completion(self):
        await self.task_queue.join()
    
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
        while not self.results_queue.empty():
            results.append(await self.results_queue.get())
            self.results_queue.task_done()
        return results
    
    async def get_result(self):
        if self.results_queue.empty():
            return None
        result = await self.results_queue.get()
        return result
    
    def get_failed_tasks(self):
        return self.failed_tasks

    def has_tasks(self):
        return not self.task_queue.empty()





