import os
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime


URL = "https://www.cse.lk/equity/trade-summary"  # update if your exact page differs
# Save inside the repo so GitHub Actions can upload/commit it
BASE_DIR = Path(os.environ.get("GITHUB_WORKSPACE", Path.cwd()))
DOWNLOAD_DIR = str(BASE_DIR / "data")   # will create repo/data/



def make_driver(download_dir: str) -> webdriver.Chrome:
    os.makedirs(download_dir, exist_ok=True)

    options = webdriver.ChromeOptions()
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "profile.default_content_settings.popups": 0,
        "download_restrictions": 0,

    }
    options.add_experimental_option("prefs", prefs)

    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=options)

    return driver


def click_show_all_rows(driver: webdriver.Chrome):
    wait = WebDriverWait(driver, 30)

    show_btn = wait.until(EC.element_to_be_clickable((
        By.XPATH,
        "//span[normalize-space()='Show']/following::button[1]"
    )))
    show_btn.click()

    candidates = ["All", "1000", "500", "250", "100"]
    for text in candidates:
        try:
            opt = wait.until(EC.element_to_be_clickable((
                By.XPATH,
                f"//*[self::button or self::div or self::li or self::a][normalize-space()='{text}']"
            )))
            opt.click()
            print("Selected rows:", text)
            time.sleep(4)  # give table time to reload
            return
        except Exception:
            continue

    show_btn.click()



def snapshot_files(download_dir: str):
    p = Path(download_dir)
    p.mkdir(parents=True, exist_ok=True)
    return {f.name for f in p.iterdir() if f.is_file()}

def wait_for_new_download(download_dir: str, before_set, timeout: int = 180):
    """Wait for a new file to appear and for .crdownload to finish."""
    p = Path(download_dir)
    end = time.time() + timeout

    while time.time() < end:
        current = {f.name for f in p.iterdir() if f.is_file()}

        # Any brand new file?
        new_files = list(current - before_set)

        # If Chrome is still downloading, you'll see .crdownload
        downloading = [f for f in current if f.endswith(".crdownload")]

        if new_files and not downloading:
            # return newest new file path
            new_paths = [p / name for name in new_files]
            newest = max(new_paths, key=lambda x: x.stat().st_mtime)
            return str(newest)

        time.sleep(0.5)

    raise TimeoutError("Download did not appear/finish in the download folder.")




def download_xlsx(driver, download_dir: str):
    wait = WebDriverWait(driver, 30)

    before_set = snapshot_files(download_dir)

    # open download dropdown
    download_btn = wait.until(EC.element_to_be_clickable((
        By.CSS_SELECTOR,
        "div.download-dropdown button[aria-label='Download options']"
    )))
    driver.execute_script("arguments[0].click();", download_btn)
    print("Clicked download menu")

    time.sleep(1)  # allow menu to appear

    # click XLSX option
    xlsx_item = wait.until(EC.element_to_be_clickable((
        By.XPATH,
        "//*[self::button or self::a or self::li or self::div][normalize-space()='XLS']"
    )))
    print("Found XLSX option:", xlsx_item.text)

    driver.execute_script("arguments[0].click();", xlsx_item)
    print("Clicked XLSX")

    return wait_for_new_download(download_dir, before_set, timeout=180)


def finalize_download(downloaded_path: str, download_dir: str) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    target = os.path.join(download_dir, f"cse_trade_summary_{today}.xls")

    if os.path.exists(target):
        os.remove(target)

    os.rename(downloaded_path, target)
    return target




def main():
    print("Download dir:", DOWNLOAD_DIR)
    
    driver = make_driver(DOWNLOAD_DIR)
    try:
        driver.get(URL)

        # Give the page a moment to render table (JS heavy pages sometimes need a beat)
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.trade-summary-table"))
        )

        click_show_all_rows(driver)
        time.sleep(2)  # allow table to reload fully

        rows = driver.find_elements(By.CSS_SELECTOR, "div.trade-summary-table table tbody tr")
        print("Row count before download:", len(rows))


       file_path = download_xlsx(driver, DOWNLOAD_DIR)
       file_path = finalize_download(file_path, DOWNLOAD_DIR)
       print("Downloaded:", file_path)



    finally:
        driver.quit()


if __name__ == "__main__":
    main()
