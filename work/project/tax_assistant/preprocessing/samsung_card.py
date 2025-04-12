"""
삼성카드 데이터 전처리 모듈
"""
import streamlit as st
from tax_assistant.preprocessing.lotte_card import preprocess_lotte_card

def preprocess_samsung_card(file_path):
    """
    삼성카드 데이터 전처리 함수
    
    Args:
        file_path: 삼성카드에서 다운로드한 엑셀 파일 경로
    
    Returns:
        전처리된 데이터프레임
    """
    try:
        # 현재는 롯데카드와 동일한 전처리 로직 사용 
        # (추후 삼성카드 데이터 포맷에 맞게 수정 필요)
        df = preprocess_lotte_card(file_path)
        
        if df is not None:
            # 삼성카드 특화 처리 로직 (필요시 추가)
            # 예: 특정 컬럼명 변경, 추가 정보 처리 등
            pass
        
        return df
        
    except Exception as e:
        st.error(f"삼성카드 데이터 전처리 중 오류가 발생했습니다: {str(e)}")
        return None