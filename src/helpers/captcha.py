from tenacity import retry_if_exception_type, stop_after_attempt, retry, retry_if_result
from twocaptcha import TwoCaptcha, TimeoutException, ApiException, NetworkException
from urllib.parse import quote
from bs4 import BeautifulSoup
import requests
import logging
import time
import json
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

attempt = 0


def is_none(value):
    return value is None


@retry(
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type((TimeoutException, ApiException, NetworkException)),
)
async def solve_2captcha(captcha_blob, url):
    """https://2captcha.com/"""

    global attempt

    logging.info(f"Waiting on 2Captcha to solve captcha attempt {attempt} / 5 ...")

    attempt += 1

    solver = TwoCaptcha(os.environ.get("TWOCAPTCHA_API_KEY"))

    result = solver.funcaptcha(
        sitekey="3117BF26-4762-4F5A-8ED9-A85E69209A46",
        url=url,
        **{"data[blob]": captcha_blob},
        surl="https://iframe.arkoselabs.com",
    )

    logging.info("2Captcha finished solving captcha")

    return result["code"]


@retry(stop=stop_after_attempt(10), retry=retry_if_result(is_none))
async def solve_capsolver(captcha_blob, url):
    """https://capsolver.com/"""

    logging.info("Waiting on CapSolver to solve captcha...")

    payload = {
        "clientKey": os.environ.get("CAPSOLVER_API_KEY"),
        "task": {
            "type": "FunCaptchaTaskProxyLess",
            "websitePublicKey": "3117BF26-4762-4F5A-8ED9-A85E69209A46",
            "websiteURL": url,
            "data": json.dumps({"blob": captcha_blob}) if captcha_blob else "",
        },
    }

    res = requests.post("https://api.capsolver.com/createTask", json=payload)
    resp = res.json()
    task_id = resp.get("taskId")

    if not task_id:
        raise Exception(
            "CapSolver failed to create task, try another captcha solver like 2Captcha if this persists or use browser sign in `pip install staffspy[browser]` and then remove the username/password params to the LinkedInAccount()",
            res.text,
        )

    logging.info(f"Received captcha solver taskId: {task_id} / Getting result...")

    while True:
        time.sleep(1)
        payload = {"clientKey": os.environ.get("CAPSOLVER_API_KEY"), "taskId": task_id}
        res = requests.post("https://api.capsolver.com/getTaskResult", json=payload)
        resp = res.json()
        status = resp.get("status")
        if status == "ready":
            logging.info("CapSolver finished solving captcha")
            return resp.get("solution", {}).get("token")
        if status == "failed" or resp.get("errorId"):
            logging.info(f"Captcha solve failed! response: {res.text}")
            return None


async def solve_captcha(driver, solver):
    url = await driver.current_url

    content = await driver.page_source

    soup = BeautifulSoup(content, "html.parser")

    code_tag = soup.find("code", id="securedDataExchange")

    logging.info("Searching for captcha blob in linkedin to begin captcha solving")

    if code_tag:
        comment = code_tag.contents[0]
        extracted_code = str(comment).strip('<!--""-->').strip()
        logging.info("Extracted captcha blob:", extracted_code)
    elif "Please choose a more secure password." in content:
        raise Exception("Linkedin is requiring a more secure password. Reset pw and try again")
    else:
        raise Exception("Could not find captcha blob")

    if solver == "2captcha":
        captcha_response = await solve_2captcha(extracted_code, url)
    elif solver == "capsolver":
        captcha_response = await solve_capsolver(extracted_code, url)
    else:
        raise Exception("Invalid captcha solver")

    captcha_site_key = soup.find("input", {"name": "captchaSiteKey"})["value"]
    challenge_id = soup.find("input", {"name": "challengeId"})["value"]
    challenge_data = soup.find("input", {"name": "challengeData"})["value"]
    challenge_details = soup.find("input", {"name": "challengeDetails"})["value"]
    challenge_type = soup.find("input", {"name": "challengeType"})["value"]
    challenge_source = soup.find("input", {"name": "challengeSource"})["value"]
    request_submission_id = soup.find("input", {"name": "requestSubmissionId"})["value"]
    display_time = soup.find("input", {"name": "displayTime"})["value"]
    page_instance = soup.find("input", {"name": "pageInstance"})["value"]
    failure_redirect_uri = soup.find("input", {"name": "failureRedirectUri"})["value"]
    sign_in_link = soup.find("input", {"name": "signInLink"})["value"]
    join_now_link = soup.find("input", {"name": "joinNowLink"})["value"]

    cookies = await driver.get_cookies()

    for cookie in cookies:
        if cookie.name == "JSESSIONID":
            jsession_value = cookie.value.split("ajax:")[1].strip('"')
            break
    else:
        raise Exception("jsessionid not found")

    csrf_token = f"ajax:{jsession_value}"

    payload = {
        "csrfToken": csrf_token,
        "captchaSiteKey": captcha_site_key,
        "challengeId": challenge_id,
        "language": "en-US",
        "displayTime": display_time,
        "challengeType": challenge_type,
        "challengeSource": challenge_source,
        "requestSubmissionId": request_submission_id,
        "captchaUserResponseToken": captcha_response,
        "challengeData": challenge_data,
        "pageInstance": page_instance,
        "challengeDetails": challenge_details,
        "failureRedirectUri": failure_redirect_uri,
        "signInLink": sign_in_link,
        "joinNowLink": join_now_link,
        "_s": "CONSUMER_LOGIN",
    }
    encoded_payload = {key: f'{quote(str(value), "")}' for key, value in payload.items()}

    query_string = "&".join([f"{key}={value}" for key, value in encoded_payload.items()])

    await driver.fetch("https://www.linkedin.com/checkpoint/challenge/verify", method="POST", body=query_string)


# async def solve_captcha(driver):
#     async def on_request(data: InterceptedRequest, captcha_response):
#         if "checkpoint/challenge/verify" in data.request.url and data.request.method == "POST":
#             print(f"Original data: {data.request.post_data}")
#             payload_dict = parse_qs(data.request.post_data)
#             payload_dict = {k: v[0] if len(v) == 1 else v for k, v in payload_dict.items()}
#             print(f"parsed data: {payload_dict}")
#             payload_dict["captchaUserResponseToken"] = captcha_response
#             modified_payload = urlencode(payload_dict)
#             modified_payload_binary = modified_payload.encode("utf-8")
#             await data.continue_request(post_data=modified_payload_binary)
#         else:
#             await data.resume()

#     print("Solving captcha...")
#     await driver.sleep(10)
#     site_key_element = await driver.find_element(By.CSS_SELECTOR, "form#captcha-challenge input[name='captchaSiteKey']")
#     site_key = await site_key_element.get_attribute("value")
#     print(f"siteKey: {site_key}")

#     iframe = await driver.find_element(By.CSS_SELECTOR, "iframe#captcha-internal")
#     iframe_src = await iframe.get_attribute("src")
#     print(f"iframe_src: {iframe_src}")

#     captcha_response = await call_2captcha(site_key, iframe_src)

#     async with NetworkInterceptor(
#         driver,
#         on_request=lambda r: on_request(r, captcha_response),
#         patterns=[RequestPattern.AnyRequest],
#     ) as interceptor:
#         await driver.execute_script("document.querySelector('form#captcha-challenge').submit()")

#         async for data in interceptor:
#             if "checkpoint/challenge/verify" in data.request.url and data.request.method == "POST":
#                 print(f"Modified?: {data.request.post_data}")
