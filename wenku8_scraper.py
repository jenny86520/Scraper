import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin

def fetch_page(url, headers):
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    resp.encoding = "gbk"  # wenku8 使用 GBK 編碼
    return resp.text

def parse_text(html):
    soup = BeautifulSoup(html, "html.parser")
    content_div = soup.find("div", id="content")
    if not content_div:
        return ""
    # 去除多餘空白並保留換行
    text = content_div.get_text("\n", strip=True)
    return text

def find_next_page_url(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    next_link = soup.find("a", string=lambda s: s and "下一页" in s)
    if next_link and next_link.get("href"):
        return urljoin(base_url, next_link["href"])
    return None

def scrape_all(start_url, output_filename):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    url = start_url
    with open(output_filename, "w", encoding="utf-8") as f:
        while url:
            print(f"抓取中: {url}")
            try:
                html = fetch_page(url, headers)
            except Exception as e:
                print(f"⚠️ 無法讀取 {url}: {e}")
                break

            text = parse_text(html)
            if not text.strip():
                print("⚠️ 找不到正文，可能是防爬或頁面格式不同。")
                break

            f.write(text)
            f.write("\n\n")

            next_url = find_next_page_url(html, url)
            if not next_url:
                print("✅ 沒有下一頁，抓取完成。")
                break

            url = next_url
            time.sleep(2)  # 延遲避免被封

    print(f"\n📄 所有內容已儲存到 {output_filename}")

if __name__ == "__main__":
    start_url = "https://www.wenku8.net/novel/2/2654/102261.htm"
    output_file = "wenku8_novel.txt"
    scrape_all(start_url, output_file)
