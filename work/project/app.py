from flask import Flask, render_template, request, redirect, url_for, jsonify
import subprocess
import os
import sys
import webbrowser
from threading import Timer

app = Flask(__name__)

# 프로그램 정보를 담은 딕셔너리
programs = {
    'naver_crawl': {
        'title': '네이버 지식인 크롤링',
        'path': 'data_crawl/crawl_app.py',
        'description': '네이버 지식인 데이터를 수집하여 분석할 수 있는 프로그램입니다.'
    },
    'google_review': {
        'title': '구글 앱 리뷰 크롤링',
        'path': 'google_play/googleApi_app.py',
        'description': '구글 플레이 스토어의 앱 리뷰를 수집하고 분석하는 도구입니다.'
    },
    'db_admin': {
        'title': 'DB 관리자',
        'path': 'db_chatbot/admin_app.py',
        'description': '데이터베이스 관리를 위한 관리자 도구입니다.'
    },
    'tax_knowledge': {
        'title': '세무관리 지식',
        'path': 'game/game_app.py',
        'description': '세무관리 지식과 관련된 정보를 제공하는 프로그램입니다.'
    }
}

# 폴더 및 파일 생성 함수
def create_sample_files():
    """프로그램 실행에 필요한 폴더와 샘플 파일을 생성합니다."""
    for program_id, program in programs.items():
        path = program['path']
        directory = os.path.dirname(path)
        
        # 디렉토리 생성
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            print(f"디렉토리 생성: {directory}")
        
        # 파일이 없을 경우 샘플 파일 생성
        if not os.path.exists(path):
            with open(path, 'w', encoding='utf-8') as f:
                f.write(f'''# {program['title']}
import time
import sys

def main():
    print("{program['title']} 프로그램이 실행되었습니다.")
    print("이것은 샘플 파일입니다. 실제 기능을 구현해주세요.")
    
    # 실행 시작 메시지
    for i in range(5):
        print(f"프로그램 초기화 중... {i+1}/5")
        time.sleep(0.5)
    
    print("\\n" + "="*50)
    print(f"{{program['title']}} 실행 중...")
    print("="*50 + "\\n")
    
    # 무한 루프를 방지하기 위해 잠시 후 종료 (실제 구현 시 제거)
    time.sleep(1)
    
    print("샘플 프로그램 종료")

if __name__ == "__main__":
    main()
''')
            print(f"샘플 파일 생성: {path}")


@app.route('/')
def index():
    """메인 페이지 렌더링"""
    return render_template('index.html', programs=programs)

@app.route('/run/<program_id>')
def run_program(program_id):
    """프로그램 실행 처리"""
    if program_id in programs:
        program = programs[program_id]
        path = program['path']
        
        try:
            # 현재 작업 디렉토리를 가져옴
            cwd = os.getcwd()
            # 전체 경로 생성
            full_path = os.path.join(cwd, path)
            
            # 디버깅 정보 출력
            print(f"현재 디렉토리: {cwd}")
            print(f"실행 파일 경로: {full_path}")
            print(f"파일 존재 여부: {os.path.exists(full_path)}")
            
            # 경로가 존재하는지 확인
            if not os.path.exists(full_path):
                # 파일을 찾을 수 없는 경우, 폴더 구조 문제일 수 있음
                # 필요한 디렉토리가 있는지 확인 후 생성
                directory = os.path.dirname(full_path)
                if not os.path.exists(directory):
                    os.makedirs(directory, exist_ok=True)
                    return jsonify({
                        'status': 'error', 
                        'message': f'디렉토리를 생성했습니다: {directory}. 필요한 파일을 추가하세요.'
                    })
                return jsonify({
                    'status': 'error', 
                    'message': f'파일을 찾을 수 없습니다: {path}. 파일이 존재하는지 확인하세요.'
                })
            
            # 파이썬으로 프로그램 실행
            # 현재 프로세스와 독립적으로 실행하기 위해 subprocess 사용
            python_exe = sys.executable  # 현재 실행 중인 파이썬 인터프리터 경로
            
            # 프로그램 실행 및 출력 캡처
            process = subprocess.Popen(
                [python_exe, full_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 5초 동안 기다리고 프로세스 상태 확인
            try:
                stdout, stderr = process.communicate(timeout=1)
                if process.returncode != 0:
                    # 오류가 발생한 경우
                    return jsonify({
                        'status': 'error',
                        'message': f'프로그램 실행 중 오류 발생: {stderr}'
                    })
            except subprocess.TimeoutExpired:
                # 프로세스가 계속 실행 중 - 정상으로 간주
                pass
            
            return jsonify({
                'status': 'success', 
                'message': f'{program["title"]}을(를) 실행했습니다.'
            })
            
        except Exception as e:
            return jsonify({
                'status': 'error', 
                'message': f'실행 중 오류가 발생했습니다: {str(e)}'
            })
    else:
        return jsonify({
            'status': 'error', 
            'message': '프로그램을 찾을 수 없습니다.'
        })

def open_browser():
    """기본 브라우저에서 앱 자동 실행"""
    webbrowser.open_new('http://127.0.0.1:5000/')

if __name__ == '__main__':
    # 필요한 디렉토리와 파일 생성
    create_sample_files()
    
    # 플라스크 앱이 시작된 후 브라우저 실행
    Timer(1, open_browser).start()
    # 플라스크 앱 실행
    print("="*50)
    print("플라스크 서버 시작 - http://127.0.0.1:5000/")
    print("브라우저가 자동으로 열립니다.")
    print("="*50)
    app.run(debug=True)