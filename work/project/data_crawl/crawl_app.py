import os
import time
import requests
import pandas as pd
import sqlite3
from flask import Flask, render_template, request

app = Flask(__name__)

# --- 상위 폴더의 DB 경로 설정 ---
CURRENT_DIR = os.path.dirname(__file__)  # 현재 파일(crawl_app.py)이 있는 폴더: data_craw
PARENT_DIR = os.path.dirname(CURRENT_DIR) # 상위 폴더: work
DB_PATH = os.path.join(PARENT_DIR, "data", "sqldb.db")
# 결과적으로 DB_PATH -> C:\noho\work\data\sqldb.db

def search_kin(query, display=100, max_results=1000, start_date=None, end_date=None):
    """
    네이버 지식인(kin) 검색 전용 함수.
    날짜 정보가 있으면 쿼리에 포함, sort=sim(정확도순)으로 정렬.
    페이지네이션을 통해 최대 max_results 건의 데이터를 수집.
    """
    client_id = 'UGWFRw8nJK3z1B_irpX9'
    client_secret = 'tGq_GW6jBz'
    url = "https://openapi.naver.com/v1/search/kin.json"

    # 원본 쿼리 vs 실제 검색 쿼리
    original_query = query.strip()
    if start_date and end_date:
        search_query = f"{original_query} {start_date}~{end_date}"
    else:
        search_query = original_query

    headers = {
        'X-Naver-Client-Id': client_id,
        'X-Naver-Client-Secret': client_secret
    }

    all_items = []
    for start in range(1, max_results + 1, display):
        params = {
            "query": search_query,
            "display": display,
            "start": start,
            "sort": "sim"  # 정확도순
        }
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            items = data.get('items', [])
            if not items:
                break
            all_items.extend(items)
            time.sleep(0.2)  # API 호출 간격
        else:
            print("Error:", response.status_code)
            break

    df = pd.DataFrame(all_items)
    df["original_query"] = original_query
    df["search_query"] = search_query
    df["start_date"] = start_date
    df["end_date"] = end_date

    return df

def save_to_db(df, db_path=DB_PATH):
    """
    DataFrame을 SQLite DB에 저장.
    naverAPI 테이블이 없으면 생성, 있으면 append.
    """
    if df.empty:
        return

    with sqlite3.connect(db_path) as conn:
        # 테이블이 없으면 생성
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS naverAPI (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            link TEXT,
            description TEXT,
            original_query TEXT,
            search_query TEXT,
            start_date TEXT,
            end_date TEXT
        );
        """
        conn.execute(create_table_sql)
        # DF를 naverAPI 테이블에 추가
        df.to_sql("naverAPI", conn, if_exists="append", index=False)

def get_all_db(db_path=DB_PATH):
    """
    DB에 저장된 모든 데이터(naverAPI 테이블)를 가져와 DataFrame으로 반환.
    """
    with sqlite3.connect(db_path) as conn:
        # 테이블이 없을 수도 있으니 예외 처리
        try:
            df_db = pd.read_sql("SELECT * FROM naverAPI", conn)
        except:
            # 테이블이 아직 없다면 빈 DataFrame 반환
            df_db = pd.DataFrame()
    return df_db

@app.route('/', methods=['GET', 'POST'])
def index():
    # 새로 수집된 결과
    new_result_table = None
    new_count = 0
    # DB 전체 결과
    db_result_table = None
    db_count = 0

    if request.method == 'POST':
        keyword = request.form.get('keyword', '').strip()
        start_date = request.form.get('start_date', '').strip()
        end_date = request.form.get('end_date', '').strip()

        if keyword:
            # 1) 새로 검색
            df_new = search_kin(keyword, display=100, max_results=1000,
                                start_date=start_date, end_date=end_date)
            new_count = len(df_new)
            if new_count > 0:
                # 2) DB 저장
                save_to_db(df_new, db_path=DB_PATH)
                # 3) HTML 테이블 변환
                new_result_table = df_new.to_html(classes="table table-striped", index=False, escape=False)

    # DB 전체 조회
    df_db = get_all_db(db_path=DB_PATH)
    db_count = len(df_db)
    if db_count > 0:
        db_result_table = df_db.to_html(classes="table table-bordered", index=False, escape=False)

    return render_template(
        'index.html',
        new_result_table=new_result_table,
        new_count=new_count,
        db_result_table=db_result_table,
        db_count=db_count
    )

if __name__ == '__main__':
    app.run(debug=True)
