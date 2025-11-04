from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, WebDriverException
import time
import datetime


def scrape_all(start_url, output_filename, log_filename):
    # 設定 Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 不開視窗（除錯時可註解掉）
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--lang=zh-TW")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    service = Service()  # 自動尋找 chromedriver
    driver = webdriver.Chrome(service=service, options=chrome_options)

    driver.get(start_url)
    time.sleep(2)

    page_count = 1  # 用來記錄第幾頁
    with open(output_filename, "w", encoding="utf-8") as f, open(
        log_filename, "a", encoding="utf-8"
    ) as log:
        log.write(f"\n--- 開始抓取 {datetime.datetime.now()} ---\n")

        while True:
            current_url = driver.current_url
            print(f"📄 第 {page_count} 頁: {current_url}")

            try:
                # 嘗試抓小說正文
                content_div = driver.find_element(By.ID, "content")
                text = content_div.text.strip()
                if text:
                    f.write(f"\n\n=== 第 {page_count} 頁 ===\n\n")
                    f.write(text + "\n")
                else:
                    raise ValueError("找不到正文內容")

                # 找下一頁
                try:
                    next_button = driver.find_element(By.LINK_TEXT, "下一页")
                    next_button.click()
                    page_count += 1
                    time.sleep(2)
                except NoSuchElementException:
                    print("✅ 已經是最後一頁。")
                    log.write("✅ 已經是最後一頁。\n")
                    break

            except Exception as e:
                # 紀錄錯誤訊息與頁面
                error_msg = (
                    f"⚠️ 第 {page_count} 頁發生錯誤 ({type(e).__name__}): {str(e)}"
                )
                print(error_msg)
                log.write(f"{error_msg}\nURL: {current_url}\n\n")
                # 不中斷，嘗試繼續下一頁（可選）
                try:
                    next_button = driver.find_element(By.LINK_TEXT, "下一页")
                    next_button.click()
                    page_count += 1
                    time.sleep(2)
                except NoSuchElementException:
                    print("❌ 找不到下一頁按鈕，結束。")
                    log.write("❌ 找不到下一頁按鈕，結束。\n")
                    break

    driver.quit()
    print(f"\n📄 抓取完成，內容儲存於 {output_filename}")
    print(f"🪵 錯誤日誌儲存於 {log_filename}")


if __name__ == "__main__":
    start_url = "https://www.wenku8.net/novel/2/2654/102261.htm"
    output_file = "wenku8_novel.txt"
    log_file = "wenku8_log.txt"
    scrape_all(start_url, output_file, log_file)
