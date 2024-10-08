import requests
from selenium_driverless.types.by import By
from ..utils import wait_for_selector, race


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
