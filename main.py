# main.py
import random
import time

# Explicit custom module imports
from database import DB_INIT, DB_GET_WEBSITE, DB_GET_WEBSITE_RULES, DB_WEBSITE_ADD, DB_WEBMETRIC_ADD, DB_SET_SCRAPE_COMPLETE
from scraper import SC_PARSER

# This is where our story begins...
DB_INIT()


def MAIN():
  print("[SYSTEM] Booting ScrapeApe Pipeline...")

  # 1. Fetch our complete active queue snapshot array
  website_batch = DB_GET_WEBSITE()

  if not website_batch:
    print(
        "[SYSTEM] Batch completed: No websites are currently due for scheduling."
    )
    return

  print(
      f"[SYSTEM] Found {len(website_batch)} targets due for processing. Starting"
      " stream..."
  )

  # 2. Process the queue items slice
  # Using *_ allows us to cleanly loop even if the DB array returns 8 columns
  for web_site_id, url, *_ in website_batch:
    print(f"\n[EXECUTE] Processing Site ID {web_site_id}: {url}")

    # Catch all 4 items returned by your updated INNER JOIN query!
    web_rules_id, rules_id, metric_name, selector = DB_GET_WEBSITE_RULES(web_site_id)
    print(f"  -> Rule Applied: Scraping for '{metric_name}' using selector '{selector}'")

    # Route the network request straight to your scraper module
    live_title, live_metric_text = SC_PARSER(url, selector)

    # Execute database logging and mutations cleanly hidden from main
    DB_WEBSITE_ADD(url, live_title)
    DB_WEBMETRIC_ADD(web_site_id, live_metric_text, live_title, url)

    # Reset the interval countdown timer for this site
    DB_SET_SCRAPE_COMPLETE(web_site_id)
    print(f"[SUCCESS] Finished handling Site ID {web_site_id}")

    # Metering delay to emulate human browsing behaviors
    delay = random.uniform(2.0, 4.5)
    print(f"[METERING] Pausing loop for {delay:.2f} seconds...")
    time.sleep(delay)

  print("\n[SYSTEM] ScrapeApe batch sequence finalized successfully!")


#if __name__ == "__main__":
#  MAIN()