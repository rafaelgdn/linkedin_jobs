from selenium_driverless import webdriver
from selenium_driverless.types.by import By
from tqdm import tqdm
from rich.console import Console
import asyncio
import random
import shutil
import time
import csv
import os

console = Console()
current_dir = os.path.dirname(os.path.abspath(__file__))
current_dir_abspath = os.path.abspath(current_dir)


def setup_temp_profile():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    current_dir_abspath = os.path.abspath(current_dir)

    root_dir = os.path.join(current_dir_abspath, "..")
    root_dir_abspath = os.path.abspath(root_dir)

    profiles_dir = os.path.join(root_dir_abspath, "utils", "profiles")
    temp_dir = os.path.join(root_dir_abspath, "profiles_temp")
    temp_dir_abspath = os.path.abspath(temp_dir)

    downloads_dir = os.path.join(current_dir_abspath, "..", "downloads")
    downloads_dir_abspath = os.path.abspath(downloads_dir)

    profile_name = "Profile 5"

    if os.path.exists(temp_dir_abspath):
        try:
            shutil.rmtree(temp_dir_abspath)
            print("Temp folder successfully removed.")
        except Exception as e:
            print(f"Error removing temp folder: {e}")

    os.makedirs(temp_dir_abspath, exist_ok=True)

    if os.path.exists(downloads_dir_abspath):
        try:
            shutil.rmtree(downloads_dir_abspath)
            print("Downloads folder successfully removed.")
        except Exception as e:
            print(f"Error removing temp folder: {e}")

    os.makedirs(temp_dir_abspath, exist_ok=True)
    source_profile = os.path.join(profiles_dir, profile_name)
    dest_profile = os.path.join(temp_dir_abspath, profile_name)

    if os.path.exists(dest_profile):
        shutil.rmtree(dest_profile)

    shutil.copytree(source_profile, dest_profile)
    return temp_dir_abspath, profile_name, downloads_dir_abspath


async def start_driver():
    options = webdriver.ChromeOptions()
    # options.downloads_dir = downloads_dir_abspath
    # options.user_data_dir = temp_dir_abspath
    # options.add_argument(f"--user-data-dir={temp_dir_abspath}")
    # options.add_argument(f"--profile-directory={profile_name}")
    # options.add_argument("--headless")  # uncomment this line to run in headless mode
    # options.add_argument("--disable-gpu")  # comment to run in a cloud
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--detach")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-translate")
    options.add_argument("--disable-features=VizDisplayCompositor")
    options.add_argument("--disable-features=IsolateOrigins,site-per-process")
    options.add_argument("--disable-features=BlockInsecurePrivateNetworkRequests")
    options.add_argument("--disable-features=OutOfBlinkCors")
    options.add_argument("--disable-features=SameSiteByDefaultCookies,CookiesWithoutSameSiteMustBeSecure")
    options.add_argument("--disable-features=CrossSiteDocumentBlockingIfIsolating,CrossSiteDocumentBlockingAlways")
    options.add_argument("--disable-features=ImprovedCookieControls,LaxSameSiteCookies,SameSiteByDefaultCookies,CookiesWithoutSameSiteMustBeSecure")
    options.add_argument("--disable-features=SameSiteDefaultChecksMethodRigorously")
    driver = await webdriver.Chrome(options=options)
    return driver


async def wait_for_selector(driver, selector, timeout=30, check_interval=0.5, response=None, visible=True, xpath=False):
    start_time = asyncio.get_event_loop().time()
    while (asyncio.get_event_loop().time() - start_time) < timeout:
        try:
            if xpath:
                element = await driver.find_element(By.XPATH, selector, timeout=check_interval)
            else:
                element = await driver.find_element(By.CSS_SELECTOR, selector, timeout=check_interval)
            if not visible and element:
                return response or element
            if await element.is_displayed():
                return response or element
        except Exception:
            pass

        await asyncio.sleep(check_interval)


async def race(*coroutines):
    done, pending = await asyncio.wait(coroutines, return_when=asyncio.FIRST_COMPLETED)
    for task in pending:
        task.cancel()
    return done.pop().result()


async def type_with_delay(driver, element, text, min_delay=0.2, max_delay=0.5):
    for i, char in enumerate(text):
        if i == 0:
            await element.send_keys(char, click_on=True)
        else:
            await element.send_keys(char, click_on=False)

        if i < len(text) - 1:
            await driver.sleep(random.uniform(min_delay, max_delay))

    await driver.sleep(0.5)


async def move_mouse_around_element(driver, element, num_movements=6):
    location = await element.location
    size = await element.size
    pointer = driver.current_pointer

    x_min = max(0, location["x"] - 50)
    x_max = location["x"] + size["width"] + 50
    y_min = max(0, location["y"] - 50)
    y_max = location["y"] + size["height"] + 50

    for _ in range(num_movements):
        x = random.randint(x_min, x_max)
        y = random.randint(y_min, y_max)
        await pointer.move_to(x, y, smooth_soft=60, total_time=random.uniform(0.3, 0.7))

    center_x = location["x"] + size["width"] // 2
    center_y = location["y"] + size["height"] // 2
    await pointer.move_to(center_x, center_y, smooth_soft=60, total_time=0.5)


async def is_page_loaded(driver, timeout=30):
    start_time = time.time()
    while time.time() - start_time < timeout:
        ready = await driver.execute_script("return document.readyState") == "complete"
        jQuery_active = await driver.execute_script("return !window.jQuery || jQuery.active == 0")

        if ready and jQuery_active:
            return True
        time.sleep(0.5)
    return False


async def wait_for_network_idle(driver, max_connections=0, timeout=30, idle_time=0.5):
    start_time = time.time()
    while time.time() - start_time < timeout:
        active_requests = await driver.execute_script("""
            var performance = window.performance || window.mozPerformance || window.msPerformance || window.webkitPerformance || {};
            var entries = performance.getEntriesByType && performance.getEntriesByType('resource') || [];
            return entries.filter(function(entry) {
                return !entry.responseEnd;
            }).length;
        """)

        if active_requests <= max_connections:
            time.sleep(idle_time)

            active_requests = await driver.execute_script("""
                var performance = window.performance || window.mozPerformance || window.msPerformance || window.webkitPerformance || {};
                var entries = performance.getEntriesByType && performance.getEntriesByType('resource') || [];
                return entries.filter(function(entry) {
                    return !entry.responseEnd;
                }).length;
            """)

            if active_requests <= max_connections:
                time.sleep(2)
                return True

        time.sleep(0.1)

    return False


def load_csv_data(file_path):
    data = []
    with open(file_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data


def save_success_csv(data, file_path):
    def clean_for_csv(text):
        if isinstance(text, str):
            return text.replace("\n", " ").replace("\r", "").replace('"', '""')
        return text

    if not isinstance(data, list):
        data = [data]

    creator_data_path_exists = os.path.exists(file_path)
    creator_data_file_empty = creator_data_path_exists and os.path.getsize(file_path) == 0

    with open(file_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys(), quoting=csv.QUOTE_ALL)
        if not creator_data_path_exists or creator_data_file_empty:
            writer.writeheader()
        cleaned_users = [{k: clean_for_csv(v) for k, v in user.items()} for user in data]
        writer.writerows(cleaned_users)


def save_errors(*args):
    current_dir_abspath = os.path.dirname(os.path.abspath(__file__))
    errors_path = f"{current_dir_abspath}/projects_errors.csv"

    with open(errors_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([*args])


def sleep_with_progress_bar(duration):
    """Sleep for `duration` seconds, showing a progress bar."""

    interval = 10  # Set the interval to 10 seconds
    total_intervals = int(duration) // interval  # Number of full intervals
    remainder = int(duration) % interval  # Remaining time after full intervals

    console.print(f"[bold blue]Sleeping for {duration:.2f} seconds in 10-second intervals.[/bold blue]")

    for _ in tqdm(range(total_intervals), desc="Sleeping", unit="interval", ncols=100):
        time.sleep(interval)

    if remainder > 0:
        time.sleep(remainder)
        tqdm.write(f"Finished sleeping additional {remainder} seconds.")

    console.print("[bold blue]Finished sleeping.[/bold blue]")
