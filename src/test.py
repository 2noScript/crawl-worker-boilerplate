import asyncio
from utils.worker import BrowserWorker
from utils.proxy  import ProxyManager
from models import Task



urls = [
    "https://browserleaks.com/ip"
]

async def task_handle(page, link):
    await page.goto(link, wait_until="domcontentloaded")
    await page.wait_for_timeout(60000)  # Wait for 1 second to let the page load
    return []

async def main():
    # Create a worker with 3 parallel processes
    proxy_manager = ProxyManager()
    worker = BrowserWorker(num_workers=20, show_browser=True,proxy_manager=proxy_manager)
    tasks=[]
    for url in urls:
        tasks.append(Task(handle=task_handle,args=[url]))
    await worker.run_tasks(tasks)
    res =await worker.get_results()
    print(res) 

if __name__ == "__main__":
    asyncio.run(main())