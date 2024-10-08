import json


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
