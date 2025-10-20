import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# ---------------------------------
# CONFIGURATION
# ---------------------------------
BASE_URL = "http://books.toscrape.com/catalogue/page-{}.html"
GOOGLE_SHEET_NAME = "scraped_data"  # the name for your sheet
CREDS_FILE = "google_creds.json"    # your credentials file

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/128.0.0.0 Safari/537.36"
}

# Retry setup
session = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
session.mount('http://', HTTPAdapter(max_retries=retries))
session.mount('https://', HTTPAdapter(max_retries=retries))


# ---------------------------------
# SCRAPE ONE PAGE
# ---------------------------------
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


# ---------------------------------
# SCRAPE MULTIPLE PAGES
# ---------------------------------
def scrape_all_pages(start_page=1, end_page=3):
    all_data = []
    for page_num in range(start_page, end_page + 1):
        page_url = BASE_URL.format(page_num)
        page_data = scrape_page(page_url)
        all_data.extend(page_data)
        time.sleep(random.uniform(1.5, 3.5))
    return all_data


# ---------------------------------
# SAVE TO GOOGLE SHEET (AUTO-CREATE)
# ---------------------------------
def save_to_google_sheet(data, sheet_name):
    if not data:
        print("⚠️ No data collected!")
        return

    df = pd.DataFrame(data)
    df.drop_duplicates(inplace=True)

    # Google Sheets authorization
    scope = ["https://www.googleapis.com/auth/spreadsheets",
             "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("google_creds.json", scope)
    # creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, scope)
    client = gspread.authorize(creds)

    sheet = client.create("Test Sheet Created by Script")

    print("✅ Created:", sheet.url)
    try:
        # Try opening an existing sheet
        spreadsheet = client.open(sheet_name)
        print(f"✅ Found existing Google Sheet: {sheet_name}")
    except gspread.SpreadsheetNotFound:
        # Create new sheet if not found
        spreadsheet = client.create(sheet_name)
        print(f"🆕 Created new Google Sheet: {sheet_name}")

        # Optional: share it with your own Google account so you can see it in Drive
        spreadsheet.share("your_email@gmail.com", perm_type='user', role='writer')

    # Access the first worksheet
    sheet = spreadsheet.sheet1
    sheet.clear()

    # Write headers and data
    sheet.insert_row(df.columns.tolist(), 1)
    for i, row in df.iterrows():
        sheet.insert_row(row.tolist(), i + 2)

    print(f"✅ Data uploaded to Google Sheet: {sheet_name} ({len(df)} records)")


# ---------------------------------
# MAIN
# ---------------------------------
if __name__ == "__main__":
    data = scrape_all_pages(start_page=1, end_page=5)
    save_to_google_sheet(data, GOOGLE_SHEET_NAME)
