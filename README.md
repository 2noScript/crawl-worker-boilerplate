# Crawler Worker Boilerplate

A flexible and robust web crawling framework using AsyncCamoufox for browser automation with proxy support, retry mechanisms, and parallel task processing.

## Features

- Asynchronous task processing with multiple workers
- Automatic proxy rotation and blacklisting
- Configurable retry mechanism for failed tasks
- Browser fingerprinting and humanization
- Headless/visible browser mode support
- Automatic detection and handling of proxy connection errors

## Installation

1. Clone repository:
```bash
git clone https://github.com/yourusername/crawl-worker-boilerplate.git
cd crawl-worker-boilerplate
```
2. Install dependencies:

```bash 
pip install -r requirements.txt
```

3. Example Usage
```python
# /Users/2noscript/workspace/boilerplate/crawl-worker-boilerplate/src/multi_page_crawl.py
import asyncio
import uuid
from utils.worker import BrowserWorker
from utils.proxy import ProxyManager
from models import Task

async def crawl_page(page, url, depth=0, max_depth=2):
    if depth > max_depth:
        return {"url": url, "links": [], "depth": depth}
    
    await page.goto(url, wait_until="networkidle")
    
    title = await page.title()
    
    links = await page.evaluate('''() => {
        return Array.from(document.querySelectorAll('a')).map(a => a.href)
            .filter(href => href.startsWith('http'));
    }''')
    
    unique_links = list(set(links))[:5] 
    
    return {
        "url": url,
        "title": title,
        "links": unique_links,
        "depth": depth
    }

async def main():
    proxy_manager = ProxyManager()
    
    worker = BrowserWorker(
        num_workers=5,
        max_retries=3,
        show_browser=False,
        proxy_manager=proxy_manager
    )
    
    start_urls = ["https://example.com", "https://wikipedia.org"]
    
    initial_tasks = [
        Task(id=f"task_{uuid.uuid4()}", handle=crawl_page, args=[url, 0, 2])
        for url in start_urls
    ]
    
    await worker.run_tasks(initial_tasks)
    
    results = await worker.get_results()
    
    next_level_tasks = []
    for result in results:
        for link in result.get("links", []):
            next_level_tasks.append(
                Task(
                    id=f"task_{uuid.uuid4()}", 
                    handle=crawl_page, 
                    args=(link, result["depth"] + 1, 2)
                )
            )
    
    if next_level_tasks:
        await worker.run_tasks(next_level_tasks)
        
        next_results = await worker.get_results()
        results.extend(next_results)
    
    for result in results:
        print(f"URL: {result['url']}")
        print(f"Title: {result.get('title', 'N/A')}")
        print(f"Depth: {result['depth']}")
        print(f"Found {len(result.get('links', []))} links")
        print("-" * 50)
    
    failed_tasks = worker.get_failed_tasks()
    if failed_tasks:
        print(f"Có {len(failed_tasks)} tác vụ thất bại")

if __name__ == "__main__":
    asyncio.run(main())

```


4. Demo

https://github.com/user-attachments/assets/f00596b0-1900-4efe-baa5-12256b068d50

