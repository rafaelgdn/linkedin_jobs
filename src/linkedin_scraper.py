from utils import start_driver, load_csv_data, wait_for_selector, race, wait_for_network_idle, save_success_csv
from tenacity import retry, stop_after_attempt, wait_fixed
from selenium_driverless.types.by import By
from helpers.accounts import get_account
from helpers.cookies import update_cookies
from helpers.tech_jobs import is_tech_job
from linkedin.login import login
from urllib.parse import urlparse
from rich.console import Console
from bs4 import BeautifulSoup
import asyncio
import logging
import os

console = Console()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

current_dir = os.path.dirname(os.path.abspath(__file__))
assets_path = os.path.join(current_dir, "assets")


def is_url(string):
    try:
        result = urlparse(string)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


@retry(stop=stop_after_attempt(10), wait=wait_fixed(5))
async def get_jobs_by_soup(driver):
    try:
        current_page = 1
        jobs = []
        tech_jobs = []

        while True:
            await driver.sleep(0.5)
            await wait_for_selector(driver, "ul.scaffold-layout__list-container li div[class*='content'] div[class*='title']")

            jobs_list = await wait_for_selector(driver, "div.jobs-search-results-list")

            for _ in range(30):
                await driver.execute_script("arguments[0].scrollBy(0, 200);", jobs_list)
                await driver.sleep(0.2)

            content = await driver.page_source
            soup = BeautifulSoup(content, "html.parser")

            pagination = soup.select("ul.jobs-search-pagination__pages li.jobs-search-pagination__indicator")

            if not pagination:
                pagination = soup.select("ul li[data-test-pagination-page-btn]")

            jobs_card_elements = soup.select("ul.scaffold-layout__list-container li.jobs-search-results__list-item")

            if not jobs_card_elements:
                await driver.refresh()
                await driver.sleep(2)
                raise Exception("No jobs found")

            for job_card_element in jobs_card_elements:
                url = job_card_element.select_one("a")["href"].split("?")[0]
                url = f"https://linkedin.com{url}"
                title = job_card_element.select_one("div[class*='content'] div[class*='title'] strong").text.replace("\n", "").strip()
                job = {"url": url, "title": title}
                jobs.append(job)
                is_tech = is_tech_job(title)
                if is_tech:
                    tech_jobs.append(job)
                logging.info("Job found.")
                console.print(f"[bold dark_green]tech: {is_tech}\ntitle: {title}\nurl: {url}[/bold dark_green]")

            if not pagination:
                break

            current_page += 1

            has_button = soup.select_one(f"button[aria-label='Page {current_page}']")

            if has_button:
                button = await wait_for_selector(driver, f"button[aria-label='Page {current_page}']")
                await driver.execute_script("arguments[0].click()", button)
            else:
                break

        return jobs, tech_jobs
    except Exception as e:
        logging.error(f"Error getting jobs: {e}")
        raise e


@retry(stop=stop_after_attempt(10), wait=wait_fixed(5))
async def get_jobs_by_browser(driver):
    jobs = []

    await driver.sleep(0.5)
    await wait_for_selector(driver, "div.jobs-search-results-list")
    await wait_for_selector(driver, "ul.scaffold-layout__list-container li div[class*='content'] div[class*='title']")
    await driver.sleep(2)

    pagination_selector = "ul.jobs-search-pagination__pages li.jobs-search-pagination__indicator"
    pagination = await driver.execute_script(f"return document.querySelectorAll('{pagination_selector}')")

    if not pagination:
        pagination_selector = "ul li[data-test-pagination-page-btn]"
        pagination = await driver.execute_script(f"return document.querySelectorAll('{pagination_selector}')")

    current_page = 1

    while True:
        if current_page > 1:
            await wait_for_network_idle(driver)
            await driver.sleep(0.5)

        while True:
            jobs_card_elements = await driver.execute_script(
                "return document.querySelectorAll('ul.scaffold-layout__list-container li.jobs-search-results__list-item')"
            )
            if jobs_card_elements:
                break

        for job_card_element in jobs_card_elements:
            try:
                url_element = await job_card_element.find_element(By.CSS_SELECTOR, "a")
                url = await url_element.get_attribute("href")

                title = await job_card_element.find_element(By.CSS_SELECTOR, "div[class*='content'] div[class*='title'] strong")
                title_text = (await title.text).replace("\n", "").strip()

                subtitle = await job_card_element.find_element(By.CSS_SELECTOR, "div[class*='content'] div[class*='subtitle']")
                subtitle_text = (await subtitle.text).replace("\n", "").strip()

                location = await job_card_element.find_element(By.CSS_SELECTOR, "div[class*='content'] div[class*='caption']")
                location_text = (await location.text).replace("\n", "").strip()

                try:
                    metadata = await job_card_element.find_element(By.CSS_SELECTOR, "div[class*='content'] div[class*='metadata']")
                    metadata_text = (await metadata.text).replace("\n", "").replace("\\xa", "").strip()
                except Exception:
                    metadata_text = ""
            except Exception:
                continue

            job = {"url": url, "title": title_text, "subtitle": subtitle_text, "location": location_text, "metadata": metadata_text}
            console.print(
                f"[bold aquamarine3]link: {job['url']}\ntitle: {job['title']}\nsubtitle: {job['subtitle']}\nlocation: {job['location']}[/bold aquamarine3]"
            )
            jobs.append(job)

        if not pagination:
            break

        current_page += 1

        button = await driver.execute_script(f"return document.querySelector(\"button[aria-label='Page {current_page}'\")")

        if button:
            await driver.execute_script("arguments[0].click()", button)
        else:
            await driver.sleep(2)
            button = await driver.execute_script(f"return document.querySelector(\"button[aria-label='Page {current_page}'\")")
            if button:
                await driver.execute_script("arguments[0].click()", button)
            else:
                break

    return jobs


@retry(stop=stop_after_attempt(10), wait=wait_fixed(5))
async def get_linkedin_jobs_from_company(driver, linkedin_url):
    await driver.get(f"{linkedin_url}jobs", wait_load=True)
    await wait_for_network_idle(driver)

    try:
        num_employees_element = await wait_for_selector(driver, "a[href*='/search/results/people'] span", timeout=10)
        num_employees_text = (await num_employees_element.text).replace("\n", "").strip().split(" ")[0]
    except Exception:
        pass

    race_response = await race(
        wait_for_selector(driver, "p.artdeco-empty-state__message", response="not_found_page", timeout=10),
        wait_for_selector(driver, "div.org-jobs-empty-jobs-module", response="no_jobs", timeout=10),
        wait_for_selector(driver, "div.org-jobs-recently-posted-jobs-module a[href*='/jobs/search']", timeout=10),
    )

    if race_response == "no_jobs":
        return [], [], num_employees_text

    if race_response == "not_found_page" or not race_response:
        return [], [], "0"

    await driver.execute_script("arguments[0].click()", race_response)
    await wait_for_network_idle(driver)

    jobs, tech_jobs = await get_jobs_by_soup(driver)

    return jobs, tech_jobs, num_employees_text


@retry(stop=stop_after_attempt(10), wait=wait_fixed(5))
async def get_linkedin_jobs_from_profile(driver, linkedin_url):
    logging.info(f"Getting jobs from {linkedin_url}")

    while True:
        await driver.get(linkedin_url, wait_load=True)
        await wait_for_network_idle(driver)

        race_response = await race(
            wait_for_selector(driver, "section.artdeco-card.pv-profile-card.break-words div#experience", visible=False),
            wait_for_selector(driver, "#error404", response="page_not_found"),
            wait_for_selector(driver, "div[class*='not-found']", response="page_not_found"),
            wait_for_selector(driver, "a[href*='404_page']", response="page_not_found"),
        )

        if race_response == "page_not_found":
            console.print("[bold dark_orange3]Page not found.[/bold dark_orange3]")
            return [], [], "0"

        if race_response != "premium_alert":
            break

    await wait_for_selector(driver, "a[href*='linkedin.com/company/']", throw_error=True, timeout=60)
    experience_section = await driver.execute_script("return arguments[0].parentNode;", race_response)
    experience_elements = await experience_section.find_elements(By.CSS_SELECTOR, "a[href*='linkedin.com/company/']")

    if not experience_elements:
        return [], [], "0"

    last_company = experience_elements[0]
    last_company_url = await last_company.get_attribute("href")
    jobs, tech_jobs, num_employees_text = await get_linkedin_jobs_from_company(driver, last_company_url)
    return jobs, tech_jobs, num_employees_text


async def main():
    driver = await start_driver()

    founders = load_csv_data(f"{assets_path}/founders.csv")

    for founder in founders:
        if not founder["LinkedIn"] or not is_url(founder["LinkedIn"]):
            console.print(f"[bold cyan]Skipping {founder['Name']} because LinkedIn URL is invalid.[/bold cyan]")
            continue

        account = await get_account()
        await login(driver, account)

        if "company" in founder["LinkedIn"]:
            func = get_linkedin_jobs_from_company
        else:
            func = get_linkedin_jobs_from_profile

        race_response = await race(
            func(driver, founder["LinkedIn"]),
            wait_for_selector(driver, "header.premium-custom-nav.global-alert-offset-top", response="premium_alert", timeout=999999999),
        )

        if race_response == "premium_alert":
            console.print("[bold dark_orange3]Premium alert found, changing account... [/bold dark_orange3]")
            account = await get_account()
            await login(driver, account)
            continue

        linkedin_jobs, tech_jobs, num_employees = race_response

        founder["# of Employees"] = num_employees
        founder["Jobs on Linkedin"] = linkedin_jobs
        founder["Tech Jobs on Linkedin"] = tech_jobs
        logging.info("Founder scraper result.")
        console.print(
            f"[bold green]linkedin_jobs: {len(linkedin_jobs)}\ntech_jobs: {len(tech_jobs)}\nlinkedin_employees: {num_employees}[/bold green]"
        )

        save_success_csv(founder, f"{assets_path}/founders_linkedin_jobs.csv")
        await update_cookies(driver, account["email"])

    await driver.quit()


asyncio.run(main())
