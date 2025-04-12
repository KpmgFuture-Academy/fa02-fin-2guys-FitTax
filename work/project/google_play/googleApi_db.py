import sqlite3
import pandas as pd
import os

# 데이터베이스 파일명
db_name = 'SQLDb.db'

# 현재 스크립트 파일이 있는 폴더 경로
current_script_dir = os.path.dirname(os.path.abspath(__file__))

# 상위 폴더 경로 (상대 경로)
parent_dir = os.path.join(current_script_dir, '..')

# 상위 폴더 내의 data 폴더 경로 (SQLdb 저장 위치 - 상대 경로)
db_data_folder = os.path.join(parent_dir, 'data')

# data 폴더가 없으면 생성 (SQLdb 저장 위치)
if not os.path.exists(db_data_folder):
    os.makedirs(db_data_folder)
    print(f"'{db_data_folder}' 폴더 생성 완료 (SQLdb 저장 위치).")

# 데이터베이스 파일의 전체 경로
db_path = os.path.join(db_data_folder, db_name)

# 데이터 폴더 경로 (CSV 파일 위치 - 상대 경로)
csv_data_folder = os.path.join(current_script_dir, 'data')

# 첫 번째 CSV 파일 정보 (현재 스크립트 폴더 내의 data 폴더 - 상대 경로)
csv_file_google_play_id = os.path.join(csv_data_folder, 'google_play_id.csv')
table_name_google_play_id = 'google_play_id_table'  # 생성할 테이블 이름

# 두 번째 CSV 파일 정보 (현재 스크립트 폴더 내의 data 폴더 - 상대 경로)
csv_file_all_reviews = os.path.join(csv_data_folder, 'all_korean_app_reviews1.csv')
table_name_all_reviews = 'all_korean_app_reviews1_table'  # 생성할 테이블 이름

try:
    # SQLite 데이터베이스 연결 (새로운 경로 사용)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    print(f"데이터베이스 연결 성공: {db_path}")

    # 첫 번째 CSV 파일 읽기 (pandas 사용)
    try:
        df_google_play_id = pd.read_csv(csv_file_google_play_id, encoding='utf-8')
        print(f"'{csv_file_google_play_id}' 파일 읽기 완료.")

        # 데이터프레임을 SQLite 테이블로 저장
        df_google_play_id.to_sql(table_name_google_play_id, conn, if_exists='replace', index=False)
        print(f"'{table_name_google_play_id}' 테이블 생성 및 데이터 저장 완료.")

    except FileNotFoundError:
        print(f"오류: '{csv_file_google_play_id}' 파일을 찾을 수 없습니다.")
    except Exception as e:
        print(f"오류: '{csv_file_google_play_id}' 파일 처리 중 오류 발생 - {e}")

    # 두 번째 CSV 파일 읽기 (pandas 사용)
    try:
        df_all_reviews = pd.read_csv(csv_file_all_reviews, encoding='utf-8')
        print(f"'{csv_file_all_reviews}' 파일 읽기 완료.")

        # 데이터프레임을 SQLite 테이블로 저장
        df_all_reviews.to_sql(table_name_all_reviews, conn, if_exists='replace', index=False)
        print(f"'{table_name_all_reviews}' 테이블 생성 및 데이터 저장 완료.")

    except FileNotFoundError:
        print(f"오류: '{csv_file_all_reviews}' 파일을 찾을 수 없습니다.")
    except Exception as e:
        print(f"오류: '{csv_file_all_reviews}' 파일 처리 중 오류 발생 - {e}")

    # 변경 사항 저장
    conn.commit()
    print(f"데이터베이스 '{db_name}'에 모든 테이블 생성 및 데이터 저장 완료 (경로: {db_path}).")

except sqlite3.Error as e:
    print(f"SQLite 데이터베이스 오류 발생: {e}")

finally:
    # 데이터베이스 연결 닫기
    if conn:
        conn.close()
        print("데이터베이스 연결이 닫혔습니다.")