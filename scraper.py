# scraper.py
from bs4 import BeautifulSoup
import requests


def SC_PARSER(url, css_selector, header_value):
  """Visits a target URL and parses out content using a given CSS selector rule.

  Returns: (page_title, scraped_text)
  """
  headers = {
      "User-Agent": header_value
  }

  try:
    response = requests.get(url, headers=headers, timeout=10)

    if response.status_code == 200:
      soup = BeautifulSoup(response.text, "html.parser")

      # Scrape the dynamic target metric
      element = soup.find(css_selector)
      scraped_text = (
          element.get_text(strip=True) if element else "Target element missing"
      )

      # Extract standard metadata title
      title_tag = soup.find("title")
      page_title = title_tag.get_text(strip=True) if title_tag else "No Title"

      return page_title, scraped_text
    else:
      return (
          "HTTP Error",
          f"Server returned non-200 status: {response.status_code}",
      )

  except requests.exceptions.RequestException as e:
    return "Network Failure", f"Network transmission error: {e}"
