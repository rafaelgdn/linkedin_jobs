from selenium_driverless.types.by import By
from src.utils import wait_for_selector, race, wait_for_network_idle, type_with_delay
from helpers.cookies import load_cookies, save_cookies
from helpers.two_factor import two_factor_authentication
from helpers.captcha import solve_captcha


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
        await solve_captcha(driver, "2captcha")

    if race_response == "2fa":
        await two_factor_authentication(driver, account)

    await save_cookies(driver, account["email"])
