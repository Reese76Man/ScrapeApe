import sqlite3

DB_NAME = "scrapeape.db"


def DB_INIT():
  """Creates the database and table if they don't exist."""
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute(
      """
        CREATE TABLE IF NOT EXISTS page_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            title TEXT,
            url TEXT,
            ip TEXT
        )
    """
  )
  conn.commit()
  conn.close()


def DB_SAVE(timestamp, title, url, ip):
  """Opens a connection, saves a single metric row, and closes safely."""
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute(
      """
        INSERT INTO page_metrics (timestamp, title, url, ip) 
        VALUES (?, ?, ?, ?)
    """,
      (timestamp, title, url, ip),
  )
  conn.commit()
  conn.close()
