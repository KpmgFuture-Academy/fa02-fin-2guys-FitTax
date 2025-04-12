import streamlit as st
import sqlite3

DB_PATH = "prompt_bank.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stage TEXT NOT NULL,
            title TEXT NOT NULL,
            template TEXT NOT NULL,
            description TEXT
        )
    """)
    conn.commit()
    conn.close()

def fetch_prompts():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, stage, title, template, description FROM prompts")
    rows = cursor.fetchall()
    conn.close()
    return rows

def add_prompt(stage, title, template, description):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO prompts (stage, title, template, description) VALUES (?, ?, ?, ?)",
                   (stage, title, template, description))
    conn.commit()
    conn.close()

def delete_prompt(prompt_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM prompts WHERE id = ?", (prompt_id,))
    conn.commit()
    conn.close()

# Streamlit UI
st.set_page_config(page_title="프롬프트 관리자", layout="wide")
st.title("🛠 전략 프롬프트 관리 대시보드")

init_db()
st.markdown("새 프롬프트 추가")

with st.form("add_prompt_form"):
    stage = st.text_input("프레임워크 단계 (예: 문제 정의)")
    title = st.text_input("영문 제목 (예: Problem Framing)")
    template = st.text_area("프롬프트 템플릿 (LangChain용)")
    description = st.text_area("설명 (선택)")
    submitted = st.form_submit_button("추가하기")
    if submitted:
        add_prompt(stage, title, template, description)
        st.success("프롬프트가 추가되었습니다.")

st.markdown("---")
st.subheader("📋 현재 프롬프트 목록")

prompts = fetch_prompts()
for pid, stage, title, template, desc in prompts:
    with st.expander(f"{stage} / {title}"):
        st.code(template, language="text")
        if desc:
            st.markdown(f"📝 {desc}")
        if st.button("삭제", key=f"delete_{pid}"):
            delete_prompt(pid)
            st.experimental_rerun()