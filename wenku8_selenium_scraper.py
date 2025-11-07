import argparse
import os
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
import time
import random
import datetime

output_dir = "wenku8_novel"
next_btn_text = "下一页"


def get_novel_title(driver):
    """抓取小說名稱作為檔名並加上時間"""
    try:
        linkleft = driver.find_element(By.ID, "linkleft")
        a_tags = linkleft.find_elements(By.TAG_NAME, "a")
        if len(a_tags) >= 3:
            title = a_tags[2].text.strip()
            title = re.sub(r'[\\/:"*?<>|]', "", title)
        else:
            title = "novel"
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        return f"{title}_{timestamp}"
    except Exception:
        return f"novel_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}"


def find_content(driver, log, current_url, max_retry=3):
    """安全抓取正文內容（含 Cloudflare 重試）"""
    for attempt in range(1, max_retry + 1):
        chapter_name = driver.title.split("-")[0].strip()
        try:
            # Cloudflare 偵測
            if "Access denied" in driver.title or "Cloudflare" in driver.page_source:
                print(f"⚠️ Cloudflare 攔截（第 {attempt} 次重試）")
                log.write(
                    f"⚠️ Cloudflare 攔截（第 {attempt} 次重試） URL: {current_url}\n"
                )
                time.sleep(random.uniform(8, 15))
                driver.refresh()
                continue

            content_div = driver.find_element(By.ID, "content")
            text = content_div.text.strip()
            if not text:
                raise ValueError("找不到正文內容")
            return text

        except Exception as e:
            print(f"⚠️ 抓取失敗（第 {attempt} 次）：{e}")
            log.write(f"⚠️ 抓取失敗（第 {attempt} 次）【{chapter_name}】- {e}\n")
            time.sleep(random.uniform(1.5, 3))
            driver.refresh()

    return None


def scrape_all(start_url, start_page=None, end_page=None):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--lang=zh-TW")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/142.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(service=Service(), options=chrome_options)
    driver.get(start_url)
    time.sleep(random.uniform(1.5, 3))

    os.makedirs(output_dir, exist_ok=True)
    novel_title = get_novel_title(driver)
    output_filename = os.path.join(output_dir, f"{novel_title}.txt")
    log_filename = os.path.join(output_dir, f"{novel_title}_log.txt")
    print(f"📄 輸出檔案: {output_filename}")

    page_count = 1
    start_time = time.time()

    with open(output_filename, "w", encoding="utf-8") as f, open(
        log_filename, "a", encoding="utf-8"
    ) as log:
        f.writelines(f"《{novel_title}》")
        log.write(f"\n--- 開始抓取 {datetime.datetime.now()} ---\n")
        log.write(f"起始網址: {start_url}\n\n")

        # 如果指定起始頁，先跳到該頁
        if start_page and start_page > 1:
            for current_page in range(2, start_page + 1):
                try:
                    driver.find_element(By.LINK_TEXT, next_btn_text).click()
                    page_count += 1
                    time.sleep(random.uniform(1.5, 3))
                except NoSuchElementException:
                    log.write(
                        f"⚠️ 無法到達第 {start_page} 頁，從第 {current_page-1} 頁開始\n"
                    )
                    break

        # 開始抓取
        while True:
            current_url = driver.current_url

            text = find_content(driver, log, current_url)
            chapter_name = driver.title.split("-")[0].strip()

            if text:
                elapsed = time.time() - start_time
                print(f"【{chapter_name}】{current_url} | 經過 {int(elapsed)} 秒")
                f.write(f"\n\n【{chapter_name}】\n\n{text}")
            else:
                print(f"❌ 無法取得【{chapter_name}】內容，略過此頁。")
                log.write(
                    f"❌ 無法取得【{chapter_name}】內容，略過此頁。\nURL: {current_url}\n"
                )

            # 檢查是否達到結束頁
            if end_page and page_count >= end_page:
                print(f"✅ 已達指定頁數（{end_page}），結束。")
                log.write(f"✅ 已達指定頁數（{end_page}），結束。\n")
                break

            # 下一頁
            try:
                driver.find_element(By.LINK_TEXT, next_btn_text).click()
                page_count += 1
                time.sleep(1.5)
                # time.sleep(random.uniform(1.5, 3))
            except NoSuchElementException:
                print("✅ 沒有下一頁，完成。")
                log.write("✅ 沒有下一頁，完成。\n")
                break

    driver.quit()
    print(f"\n📘 小說內容：{output_filename}")
    print(f"🧾 錯誤日誌：{log_filename}")


if __name__ == "__main__":
    print("📚 轻小说文库 爬蟲啟動...")
    parser = argparse.ArgumentParser(description="轻小说文库 爬蟲")
    parser.add_argument(
        "start_url",
        help="起始網址，例如：https://www.wenku8.net/novel/2/2654/102261.htm",
    )
    parser.add_argument(
        "pages", nargs="*", type=int, help="可選：起始頁 結束頁，例如 3 10"
    )
    args = parser.parse_args()

    start_page = args.pages[0] if len(args.pages) >= 1 else None
    end_page = args.pages[1] if len(args.pages) >= 2 else None

    scrape_all(args.start_url, start_page, end_page)
