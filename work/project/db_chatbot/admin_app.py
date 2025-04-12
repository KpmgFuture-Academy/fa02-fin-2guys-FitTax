import os
import sqlite3
import shutil
import time
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# DB 경로 설정 (현재 파일의 상위 폴더 내 data 폴더에 sqldb.db 존재)
CURRENT_DIR = os.path.dirname(__file__)
PARENT_DIR = os.path.dirname(CURRENT_DIR)
DB_PATH = os.path.join(PARENT_DIR, "data", "SQLDb.db")
print(DB_PATH)

# ----- DB 정합성 검사 -----
@app.route('/admin/db_integrity')
def db_integrity():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("PRAGMA integrity_check;")
            result = cur.fetchone()[0]
            if result == "ok":
                message = "Database integrity check passed."
            else:
                message = f"Database integrity check failed: {result}"
    except Exception as e:
        message = f"Error: {e}"
    return render_template("db_integrity.html", message=message)

# ----- 테이블 및 데이터 조회 -----
@app.route('/admin/view_tables', methods=['GET', 'POST'])
def view_tables():
    error = None
    table_data = None
    selected_table = None
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [t[0] for t in cur.fetchall()]
            if request.method == 'POST':
                selected_table = request.form.get('table_name')
                if selected_table and selected_table in tables:
                    cur.execute(f"SELECT * FROM {selected_table} LIMIT 10;")
                    rows = cur.fetchall()
                    columns = [desc[0] for desc in cur.description] if cur.description else []
                    table_data = {"columns": columns, "rows": rows}
                else:
                    error = "선택한 테이블이 유효하지 않습니다."
    except Exception as e:
        error = str(e)
    return render_template("view_tables.html", tables=tables, table_data=table_data, error=error, selected_table=selected_table)

# ----- 중복 데이터 제거 -----
@app.route('/admin/duplicate_removal', methods=['GET', 'POST'])
def duplicate_removal():
    message = None
    if request.method == 'POST':
        table = request.form.get('table')
        column = request.form.get('column')
        if table and column:
            try:
                with sqlite3.connect(DB_PATH) as conn:
                    cur = conn.cursor()
                    # 중복 그룹 수 확인
                    cur.execute(f"""
                        SELECT COUNT(*) FROM (
                            SELECT {column}, COUNT(*) AS cnt 
                            FROM {table} 
                            GROUP BY {column} HAVING cnt > 1
                        );
                    """)
                    dup_groups = cur.fetchone()[0]
                    # 중복 제거: 각 그룹에서 rowid가 최소인 것만 남김
                    cur.execute(f"""
                        DELETE FROM {table} 
                        WHERE rowid NOT IN (
                            SELECT MIN(rowid) FROM {table} GROUP BY {column}
                        );
                    """)
                    conn.commit()
                    deleted = cur.rowcount
                    message = f"중복 데이터 제거 완료: {deleted} 건 삭제됨. (중복 그룹 수: {dup_groups})"
            except Exception as e:
                message = f"Error: {e}"
        else:
            message = "테이블 이름과 중복 판정 기준 컬럼을 입력하세요."
    return render_template("duplicate_removal.html", message=message)

# ----- SQL 쿼리 실행 도구 -----
@app.route('/admin/sql_query', methods=['GET', 'POST'])
def sql_query():
    """ SQL 쿼리 실행 도구 """
    tables = []
    columns_for_selected = []
    query_result = None
    query = ""
    error = None
    row_count = None
    selected_table = None

    try:
        # 먼저, DB 내 모든 테이블 목록을 가져옵니다.
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cur.fetchall()]

        # POST 요청 처리
        if request.method == 'POST':
            # 사용자가 드롭다운에서 선택한 테이블
            selected_table = request.form.get('selected_table')

            # 선택된 테이블이 있으면 해당 테이블의 컬럼 목록을 가져옵니다.
            if selected_table:
                with sqlite3.connect(DB_PATH) as conn:
                    cur = conn.cursor()
                    cur.execute(f"PRAGMA table_info({selected_table})")
                    columns_for_selected = [row[1] for row in cur.fetchall()]

            # 사용자가 입력한 쿼리
            query = request.form.get('query', '').strip()
            if query:
                with sqlite3.connect(DB_PATH) as conn:
                    cur = conn.cursor()
                    try:
                        cur.execute(query)

                        # SELECT 쿼리인 경우 결과 집합 표시
                        if query.lower().startswith("select"):
                            rows = cur.fetchall()
                            columns = [desc[0] for desc in cur.description] if cur.description else []
                            row_count = len(rows)
                            query_result = {
                                "columns": columns,
                                "rows": rows
                            }
                        else:
                            # SELECT 이외 (INSERT, UPDATE, DELETE 등)
                            conn.commit()
                            row_count = cur.rowcount
                            query_result = f"쿼리 실행 성공. 영향을 받은 행 수: {row_count}"
                    except Exception as e:
                        error = str(e)
    except Exception as e:
        error = str(e)

    return render_template(
        "sql_query.html",
        tables=tables,
        selected_table=selected_table,
        columns_for_selected=columns_for_selected,
        query=query,
        query_result=query_result,
        error=error,
        row_count=row_count
    )

# ----- 백업 및 복원 관리 -----
@app.route('/admin/backup_restore', methods=['GET', 'POST'])
def backup_restore():
    message = None
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'backup':
            try:
                backup_filename = "sqldb.db.backup_" + time.strftime("%Y%m%d_%H%M%S")
                backup_path = os.path.join(os.path.dirname(DB_PATH), backup_filename)
                shutil.copy(DB_PATH, backup_path)
                message = f"백업 완료: {backup_path}"
            except Exception as e:
                message = f"백업 오류: {e}"
        elif action == 'restore':
            if 'backup_file' not in request.files:
                message = "복원할 파일이 선택되지 않았습니다."
            else:
                file = request.files['backup_file']
                if file.filename == "":
                    message = "파일 이름이 없습니다."
                else:
                    try:
                        file.save(DB_PATH)
                        message = "복원 완료."
                    except Exception as e:
                        message = f"복원 오류: {e}"
        else:
            message = "알 수 없는 동작입니다."
    return render_template("backup_restore.html", message=message)

# ----- 로그 및 통계 -----
@app.route('/admin/logs_stats')
def logs_stats():
    stats = {}
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [t[0] for t in cur.fetchall()]
            for table in tables:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                stats[table] = count
    except Exception as e:
        stats = {"error": str(e)}
    return render_template("logs_stats.html", stats=stats)

# ----- 설정 및 사용자 관리 (플레이스홀더) -----
@app.route('/admin/settings', methods=['GET', 'POST'])
def settings():
    message = None
    if request.method == 'POST':
        # 예: 관리자 비밀번호 변경 등 설정 처리
        message = "설정이 저장되었습니다."
    return render_template("settings.html", message=message)

# ----- 관리자 대시보드 -----
@app.route('/admin')
def admin_dashboard():
    return render_template("admin.html")

@app.route('/')
def home_redirect():
    return redirect('/admin')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
