import asyncio
from typing import List, Any, Optional

class Store:
    def __init__(self):
        self.task_queue = asyncio.Queue()
        self.result_queue = asyncio.Queue()
        
    async def add_task(self, task):
        await self.task_queue.put(task)
        
    async def get_task(self) -> Optional[Any]:
        if self.task_queue.empty():
            return None
        return await self.task_queue.get()
        
    async def get_tasks(self) -> List[Any]:
        tasks = []
        while not self.task_queue.empty():
            task = await self.task_queue.get()
            tasks.append(task)
        return tasks
        
    async def add_result(self, result):
        await self.result_queue.put(result)
        
    async def get_results(self) -> List[Any]:
        results = []
        while not self.result_queue.empty():
            results.append(await self.result_queue.get())
        return results
    
    async def get_result(self) -> Optional[Any]:
        if self.result_queue.empty():
            return None
        result = await self.result_queue.get()
        return result
    
    def has_tasks(self) -> bool:
        return not self.task_queue.empty()
    
    def has_results(self) -> bool:
        return not self.result_queue.empty()
    
    def task_done(self):
        self.task_queue.task_done()
        
    async def wait_for_completion(self):
        await self.task_queue.join()
    
    async def wait_for_clean(self):
        while not self.task_queue.empty() or not self.result_queue.empty():
            await asyncio.sleep(2)
    def is_clean(self):
        return self.task_queue.empty() and self.result_queue.empty()
  
# Create a global store instance
task_store = Store()






