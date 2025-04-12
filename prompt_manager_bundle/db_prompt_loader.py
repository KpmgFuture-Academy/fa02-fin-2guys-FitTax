import sqlite3

DB_PATH = "prompt_bank.db"

def load_prompt_by_stage(stage: str) -> str:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT template FROM prompts WHERE stage = ?", (stage,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else "기본 프롬프트가 없습니다."