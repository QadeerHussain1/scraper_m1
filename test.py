import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

BASE_URL = "http://books.toscrape.com/catalogue/page-{}.html"
OUTPUT_FILE = "books.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/128.0.0.0 Safari/537.36"
}

session = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
session.mount('http://', HTTPAdapter(max_retries=retries))
session.mount('https://', HTTPAdapter(max_retries=retries))

def scrape_page(url):
    print(f"Scraping: {url}")
    try:
        response = session.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"⚠️ Request failed: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    items = soup.select(".product_pod")

    data = []
    for item in items:
        name = item.select_one("h3 a").get("title", "N/A")
        price = item.select_one(".price_color").text.strip()
        availability = item.select_one(".availability").text.strip()
        data.append({"Name": name, "Price": price, "Availability": availability})

    return data

def scrape_all_pages(start_page=1, end_page=3):
    all_data = []
    for page_num in range(start_page, end_page + 1):
        page_url = BASE_URL.format(page_num)
        page_data = scrape_page(page_url)
        all_data.extend(page_data)
        time.sleep(random.uniform(1.5, 3.5))
    return all_data

def save_to_csv(data, filename):
    if not data:
        print("⚠️ No data collected!")
        return
    df = pd.DataFrame(data)
    df.drop_duplicates(inplace=True)
    df.to_csv(filename, index=False)
    print(f"✅ Data saved to {filename} ({len(df)} records).")

if __name__ == "__main__":
    data = scrape_all_pages(start_page=1, end_page=5)
    save_to_csv(data, OUTPUT_FILE)
