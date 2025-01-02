import os
import time
from flask import Flask, render_template, request, redirect, url_for
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
from PIL import Image
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Load environment variables from .env file
load_dotenv()

# Google Sheets API Setup
service_account_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if not service_account_path or not os.path.exists(service_account_path):
    raise FileNotFoundError("Service account file not found. Please check the path in your .env file.")

credentials = Credentials.from_service_account_file(service_account_path)
service = build('sheets', 'v4', credentials=credentials)

# Global Variables
SPREADSHEET_ID = ""
current_row = 2

# Filter criteria
EXCLUDE_KEYWORDS = ["logo", "banner", "icon", "advert", "placeholder", "blank"]
VALID_FORMATS = (".jpg", ".jpeg", ".png", ".webp")
MIN_WIDTH, MIN_HEIGHT = 200, 200  # Minimum dimensions for images
MAX_THREADS = 10  # Maximum number of concurrent threads


def is_valid_image(url, headers):
    """
    Checks if an image URL is valid and meets size requirements.
    """
    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content))
        if image.width >= MIN_WIDTH and image.height >= MIN_HEIGHT:
            return url
    except Exception:
        pass
    return None


def parse_img_tags(link):
    """
    Scraper to extract and validate image URLs.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(link, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        img_tags = soup.find_all("img")
        img_urls = [urljoin(link, img.get("src")) for img in img_tags if img.get("src")]

        # Use threading to validate images concurrently
        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            results = list(executor.map(lambda url: is_valid_image(url, headers), img_urls))

        return [url for url in results if url]
    except requests.RequestException as e:
        print(f"Error while fetching {link}: {e}")
        return []


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/set_sheet_id', methods=['POST'])
def set_sheet_id():
    global SPREADSHEET_ID
    SPREADSHEET_ID = request.form.get('sheet_id')
    return redirect(url_for('view_images'))


@app.route('/view_images', methods=['GET', 'POST'])
def view_images():
    global current_row
    if not SPREADSHEET_ID:
        return redirect(url_for('index'))

    if request.method == 'POST':
        selected_links = request.form.to_dict()
        row_data = [''] * 10  # Exactly 10 columns: F to O

        for img, value in selected_links.items():
            if value.startswith('p'):
                col_index = int(value[1]) - 1  # p1 -> F (index 0), p2 -> G (index 1)
                row_data[col_index] = img
            elif value.startswith('l'):
                col_index = int(value[1]) + 4  # l1 -> K (index 5), l2 -> L (index 6)
                row_data[col_index] = img

        row_data = row_data[:10]
        while len(row_data) < 10:
            row_data.append('')

        sheet = service.spreadsheets().values()
        range_to_update = f'Sheet1!F{current_row}:O{current_row}'
        body = {"values": [row_data]}
        sheet.update(
            spreadsheetId=SPREADSHEET_ID,
            range=range_to_update,
            valueInputOption="RAW",
            body=body
        ).execute()

        new_row = request.form.get('row_navigation', '')
        if new_row.isdigit():
            current_row = int(new_row)
        else:
            current_row += 1

        return redirect(url_for('view_images'))

    # Fetch the URL from Column D
    sheet = service.spreadsheets().values()
    result = sheet.get(spreadsheetId=SPREADSHEET_ID, range=f'Sheet1!D{current_row}').execute()
    links = result.get('values', [[]])[0]

    if not links:
        return render_template('no_link.html', current_row=current_row, no_link=True)

    # Scraper to fetch images
    images = parse_img_tags(links[0])

    # Fetch product name from Column E
    product_name_data = sheet.get(spreadsheetId=SPREADSHEET_ID, range=f'Sheet1!E{current_row}').execute()
    product_name = product_name_data.get('values', [[]])[0][0] if product_name_data.get('values', [[]])[0] else ''

    return render_template('view_images.html', images=images, current_row=current_row, product_name=product_name)


@app.route('/no_link', methods=['GET', 'POST'])
def no_link():
    if request.method == 'POST':
        new_row = request.form.get('row_number')
        if new_row.isdigit():
            global current_row
            current_row = int(new_row)
        return redirect(url_for('view_images'))

    return render_template('no_link.html', current_row=current_row)


if __name__ == '__main__':
    app.run(debug=True)
