"""
유틸리티 함수 모듈
"""
import os
import tempfile
from datetime import datetime
import pandas as pd

def save_uploaded_file(uploaded_file):
    """
    업로드된 파일을 임시 디렉토리에 저장
    
    Args:
        uploaded_file: Streamlit 파일 업로더 객체
        
    Returns:
        저장된 파일의 경로
    """
    try:
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
            temp_file.write(uploaded_file.getbuffer())
            file_path = temp_file.name
        
        return file_path
    except Exception as e:
        print(f"파일 저장 중 오류 발생: {str(e)}")
        return None

def cleanup_temp_file(file_path):
    """
    임시 파일 삭제
    
    Args:
        file_path: 삭제할 파일 경로
    """
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print(f"파일 삭제 중 오류 발생: {str(e)}")

def get_current_tax_period():
    """
    현재 날짜 기준 과세기간 반환
    
    Returns:
        과세기간 문자열
    """
    now = datetime.now()
    year = now.year
    
    if now.month <= 6:
        return f"{year}년 1기 (1월~6월)"
    else:
        return f"{year}년 2기 (7월~12월)"

def get_tax_due_date(tax_period):
    """
    과세기간에 따른 신고 기한 반환
    
    Args:
        tax_period: 과세기간 문자열
        
    Returns:
        신고 기한 문자열
    """
    if "1기" in tax_period:
        year = int(tax_period.split('년')[0])
        return f"{year}년 7월 25일"
    else:
        year = int(tax_period.split('년')[0]) + 1
        return f"{year}년 1월 25일"

def format_currency(amount):
    """
    금액 형식 변환
    
    Args:
        amount: 형식화할 금액
        
    Returns:
        형식화된 금액 문자열
    """
    return f"{amount:,.0f}원"

def export_to_csv(df, filename=None):
    """
    데이터프레임을 CSV로 변환
    
    Args:
        df: 변환할 데이터프레임
        filename: 파일명 (기본값: 현재 날짜 기반)
        
    Returns:
        CSV 바이트 데이터
    """
    if filename is None:
        filename = f"부가세신고용_{datetime.now().strftime('%Y%m%d')}.csv"
    
    return df.to_csv(index=False).encode('utf-8-sig'), filename