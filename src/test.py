import asyncio
from utils.worker import TaskWorker
from utils.handle import bypass_check, get_gtin13


urls = [
    "https://www.walmart.com/ip/Care-Bears-Cheer-Bear-T-Shirt/335240193",
    "https://www.walmart.com/ip/Care-Bears-Cheer-Bear-T-Shirt/335240193",
    "https://www.walmart.com/ip/Care-Bears-Cheer-Bear-T-Shirt/335240193",
    "https://www.walmart.com/ip/Care-Bears-Cheer-Bear-T-Shirt/335240193",
    "https://www.walmart.com/ip/Care-Bears-Cheer-Bear-T-Shirt/335240193",
    "https://www.walmart.com/ip/Care-Bears-Cheer-Bear-T-Shirt/335240193",
    "https://www.walmart.com/ip/Care-Bears-Cheer-Bear-T-Shirt/335240193",
    "https://www.walmart.com/ip/Care-Bears-Cheer-Bear-T-Shirt/335240193",
    "https://www.walmart.com/ip/Care-Bears-Cheer-Bear-T-Shirt/335240193",
    "https://www.walmart.com/ip/Care-Bears-Cheer-Bear-T-Shirt/335240193",
    "https://www.walmart.com/ip/335240193",
    "https://www.walmart.com/ip/335240193"
    "https://www.walmart.com/ip/335240193",
    "https://www.walmart.com/ip/Care-Bears-Cheer-Bear-T-Shirt/335240193",
    "https://www.walmart.com/ip/Care-Bears-Cheer-Bear-T-Shirt/335240193",
    "https://www.walmart.com/ip/Care-Bears-Cheer-Bear-T-Shirt/335240193",
    "https://www.walmart.com/ip/335240193",
    "https://www.walmart.com/ip/335240193"
    "https://www.walmart.com/ip/335240193"
    
]

async def task(page, link):
    # Your task logic here
    await page.goto(link, wait_until="domcontentloaded")
    await bypass_check(page)
    gtin13 = await get_gtin13(page)
    return gtin13

async def main():
    # Create a worker with 3 parallel processes
    worker = TaskWorker(num_workers=4)

    # Start the workers
    await worker.start()

    for url in urls:
        await worker.add_task(task, [url])

    await worker.wait_for_completion()

    # Stop the workers
    await worker.stop()
    print(worker.results)  # Print the results of the tasks

# Run the async main function
if __name__ == "__main__":
    asyncio.run(main())