from datetime import datetime
import sqlite3
from bs4 import BeautifulSoup
import requests

# 1. Connect to SQLite database (creates 'metrics.db' if it doesn't exist)
conn = sqlite3.connect("metrics.db")
cursor = conn.cursor()

# Create a table for our metrics
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS page_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        title TEXT
    )
"""
)

# 2. Fetch the web page
url = "https://example.com"
response = requests.get(url, timeout=10)

if response.status_code == 200:
  # 3. Parse the HTML
  soup = BeautifulSoup(response.text, "html.parser")
  page_title = soup.find("h1").get_text(strip=True)
  current_time = datetime.now().isoformat()

  # 4. Insert metrics into the database
  cursor.execute(
      "INSERT INTO page_metrics (timestamp, title) VALUES (?, ?)",
      (current_time, page_title),
  )
  conn.commit()
  print(f"Saved metric at {current_time}: {page_title}")

# Close the database connection
conn.close()
