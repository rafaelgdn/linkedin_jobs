import os
import json
import requests
from twocaptcha import TwoCaptcha
from urllib.parse import urlparse
from selenium_driverless.types.by import By
from urllib.parse import parse_qs, urlencode
from .utils import race, wait_for_selector, type_with_delay, load_csv_data, save_success_csv, wait_for_network_idle
from selenium_driverless.scripts.network_interceptor import (
    NetworkInterceptor,
    InterceptedRequest,
    RequestPattern,
)

accounts = [
    # {"email": "ErginKaya733@gmail.com", "password": "Bn@#9262853856286", "2FA": "WAG6NVZNXL5RY6QTGTE52UF3ZL2VT6XG"},
    # {"email": "reysisaydan371@gmail.com", "password": "Bn@#9262853856286", "2FA": "L3NTQPHTRTJMG24OCMX5XAWMPNFMVJFI"},
    # {"email": "fevzidege286@gmail.com", "password": "Bn@#9262853856286", "2FA": "MNCBPX4MDSWTQJKAEQBGFWHYEEC5FPLL"},
    # {"email": "aysecansucinar592@gmail.com", "password": "Bn@#9262853856286", "2FA": "KMW2IJA5Z4X7CAPOEROPCY53B54R4OYK"},
    # {"email": "caneraskar491@gmail.com", "password": "Bn@#9262853856286", "2FA": "XZ3LLWVLV4OOII44C4AAT3UIBJTJOWDE"},
    {"email": "NusretAkay033@gmail.com", "password": "Bn@#9262853856286", "2FA": "CH7KWEZB3CPE3MIQETVDZABUZQSFBBSU"},
    {"email": "kezibanyediel468@gmail.com", "password": "Bn@#9262853856286", "2FA": "SIEMCWS2WOLFKEUVPF6P4F6WQNLXTZKA"},
    {"email": "OrhanSezer177@gmail.com", "password": "Bn@#9262853856286", "2FA": "O55GSPH6QAJGQGKUTAU4BANLJWEROYXW"},
    {"email": "tekinakdemir21@gmail.com", "password": "Bn@#9262853856286", "2FA": "O63JGN6ZQVOIMVM6CEVIPGCZCGUG7F62"},
    {"email": "tekinakdemir14@gmail.com", "password": "Bn@#9262853856286", "2FA": "65TQ33OVGPLVFZIGBS3ILIZMVFWNYOCD"},
    {"email": "necatikantar75@gmail.com", "password": "Bn@#9262853856286", "2FA": "DWY3SK7E2CFI2RVVAV4N6PHPTDJZWI7Q"},
    {"email": "sefacanbay79@gmail.com", "password": "Bn@#9262853856286", "2FA": "TZOPZC3ATHBFRRWXYO2RB24CTBTEO2FL"},
    {"email": "samedakbulut24@gmail.com", "password": "Bn@#9262853856286", "2FA": "LP4YTEVVFL6V44WNNU46OR5HGAMWTPS3"},
    {"email": "samedakbulut58@gmail.com", "password": "Bn@#9262853856286", "2FA": "KAFVMFCUS7MKW62EUZFBVD3DTFIK63OT"},
    {"email": "halimaybakan503@gmail.com", "password": "Bn@#9262853856286", "2FA": "N3F2ERTGMROABW2JVQYJEF2UOY3NE3X6"},
    {"email": "rukiyekaygusuz813@gmail.com", "password": "Bn@#9262853856286", "2FA": "KO2VX7ITJXVDY3GC4BKOZRQUTD2C2FYZ"},
]

founders_scraped = 0
account_index = 0
first_acc_call = True
api_key_2captcha = ""

current_dir = os.path.dirname(os.path.abspath(__file__))
current_dir_abspath = os.path.abspath(current_dir)
assets_path = os.path.join(current_dir_abspath, "..", "assets")
assets_abspath = os.path.abspath(assets_path)


def is_url(string):
    try:
        result = urlparse(string)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


async def call_2captcha(site_key, iframe_src):
    solver = TwoCaptcha(api_key_2captcha)
    response = await solver.funcaptcha(sitekey=site_key, url=iframe_src)
    print(f"2captcha response: {response}")
    return response


async def solve_captcha(driver):
    async def on_request(data: InterceptedRequest, captcha_response):
        if "checkpoint/challenge/verify" in data.request.url and data.request.method == "POST":
            print(f"Original data: {data.request.post_data}")
            payload_dict = parse_qs(data.request.post_data)
            payload_dict = {k: v[0] if len(v) == 1 else v for k, v in payload_dict.items()}
            print(f"parsed data: {payload_dict}")
            payload_dict["captchaUserResponseToken"] = captcha_response
            modified_payload = urlencode(payload_dict)
            modified_payload_binary = modified_payload.encode("utf-8")
            await data.continue_request(post_data=modified_payload_binary)
        else:
            await data.resume()

    print("Solving captcha...")
    await driver.sleep(10)
    site_key_element = await driver.find_element(By.CSS_SELECTOR, "form#captcha-challenge input[name='captchaSiteKey']")
    site_key = await site_key_element.get_attribute("value")
    print(f"siteKey: {site_key}")

    iframe = await driver.find_element(By.CSS_SELECTOR, "iframe#captcha-internal")
    iframe_src = await iframe.get_attribute("src")
    print(f"iframe_src: {iframe_src}")

    captcha_response = await call_2captcha(site_key, iframe_src)

    async with NetworkInterceptor(
        driver,
        on_request=lambda r: on_request(r, captcha_response),
        patterns=[RequestPattern.AnyRequest],
    ) as interceptor:
        await driver.execute_script("document.querySelector('form#captcha-challenge').submit()")

        async for data in interceptor:
            if "checkpoint/challenge/verify" in data.request.url and data.request.method == "POST":
                print(f"Modified?: {data.request.post_data}")


async def load_cookies(driver, email):
    try:
        with open(f"cookies-{email}.json", "r") as f:
            cookies = json.load(f)
            for cookie in cookies:
                await driver.add_cookie(cookie)
    except FileNotFoundError:
        print("Cookie file not found.")


async def save_cookies(driver, email):
    cookies = await driver.get_cookies()
    with open(f"cookies-{email}.json", "w") as f:
        json.dump(cookies, f)


async def update_cookies(driver, email):
    await save_cookies(driver, email)


async def two_factor_authentication(driver, account):
    print("Two-factor authentication...")
    two_factor_authentication_code = account["2FA"]
    response = requests.get(f"https://2fa.live/tok/{two_factor_authentication_code}")
    token = response.json().get("token")
    await driver.sleep(2)
    input_element = await driver.find_element(By.CSS_SELECTOR, "input.input_verification_pin")
    await input_element.send_keys(token)
    submit_element = await driver.find_element(By.ID, "two-step-submit-button")
    await driver.execute_script("arguments[0].click()", submit_element)

    race_response = await race(
        wait_for_selector(driver, "button.sign-in-modal", response="modal"),
        wait_for_selector(driver, "section.artdeco-card", response="logged"),
    )

    if race_response == "modal":
        email_input = await driver.find_element(By.ID, "base-sign-in-modal_session_key")
        await email_input.send_keys(account["email"])
        password_input = await driver.find_element(By.ID, "base-sign-in-modal_session_password")
        await password_input.send_keys(account["password"])
        submit_button = await driver.find_element(By.CSS_SELECTOR, "button[data-id='sign-in-form__submit-btn']")
        await driver.execute_script("arguments[0].click()", submit_button)

        input_2fa = wait_for_selector(driver, "input.input_verification_pin", visible=False, check_interval=0.1)
        response = requests.get(f"https://2fa.live/tok/{two_factor_authentication_code}")
        token = response.json().get("token")
        await driver.sleep(2)
        await input_2fa.send_keys(token)
        submit_element = await driver.find_element(By.ID, "two-step-submit-button")
        await driver.execute_script("arguments[0].click()", submit_element)


async def login(driver, account):
    print(f"Logging in account: {account['email']}")

    if account.get("proxy", None):
        await driver.set_single_proxy(account["proxy"])

    await load_cookies(driver, account["email"])

    await driver.get("https://www.linkedin.com/login", wait_load=True)

    race_response = await race(
        wait_for_selector(driver, "section.artdeco-card", response="logged"),
        wait_for_selector(driver, "#password", response="need_login"),
    )

    if race_response == "logged":
        print("Already logged in.")
        return

    await wait_for_network_idle(driver)

    has_member_profile = await driver.find_elements(By.CSS_SELECTOR, "div.profile-action-container button.more-actions-btn")

    if not has_member_profile:
        await wait_for_selector(driver, "#username")
        user_element = await driver.find_element(By.ID, "username")
        await type_with_delay(driver, user_element, account["email"])

    pass_element = await driver.find_element(By.ID, "password")
    await type_with_delay(driver, pass_element, account["password"])

    submit_button = await driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    await driver.execute_script("arguments[0].click()", submit_button)

    race_response = await race(
        wait_for_selector(driver, "#captcha-internal", response="captcha"),
        wait_for_selector(driver, "section.artdeco-card", response="logged"),
        wait_for_selector(driver, "input.input_verification_pin", response="2fa", visible=False, check_interval=0.1),
    )

    if race_response == "captcha":
        await solve_captcha(driver)

    if race_response == "2fa":
        await two_factor_authentication(driver, account)

    await save_cookies(driver, account["email"])


async def get_jobs(driver):
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
            print(f"\nlink: {job['url']}\ntitle: {job['title']}\nsubtitle: {job['subtitle']}\nlocation: {job['location']}\n")
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


async def get_linkedin_jobs_from_company(driver, linkedin_url):
    await driver.get(f"{linkedin_url}jobs", wait_load=True)

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
        return [], num_employees_text

    if race_response == "not_found_page" or not race_response:
        return [], "0"

    await driver.execute_script("arguments[0].click()", race_response)
    await wait_for_network_idle(driver)

    jobs = await get_jobs(driver)
    return jobs, num_employees_text


async def get_linkedin_jobs_from_profile(driver, linkedin_url):
    print(f"Getting jobs from {linkedin_url}")

    while True:
        await driver.get(linkedin_url, wait_load=True)

        race_response = await race(
            wait_for_selector(driver, "section.artdeco-card.pv-profile-card.break-words div#experience", visible=False),
            wait_for_selector(driver, "#error404", response="page_not_found"),
            wait_for_selector(driver, "div[class*='not-found']", response="page_not_found"),
            wait_for_selector(driver, "a[href*='404_page']", response="page_not_found"),
        )

        if race_response == "page_not_found":
            print("Page not found.")
            return [], "0"

        if race_response != "premium_alert":
            break

    experience_section = await driver.execute_script("return arguments[0].parentNode;", race_response)
    experience_elements = await experience_section.find_elements(By.CSS_SELECTOR, "a[href*='linkedin.com/company/']")

    if not experience_elements:
        return [], "0"

    last_company = experience_elements[0]
    last_company_url = await last_company.get_attribute("href")
    jobs, num_employees_text = await get_linkedin_jobs_from_company(driver, last_company_url)
    return jobs, num_employees_text


def get_linkedin_account():
    global account_index, first_acc_call
    accounts_len = len(accounts)

    if first_acc_call:
        first_acc_call = False
    else:
        account_index += 1

    if account_index >= accounts_len - 1:
        account_index = 0

    return accounts[account_index]


async def linkedin_scraper(driver):
    global founders_scraped

    account = get_linkedin_account()

    await login(driver, account)

    founders = load_csv_data(f"{assets_abspath}/founders.csv")

    for founder in founders:
        if not founder["LinkedIn"] or not is_url(founder["LinkedIn"]):
            print(f"Skipping {founder['Name']} because LinkedIn URL is invalid.")
            continue

        linkedin_jobs = None
        num_employees = None

        while linkedin_jobs is None and num_employees is None:
            if founders_scraped >= 3:
                print("Too many extrations, changing account...")
                founders_scraped = 0
                await update_cookies(driver, account["email"])
                account = get_linkedin_account()
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
                print("Premium alert found, changing account... ")
                account = get_linkedin_account()
                await login(driver, account)
                continue

            linkedin_jobs, num_employees = race_response

            founder["# of Employees"] = num_employees
            founder["Jobs on Linkedin"] = linkedin_jobs
            print(f"\nlinkedin_jobs: {len(linkedin_jobs)}\nlinkedin_employees: {num_employees}\n")
            founders_scraped += 1

            save_success_csv(founder, f"{assets_abspath}/founders_linkedin_jobs.csv")
    await update_cookies(driver, account["email"])
    return founders
