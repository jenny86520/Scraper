from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, WebDriverException
import time

def scrape_all(start_url, output_filename):
    # 設定 Selenium Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 不開視窗
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--lang=zh-TW")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                "AppleWebKit/537.36 (KHTML, like Gecko) "
                                "Chrome/120.0.0.0 Safari/537.36")

    # 啟動 ChromeDriver（需先安裝）
    service = Service()  # 自動尋找 ChromeDriver
    driver = webdriver.Chrome(service=service, options=chrome_options)

    driver.get(start_url)
    time.sleep(2)

    with open(output_filename, "w", encoding="utf-8") as f:
        while True:
            try:
                # 找小說正文
                content_div = driver.find_element(By.ID, "content")
                text = content_div.text.strip()
                if text:
                    f.write(text + "\n\n")
                else:
                    print("⚠️ 找不到正文文字。")

                # 嘗試找到「下一页」按鈕
                try:
                    next_button = driver.find_element(By.LINK_TEXT, "下一页")
                    next_button.click()
                    print("➡️ 進入下一頁...")
                    time.sleep(2)
                except NoSuchElementException:
                    print("✅ 已經是最後一頁，抓取完成。")
                    break

            except WebDriverException as e:
                print(f"⚠️ 錯誤: {e}")
                break

    driver.quit()
    print(f"\n📄 所有內容已儲存至 {output_filename}")

if __name__ == "__main__":
    start_url = "https://www.wenku8.net/novel/2/2654/102261.htm"
    output_file = "wenku8_novel.txt"
    scrape_all(start_url, output_file)
