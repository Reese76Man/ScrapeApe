from datetime import datetime
import socket
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import requests

# Import custom functions
from database import DB_INIT, DB_SAVE

# Ensure database and table exist before running
DB_INIT()

url = "https://example.com"
headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )
}

try:
  domain = urlparse(url).netloc
  target_ip = socket.gethostbyname(domain)

  response = requests.get(url, headers=headers, timeout=10)

  if response.status_code == 200:
    soup = BeautifulSoup(response.text, "html.parser")
    title_element = soup.find("title")
    page_title = title_element.get_text(strip=True) if title_element else "N/A"
    current_time = datetime.now().isoformat()

    # Call the clean subroutine/function from database.py
    DB_SAVE(current_time, page_title, url, target_ip)

    print(f"Saved successfully!")
  else:
    print(f"Error: Status Code: {response.status_code}")

except Exception as e:
  print(f"An error occurred: {e}")

