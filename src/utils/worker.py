import urllib3
from camoufox.async_api import AsyncCamoufox
from browserforge.fingerprints import Screen
import asyncio
import re
from utils.proxy import proxy_manager

# Disable insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class TaskWorker:
    def __init__(self, num_workers=3, max_retries=5):
        self.task_queue = asyncio.Queue()
        self.num_workers = num_workers
        self.workers = []
        self.results = []
        self.failed_tasks = []
        self.max_retries = max_retries
        self.retry_counts = {}  # Track retry counts for each task
    
    async def worker(self, worker_id):
        """Worker process that handles tasks from the queue"""
        while True:
            # Get a task from the queue
            task_item = await self.task_queue.get()
            
            try:
                task_func, args, task_id = task_item
                print(f"Worker {worker_id}: Processing task {task_id}")
                result, used_proxy = await self._run_task(task_func, args)
                self.results.append(result)
                print(f"Worker {worker_id}: Task {task_id} completed")
            except Exception as e:
                print(f"Worker {worker_id}: Error processing task {task_id}: {e}")
                # Add the failed proxy to blacklist if it exists
                if 'used_proxy' in locals() and used_proxy:
                    proxy_str = used_proxy.get('server', '')
                    if proxy_str:
                        print(f"Adding proxy {proxy_str} to blacklist")
                        proxy_manager.add_to_blacklist(proxy_str)
                
                # Track failed task for retry
                retry_count = self.retry_counts.get(task_id, 0) + 1
                self.retry_counts[task_id] = retry_count
                
                if retry_count <= self.max_retries:
                    print(f"Worker {worker_id}: Retrying task {task_id} (attempt {retry_count}/{self.max_retries})")
                    # Put the task back in the queue for retry
                    await self.task_queue.put((task_func, args, task_id))
                else:
                    print(f"Worker {worker_id}: Task {task_id} failed after {self.max_retries} attempts")
                    self.failed_tasks.append((task_func, args, task_id, str(e)))
            finally:
                # Mark the task as done
                self.task_queue.task_done()
    
    async def add_task(self, task_func, args):
        """Add a task to the queue with a unique ID"""
        task_id = f"task_{len(self.retry_counts) + 1}"
        await self.task_queue.put((task_func, args, task_id))
        return task_id
    
    async def _run_task(self, task, args):
        """Execute a single task with a browser instance"""
        # Get a proxy using the proxy manager
        proxy = proxy_manager.get_random_proxy()
            
        async with AsyncCamoufox(
            i_know_what_im_doing=True,
            geoip=True,
            os=('windows', 'macos', 'linux'),
            screen=Screen(max_width=1920, max_height=3200),
            humanize=True,
            proxy=proxy,
            block_images=True
        ) as browser:
            context = await browser.new_context()
            page = await context.new_page()
            result = await task(page, *args)
            await context.close()
        return result, proxy
    
    async def start(self):
        """Start the worker processes"""
        self.workers = []
        for i in range(self.num_workers):
            worker_task = asyncio.create_task(self.worker(i+1))
            self.workers.append(worker_task)
    
    async def stop(self):
        """Stop all worker processes"""
        for worker in self.workers:
            worker.cancel()
        self.workers = []
    
    async def wait_for_completion(self):
        """Wait for all tasks to complete"""
        await self.task_queue.join()
    
    async def run_tasks(self, tasks):
        """Run a list of tasks and wait for completion
        
        Each task should be a tuple of (task_func, args)
        """
        await self.start()
        
        for task_func, args in tasks:
            await self.add_task(task_func, args)
        
        await self.wait_for_completion()
        await self.stop()
        
        return self.results
    
    def get_failed_tasks(self):
        """Get list of tasks that failed after max retries"""
        return self.failed_tasks
    
    async def retry_failed_tasks(self):
        """Retry all failed tasks"""
        if not self.failed_tasks:
            return
        
        print(f"Retrying {len(self.failed_tasks)} failed tasks...")
        tasks_to_retry = self.failed_tasks.copy()
        self.failed_tasks = []
        
        for task_func, args, task_id, _ in tasks_to_retry:
            # Reset retry count for this task
            self.retry_counts[task_id] = 0
            await self.add_task(task_func, args)


# For backward compatibility
async def runTask(task, args):
    worker = TaskWorker(num_workers=1)
    results = await worker.run_tasks([(task, args)])
    return results[0] if results else None


# Example task
async def my_task(page):
    await page.goto('https://example.com')
    title = await page.title()
    # Do something with the page
    return title
