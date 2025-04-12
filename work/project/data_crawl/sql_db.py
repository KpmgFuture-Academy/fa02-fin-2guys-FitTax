import sqlite3
import os
CURRENT_DIR = os.path.dirname(__file__)  # 현재 파일(crawl_app.py)이 있는 폴더: data_craw
PARENT_DIR = os.path.dirname(CURRENT_DIR) # 상위 폴더: work
DB_PATH = os.path.join(PARENT_DIR, "data", "sqldb.db")


with sqlite3.connect(DB_PATH) as conn:
    cursor = conn.cursor()
    cursor.execute("PRAGMA integrity_check;")
    result = cursor.fetchone()
    if result[0] == "ok":
        print("Database integrity check passed.")
    else:
        print("Database integrity check failed:", result)