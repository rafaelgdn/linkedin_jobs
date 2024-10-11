from utils import start_driver, load_csv_data, wait_for_network_idle
from helpers.logger import logger
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import asyncio
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
assets_path = os.path.join(current_dir, "assets")


def is_url(string):
    try:
        result = urlparse(string)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


async def is_404(driver):
    if await driver.execute_script("return window.performance.getEntries()[0].responseStatus") == 404:
        return True

    current_url = await driver.current_url
    if "/404" in current_url.lower() or "not-found" in current_url.lower():
        return True

    soup = BeautifulSoup(await driver.page_source, "html.parser")

    title = soup.title.string.lower() if soup.title else ""
    if "404" in title or "not found" in title or "error" in title:
        return True

    body_text = soup.body.text.lower() if soup.body else ""
    error_phrases = ["404", "not found", "page not found", "error", "does not exist"]
    if any(phrase in body_text for phrase in error_phrases):
        return True

    error_selectors = ["[id*='error']", "[class*='error']", "[id*='404']", "[class*='404']", "[id*='not-found']", "[class*='not-found']"]
    if any(soup.select_one(selector) for selector in error_selectors):
        return True

    return False


def get_job_element(element, tags, classes, ids):
    for _class in classes:
        item = element.select_one(f"[class*='{_class}']")
        if item:
            return item

    for _id in ids:
        item = element.select_one(f"[id*='{_id}']")
        if item:
            return item


def get_job_elements(element, tags, classes, ids):
    for _class in classes:
        items = element.select(f"[class*='{_class}']")
        if items:
            return items

    for _id in ids:
        items = element.select(f"[id*='{_id}']")
        if items:
            return items


async def extract_job_listings(driver):
    for _ in range(20):
        await driver.execute_script("window.scrollBy(0, 300);")
        await driver.sleep(0.2)

    await driver.sleep(2)

    soup = BeautifulSoup(await driver.page_source, "html.parser")

    job_listings = []

    job_item_identifiers = {
        "tags": ["div", "li", "article"],
        "classes": ["premium-blog-post-container", "single-position", "b-open-positions__job"],
        "ids": [],
    }

    title_identifiers = {
        "tags": ["h1", "h2", "h3", "h4", "strong", "span", "a", "p"],
        "classes": ["position-name", "premium-blog-entry-title", "job-name"],
        "ids": [],
    }

    description_identifiers = {
        "tags": ["p", "div", "span"],
        "classes": ["position-details", "premium-blog-post-content"],
        "ids": [],
    }

    location_identifiers = {
        "tags": ["span", "div", "p"],
        "classes": ["position-location", "job-location"],
        "ids": [],
    }

    job_elements = get_job_elements(soup, **job_item_identifiers)

    for element in job_elements:
        if element:
            job = {}

            title_element = get_job_element(element, **title_identifiers)
            if title_element:
                job["title"] = title_element.text.strip()

                if title_element.name == "a" and "href" in title_element.attrs:
                    job["url"] = title_element["href"]
                else:
                    link = title_element.find("a")
                    if link and "href" in link.attrs:
                        job["url"] = link["href"]

            description_element = get_job_element(element, **description_identifiers)
            if description_element:
                job["description"] = description_element.text.strip()

            location_element = get_job_element(element, **location_identifiers)
            if location_element:
                job["location"] = location_element.text.strip()

            if job:
                job_listings.append(job)

    return job_listings


async def main():
    driver = await start_driver()

    founders = load_csv_data(f"{assets_path}/founders.csv")

    job_page_suffixes = [
        "/careers",
        "/jobs",
        "/openings",
        "/opportunities",
        "/positions",
        "/vacancies",
        "/work-with-us",
        "/join-us",
        "/join-our-team",
        "/employment",
        "/current-openings",
        "/job-opportunities",
        "/career-opportunities",
        "/work-for-us",
        "/job-listings",
        "/job-search",
        "/open-positions",
    ]

    for founder in founders:
        if not founder["Website"] or not is_url(founder["Website"]):
            logger.skip(f"Skipping {founder['Name']} because Website URL is invalid.")
            continue

        website_url = founder["Website"].rstrip("/")

        job_listings = []

        for suffix in job_page_suffixes:
            logger.info(f"Checking {founder['Name']} on {website_url}{suffix}")

            await driver.get(f"{website_url}{suffix}", wait_load=True)
            await wait_for_network_idle(driver)
            await driver.sleep(0.5)

            if not await is_404(driver):
                job_listings = await extract_job_listings(driver)
                if job_listings:
                    break

        if job_listings:
            logger.success(f"Found {len(job_listings)} job listings for {founder['Name']}")
            for job in job_listings:
                logger.success(f"Title: {job.get('title', 'N/A')}")
                logger.success(f"Description: {job.get('description', 'N/A')[:100]}...")
                logger.success(f"Location: {job.get('location', 'N/A')}")
                logger.success(f"Url: {job.get('url', 'N/A')[:100]}")
                logger.success("---")
        else:
            logger.warning(f"No job listings found for {founder['Name']}")


asyncio.run(main())
