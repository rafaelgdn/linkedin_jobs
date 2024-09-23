import asyncio
from helpers.utils import start_driver
from helpers.linkedin import linkedin_scraper


async def main():
    driver = await start_driver()
    await linkedin_scraper(driver)

    await driver.quit()


asyncio.run(main())
