from datetime import datetime
from turtle import title
from unittest import result
from urllib.parse import urlparse
import sqlite3
import socket

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
            CREATE TABLE IF NOT EXISTS web_site     ( id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT UNIQUE, ip TEXT, title TEXT, interval_min INTEGER DEFAULT 60,scrapedate TEXT, createdate TEXT DEFAULT (datetime('now')), modifydate TEXT DEFAULT (datetime('now')) );
            CREATE TABLE IF NOT EXISTS rules        ( id INTEGER PRIMARY KEY AUTOINCREMENT, rule_name TEXT, css_selector TEXT, active INTEGER DEFAULT 1 );
            CREATE TABLE IF NOT EXISTS web_rules    ( id INTEGER PRIMARY KEY AUTOINCREMENT, web_site_id INTEGER NULL, metric_name TEXT, css_selector TEXT, active INTEGER DEFAULT 1, FOREIGN KEY(web_site_id) REFERENCES web_site(id) ON DELETE CASCADE);
            CREATE TABLE IF NOT EXISTS web_metrics  ( id INTEGER PRIMARY KEY AUTOINCREMENT, web_site_id INTEGER, createdate TEXT, title TEXT, metric_text TEXT,url TEXT, ip TEXT, FOREIGN KEY(web_site_id) REFERENCES web_site(id) ON DELETE CASCADE);

            -- Inserting default data all over the place!
            INSERT OR IGNORE INTO rules (rule_name, css_selector, active) VALUES ('page_title', 'title', 1);
            INSERT OR IGNORE INTO web_rules (web_site_id, metric_name, css_selector, active) VALUES (NULL, 'page_title', 'title', 1);
            INSERT OR IGNORE INTO web_site (url) VALUES ('https://toscrape.com'), ('https://httpbin.org');
        """
    )
    conn.commit()
    
  except sqlite3.Error as e:
    print(f"DB_INIT error: {e}")
  finally:
    conn.close()
    print("Initialization Successful!")


def DB_GET_WEBSITE_RULES(web_site_id):
    """Fetches a site-specific rule or falls back to the global NULL rule."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()    

    cursor.execute("""
        SELECT metric_name, css_selector FROM web_rules
        WHERE (web_site_id = ? OR web_site_id IS NULL) AND active = 1
        ORDER BY web_site_id DESC LIMIT 1
    """, (web_site_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    # Returns array or default rule if none found
    return result if result else ("page_title", "title")

 


def DB_WEBSITE_ADD(url, title):                                       # Inserts a crawled site into the database, ignoring duplicate URLs
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
            INSERT OR IGNORE INTO web_site (url, ip, title, createdate, modifydate) VALUES (?, ?, ?, ?, ?)

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



def DB_SAVE(metric_text, title, url):                                                 # Opens a connection, saves a single metric row, and closes safely.
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  domain = urlparse(url).netloc
  if domain:
      ip = socket.gethostbyname(domain)
  else:
      ip = "0.0.0.0"
  current_date = datetime.now().isoformat()

  try:
    cursor.execute(
        """
          INSERT INTO web_metrics (createdate, title, metric_text, url, ip) VALUES (?, ?, ?, ?, ?)
      """,
        (current_date, title, metric_text, url, ip),
    )
    conn.commit()

  except sqlite3.Error as e:
    print(f"DB_SAVE error: {e}")  
    conn.close()
  
