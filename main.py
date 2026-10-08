# main.py
import random
import time

# Explicit custom module imports
from database import (
    DB_INIT,
    DB_GET_DUE_WEBSITES,
    DB_GET_WEBSITE_RULES,
    DB_WEBSITE_ADD,
    DB_WEBMETRIC_ADD,
    DB_SET_SCRAPE_COMPLETE,
)
from scraper import parse_page_element


def main():
  print("[SYSTEM] Booting ScrapeApe Pipeline...")

  # 1. Self-heal and initialize infrastructure
  DB_INIT()

  # 2. Extract our due target batch array snapshot
  due_batch = DB_GET_DUE_WEBSITES()

  if not due_batch:
    print(
        "[SYSTEM] Batch completed: No websites are currently due for scheduling."
    )
    return

  print(
      f"[SYSTEM] Found {len(due_batch)} targets due for processing. Starting"
      " stream..."
  )

  # 3. Process the queue slice
  for site_id, url in due_batch:
    print(f"\n[EXECUTE] Processing Site ID {site_id}: {url}")

    # Ask the database how to scan this specific page
    metric_name, selector = DB_GET_WEBSITE_RULES(site_id)

    # Route straight to the scraper module
    live_title, live_metric_text = parse_page_element(url, selector)

    # Execute database double-duty mutations and logs completely hidden from main
    DB_WEBSITE_ADD(url, live_title)
    DB_WEBMETRIC_ADD(site_id, live_metric_text, live_title, url)

    # Update state: reset interval clock window
    DB_SET_SCRAPE_COMPLETE(site_id)
    print(f"[SUCCESS] Finished handling Site ID {site_id}")

    # Metering delay between sites
    delay = random.uniform(2.0, 4.5)
    print(f"[METERING] Pausing loop for {delay:.2f} seconds...")
    time.sleep(delay)

  print("\n[SYSTEM] ScrapeApe batch sequence finalized successfully!")


if __name__ == "__main__":
  main()