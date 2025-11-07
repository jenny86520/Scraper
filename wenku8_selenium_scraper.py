import argparse
import os
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from urllib.parse import quote
import time
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
            # 移除 Windows 不允許的字元
            title = re.sub(r'[\\/:"*?<>|]', "", title)
        else:
            title = "novel"

        # 加上時間
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M")
        filename = f"{title}_{timestamp}"
        return filename
    except Exception:
        return "novel"


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
        "Chrome/120.0.0.0 Safari/537.36"
    )

    service = Service()
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get(start_url)
    time.sleep(2)

    # 抓小說名稱
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
            current_page = 1
            while current_page < start_page:
                try:
                    next_btn = driver.find_element(By.LINK_TEXT, next_btn_text)
                    next_btn.click()
                    current_page += 1
                    page_count += 1
                    time.sleep(1.2)
                except NoSuchElementException:
                    print(
                        f"⚠️ 無法到達第 {start_page} 頁，從第 {current_page} 頁開始抓取"
                    )
                    log.write(
                        f"⚠️ 無法到達第 {start_page} 頁，從第 {current_page} 頁開始抓取\n"
                    )
                    break

        # 開始抓取
        while True:
            current_url = driver.current_url
            elapsed = time.time() - start_time
            chapter_name = driver.title.split("-")[0]
            print(f"📄【{chapter_name}】{current_url} | 經過時間 {int(elapsed)} 秒")

            try:
                content_div = driver.find_element(By.ID, "content")
                text = content_div.text.strip()
                if text:
                    f.write(f"\n\n【{chapter_name}】\n\n")
                    f.write(text)
                else:
                    raise ValueError("找不到正文內容")

                # 如果到達指定結束頁，停止
                if end_page and page_count >= end_page:
                    print(f"✅ 已達指定頁數（{end_page} 頁），抓取完成。")
                    log.write(f"✅ 已達指定頁數（{end_page} 頁），抓取完成。\n")
                    break

                # 嘗試下一頁
                try:
                    next_btn = driver.find_element(By.LINK_TEXT, next_btn_text)
                    next_btn.click()
                    page_count += 1
                    time.sleep(1.2)
                except NoSuchElementException:
                    print("✅ 已經是最後一頁，抓取完成。")
                    log.write("✅ 已經是最後一頁，抓取完成。\n")
                    break

            except Exception as e:
                error_msg = f"⚠️ {chapter_name}錯誤 ({type(e).__name__}): {e}"
                print(error_msg)
                log.write(f"{error_msg}\nURL: {current_url}\n\n")
                # 嘗試下一頁
                try:
                    next_btn = driver.find_element(By.LINK_TEXT, next_btn_text)
                    next_btn.click()
                    page_count += 1
                    time.sleep(1.2)
                except NoSuchElementException:
                    print("❌ 找不到下一頁按鈕，結束。")
                    log.write("❌ 找不到下一頁按鈕，結束。\n")
                    break

    driver.quit()
    print(f"\n📄 小說內容： {output_filename}")
    print(f"⛔ 錯誤日誌： {log_filename}")


if __name__ == "__main__":
    print("轻小说文库 爬蟲...")
    parser = argparse.ArgumentParser(description="轻小说文库 爬蟲")
    parser.add_argument(
        "start_url",
        help="起始網址（例如：https://www.wenku8.net/novel/2/2654/102261.htm）",
    )
    parser.add_argument(
        "pages",
        nargs="*",
        type=int,
        help="可選：起始頁 結束頁（例如 3 10，不輸入則抓到最後一頁）",
    )
    args = parser.parse_args()

    start_page = args.pages[0] if len(args.pages) >= 1 else None
    end_page = args.pages[1] if len(args.pages) >= 2 else None

    scrape_all(args.start_url, start_page, end_page)
