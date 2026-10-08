# database.py
import sqlite3
import socket
from datetime import datetime
from urllib.parse import urlparse

DB_NAME = "scrapeape.db"


def DB_INIT():                                                                # Create Database Structure (if not exists)
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()

  try:
    cursor.executescript(
        """
            -- Got this DB on lock!
            PRAGMA foreign_keys = ON;
            
            -- Table Creation Time!
            CREATE TABLE IF NOT EXISTS web_site       ( id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT UNIQUE, ip TEXT, title TEXT, interval_min INTEGER DEFAULT 60,scrapedate TEXT, createdate TEXT DEFAULT (datetime('now')), modifydate TEXT DEFAULT (datetime('now')) );
            CREATE TABLE IF NOT EXISTS rules          ( id INTEGER PRIMARY KEY AUTOINCREMENT, rule_name TEXT UNIQUE, css_selector TEXT, active INTEGER DEFAULT 1 );
            CREATE TABLE IF NOT EXISTS web_rules      ( id INTEGER PRIMARY KEY AUTOINCREMENT, web_site_id INTEGER NULL, rules_id INTEGER NOT NULL, active INTEGER DEFAULT 1, FOREIGN KEY(web_site_id) REFERENCES web_site(id) ON DELETE CASCADE, FOREIGN KEY(rules_id) REFERENCES rules(id) ON DELETE CASCADE);
            CREATE TABLE IF NOT EXISTS web_metrics    ( id INTEGER PRIMARY KEY AUTOINCREMENT, web_site_id INTEGER, rules_id INTEGER, createdate TEXT DEFAULT (datetime('now')), title TEXT, metric_text TEXT,url TEXT, ip TEXT, FOREIGN KEY(web_site_id) REFERENCES web_site(id) ON DELETE CASCADE, FOREIGN KEY(rules_id) REFERENCES rules(id) ON DELETE CASCADE);
            CREATE TABLE IF NOT EXISTS header_groups  ( id INTEGER PRIMARY KEY AUTOINCREMENT, group_name TEXT UNIQUE, active INTEGER DEFAULT 1);
            CREATE TABLE IF NOT EXISTS web_headers    ( id INTEGER PRIMARY KEY AUTOINCREMENT, web_site_id INTEGER NULL, header_groups_id INTEGER NOT NULL, header_name TEXT, header_value TEXT, createdate TEXT DEFAULT (datetime('now')), active INTEGER DEFAULT 1, FOREIGN KEY(web_site_id) REFERENCES web_site(id) ON DELETE CASCADE);
            
            -- Indexes will make this faster than a quantum computer... what? You calling me a liar?
            CREATE INDEX IF NOT EXISTS ix_web_site_scrapedate ON web_site(scrapedate);

            -- Inserting default/test data all over the place!
            INSERT OR IGNORE INTO web_site (url) SELECT 'https://toscrape.com' UNION ALL SELECT 'https://httpbin.org' WHERE NOT EXISTS (SELECT 1 FROM web_site);
            INSERT OR IGNORE INTO rules (rule_name, css_selector) SELECT 'page_title', 'title' WHERE NOT EXISTS (SELECT 1 FROM rules);
            INSERT OR IGNORE INTO web_rules (web_site_id, rules_id) SELECT NULL, last_insert_rowid() WHERE NOT EXISTS (SELECT 1 FROM web_rules);
            INSERT OR IGNORE INTO header_groups (group_name) SELECT 'WIN_CHROME' UNION ALL SELECT 'MAC_SAFARI' UNION ALL SELECT 'WIN_FIREFOX' UNION ALL SELECT 'LINUX_CHROME' WHERE NOT EXISTS (SELECT 1 FROM header_groups); 

            INSERT OR IGNORE INTO web_headers (web_site_id, header_groups_id, header_name, header_value)
            SELECT NULL, header_groups.id, 'User-Agent', CASE group_name
                                            WHEN 'WIN_CHROME' THEN 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
                                            WHEN 'MAC_SAFARI' THEN 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15'
                                            WHEN 'WIN_FIREFOX' THEN 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0'
                                            WHEN 'LINUX_CHROME' THEN 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
                                           END
            FROM header_groups
            WHERE NOT EXISTS (SELECT 1 FROM web_headers);
        """
    )
    conn.commit()
    
  except sqlite3.Error as e:
    print(f"DB_INIT error: {e}")
  finally:
    conn.close()
    print("Initialization Successful!")



def DB_GET_WEBSITE_RULES(web_site_id):                                 #Fetches a site-specific rule or falls back to the global NULL rule
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()    

    cursor.execute( """
                        SELECT web_rules.id as web_rules_id, rules.id as rules_id, rule_name, css_selector FROM web_rules
                        INNER JOIN rules ON web_rules.rules_id = rules.id
                        WHERE (web_site_id = ? OR web_site_id IS NULL) AND rules.active = 1 AND web_rules.active = 1
                        ORDER BY web_site_id DESC
                    """, (web_site_id,)
                   )
    
    result = cursor.fetchone()
    conn.close()
    
    # Returns array or default rule if none found
    return result if result else ("page_title", "title")



def DB_GET_WEBSITE():                                                 # Fetches all websites due for processing from the database
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    query = """
        SELECT id as web_site_id, url, scrapedate, interval_min, createdate, modifydate, ip, title FROM web_site
        WHERE scrapedate IS NULL OR scrapedate < datetime('now', '-1 minute')
        ORDER BY scrapedate DESC;
    """
    try:
        cursor.execute(query)
        return cursor.fetchall()

    except sqlite3.Error as e:
        print(f"[DB] Error querying website batch: {e}")
        return []

    finally:
        conn.close()


def DB_WEBSITE_ADD(url, title):                                        # Inserts a crawled site into the database, ignoring duplicate URLs
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()  
  current_date = datetime.now().isoformat()

  try:
    domain = urlparse(url).netloc
    if domain:
        ip = socket.gethostbyname(domain)
    else:
        ip = "0.0.0.0"
  except Exception:
    ip = "0.0.0.0"
    
  try:
    cursor.execute(
        """
            INSERT INTO web_site (url, ip, title, createdate, modifydate) VALUES (?, ?, ?, ?, ?)
              ON CONFLICT(url) DO UPDATE SET ip = excluded.ip, title = excluded.title,modifydate = excluded.modifydate
        """,
        (url, ip, title, current_date, current_date),
    )
    conn.commit()
    print(f"Website added/update: {url}")

  except sqlite3.Error as e:
    print(f"DB_WEBSITE_ADD error: {e}")
  finally:
    conn.close()



def DB_WEBMETRIC_ADD(web_site_id, metric_text, title, url):              # Opens a connection, saves a single metric row, and closes safely.
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  domain = urlparse(url).netloc

  if domain:
      ip = socket.gethostbyname(domain)
  else:
      ip = "0.0.0.0"
  current_date = datetime.now().isoformat()

  try:
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute(
        """
          INSERT INTO web_metrics (web_site_id, createdate, title, metric_text, url, ip) VALUES (?, ?, ?, ?, ?, ?)
      """,
        (web_site_id, current_date, title, metric_text, url, ip),
    )
    conn.commit()

  except sqlite3.Error as e:
    print(f"DB_WEBMETRIC_ADD error: {e}")    
  finally:
    conn.close()



def DB_SET_SCRAPE_COMPLETE(web_site_id):                                 # Resets the countdown timer for a specific domain record
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()

  try:
    cursor.execute(
        "UPDATE web_site SET scrapedate = datetime('now') WHERE id = ?",
        (web_site_id,),
    )
    conn.commit()
  except sqlite3.Error as e:
    print(f"[DB] Error updating scrapedate: {e}")
  finally:
    conn.close()



def DB_GET_RANDOM_USER_AGENT():                                     # Extracts a single active User-Agent string chosen entirely at random from the DB
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()

  try:
    # Only grab header_value since that's all our network parser needs!
    cursor.execute("SELECT header_value FROM web_headers WHERE active = 1 ORDER BY random() LIMIT 1;")
    result = cursor.fetchone()

  except sqlite3.Error as e:
    print(f"DB_GET_RANDOM_USER_AGENT error: {e}")
    result = None
  finally:
    conn.close()      
  
  # Returns the raw text string directly, falling back to a clean default on any miss
  return result[0] if result else 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

