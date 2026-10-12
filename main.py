# main.py
import random
import time
from datetime import datetime

# Explicit custom module imports
from database import DB_INIT, DB_GET_WEBSITE, DB_GET_WEBSITE_RULES, DB_WEBSITE_ADD, DB_WEBMETRIC_ADD, DB_SET_SCRAPE_COMPLETE, DB_GET_RANDOM_HEADER
from scraper import SC_PARSER


# This is where our story begins...
DB_INIT()


def MAIN():
  print("[SYSTEM] Booting ScrapeApe Background Daemon Engine...")

  while True:
    print(f"\n[QUEUE] Scanning database queue at {datetime.now().strftime('%H:%M:%S')}...")
    
    # 1. Fetch our complete active queue snapshot array
    website_batch = DB_GET_WEBSITE()

    if website_batch:
      print(f"[SYSTEM] Found {len(website_batch)} targets due for processing. Starting batch stream...")

      # 2. Process the active queue items slice
      for web_site_id, url, *_ in website_batch:
        print(f"\n[EXECUTE] Processing Site ID {web_site_id}: {url}")

        # Ask the database how to scan this specific page
        web_rules_id, rules_id, metric_name, selector = DB_GET_WEBSITE_RULES(web_site_id)
        
        # 🕵️ Stealth Layer: Grab a complete randomized multi-header fingerprint dictionary profile
        active_headers = DB_GET_RANDOM_HEADER()

        # Route the network request straight to your scraper module
        live_title, live_metric_text = SC_PARSER(url, selector, active_headers)

        # Execute database logging and mutations cleanly hidden from main
        DB_WEBSITE_ADD(url, live_title)
        DB_WEBMETRIC_ADD(web_site_id, live_metric_text, live_title, url)

        # Reset the interval countdown timer for this site
        DB_SET_SCRAPE_COMPLETE(web_site_id)
        print(f"[SUCCESS] Finished handling Site ID {web_site_id}")

        # Anti-ban metering delay to emulate human browsing behaviors between loops
        delay = random.uniform(2.0, 4.5)
        print(f"[METERING] Pausing batch for {delay:.2f} seconds...")
        time.sleep(delay)
        
      print("\n[SYSTEM] Batch iteration finalized. Returning to queue wait state.")
    else:
      print("[SYSTEM] Queue clear: No websites are currently due for scheduling.")

    # 3. Dynamic Daemon Cool-off Wait State
    # Instead of slamming the disk continuously checking an empty queue, we rest for 15 seconds
    # before checking to see if any new website intervals have expired.
    print("[DAEMON] Sleeping for 15 seconds before next queue evaluation...")
    time.sleep(15)


if __name__ == "__main__":
  MAIN()