"""
롯데카드 데이터 전처리 모듈
"""
import pandas as pd
import streamlit as st
from datetime import datetime
import re

# 상수 정의
DATE_PATTERNS = ['일자', '날짜', 'date', '승인일', '이용일', '거래일']
AMOUNT_PATTERNS = ['금액', '합계', 'amount', '이용금액', '결제금액', '거래금액']
VAT_PATTERNS = ['부가세', '부가가치세', 'vat', '세액', '세금']
MERCHANT_PATTERNS = ['가맹점', '상호', '업체', 'store', '이용처', '가맹점명']
APPROVAL_PATTERNS = ['승인번호', '승인', 'approval', '카드승인번호']
CATEGORY_PATTERNS = ['구분', '용도', '유형', 'type', '사용구분', '카테고리']

# 카테고리 분류 관련 상수
MERCHANT_CATEGORY_MAP = {
    # 식비
    "스타벅스": "식비",
    "맥도날드": "식비",
    "베이커리": "식비",
    "카페": "식비",
    "식당": "식비",
    "음식점": "식비",
    "커피": "식비",
    "비어": "식비",
    "피자": "식비",
    "치킨": "식비",
    "분식": "식비",
    "호프": "식비",
    "뷔페": "식비",
    "김밥": "식비",
    "떡볶이": "식비",
    
    # 교통비
    "카카오": "교통비",
    "주유소": "교통비",
    "택시": "교통비",
    "대리운전": "교통비",
    "주차장": "교통비",
    "철도": "교통비",
    "고속도로": "교통비",
    "버스": "교통비",
    "지하철": "교통비",
    
    # 사무용품
    "문구": "사무용품",
    "프린터": "사무용품",
    "복사": "사무용품",
    "오피스": "사무용품",
    "컴퓨터": "사무용품",
    
    # 기타 카테고리는 필요에 따라 추가
}

# 카테고리별 부가세 공제 가능 여부
VAT_DEDUCTIBLE_MAP = {
    "식비": True,        # 업무 관련 식비는 일부 공제 가능
    "교통비": True,      # 업무용 교통비는 공제 가능
    "사무용품": True,    # 업무용 사무용품은 공제 가능
    "통신비": True,      # 업무용 통신비는 공제 가능
    "광고홍보비": True,  # 광고홍보비는 공제 가능
    "임대료": True,      # 사업장 임대료는 공제 가능
    "접대비": False,     # 접대비는 부가세 공제 제한적
    "여행숙박": False,   # 개인적 여행숙박은 공제 불가
    "의료비": False,     # 의료비는 공제 불가
    "복리후생": True,    # 직원 복리후생은 공제 가능
    "기타": True         # 기타는 기본적으로 공제 가능으로 설정
}

# 카테고리 분류 함수
def classify_merchant_category(merchant_name):
    """
    가맹점명을 기준으로 카테고리 분류
    """
    if not merchant_name or not isinstance(merchant_name, str):
        return "기타"
    
    merchant_str = str(merchant_name).lower()
    
    # 직접 매핑 처리 (우선 적용)
    direct_mappings = {
        "카카오페이": "교통비",
        "카카오t": "교통비",
        "스타벅스": "식비",
    }
    
    for key, category in direct_mappings.items():
        if key.lower() in merchant_str:
            return category
    
    # 키워드 기반 분류
    for keyword, category in MERCHANT_CATEGORY_MAP.items():
        if keyword.lower() in merchant_str:
            return category
    
    return "기타"

# 부가세 공제 가능 여부 확인 함수
def is_tax_deductible(category):
    """
    카테고리별 부가세 공제 가능 여부 확인
    """
    return VAT_DEDUCTIBLE_MAP.get(category, True)

def preprocess_lotte_card(file_path):
    """
    롯데카드 데이터 전처리 함수
    
    Args:
        file_path: 롯데카드에서 다운로드한 엑셀 파일 경로
    
    Returns:
        전처리된 데이터프레임
    """
    try:
        # 엑셀 파일 읽기 - 롯데카드는 보통 첫 몇 줄이 설명/헤더로 구성되어 있음
        # 실제 데이터는 몇 번째 행부터 시작되는지 확인 필요
        df = pd.read_excel(file_path, header=None)
        
        # 실제 헤더 위치 찾기
        header_row = None
        for i, row in df.iterrows():
            if row.apply(lambda x: isinstance(x, str) and any(pattern in x for pattern in DATE_PATTERNS)).any():
                header_row = i
                break
        
        if header_row is None:
            # 헤더 행을 찾지 못한 경우 첫 번째 행을 헤더로 시도
            header_row = 0
        
        # 헤더 행을 기준으로 데이터 다시 불러오기
        df = pd.read_excel(file_path, header=header_row)
        
        # 열 이름 표준화 (공백 제거 및 소문자 변환)
        df.columns = [str(col).strip().lower() for col in df.columns]
        
        # 필요한 열만 추출 (부가세 신고용)
        needed_columns = []
        column_types = {}  # 컬럼 타입 추적을 위한 딕셔너리
        
        # 열 이름 패턴에 따라 필요한 열 선택
        for col in df.columns:
            col_lower = col.lower()
            # 날짜 관련 열
            if any(date_term in col_lower for date_term in DATE_PATTERNS):
                needed_columns.append(col)
                column_types[col] = "날짜"
            # 금액 관련 열
            elif any(amount_term in col_lower for amount_term in AMOUNT_PATTERNS):
                needed_columns.append(col)
                column_types[col] = "금액"
            # 부가세 관련 열
            elif any(tax_term in col_lower for tax_term in VAT_PATTERNS):
                needed_columns.append(col)
                column_types[col] = "부가세"
            # 가맹점 정보
            elif any(store_term in col_lower for store_term in MERCHANT_PATTERNS):
                needed_columns.append(col)
                column_types[col] = "가맹점"
            # 승인번호
            elif any(approval_term in col_lower for approval_term in APPROVAL_PATTERNS):
                needed_columns.append(col)
                column_types[col] = "승인번호"
            # 이용 구분
            elif any(category_term in col_lower for category_term in CATEGORY_PATTERNS):
                needed_columns.append(col)
                column_types[col] = "구분"
        
        # 필요한 열이 존재하는지 확인하고, 존재하는 열만 선택
        existing_columns = [col for col in needed_columns if col in df.columns]
        if not existing_columns:
            # 필요한 열을 찾지 못한 경우 모든 열 사용
            df_selected = df
            st.warning("자동으로 부가세 신고용 필드를 식별하지 못했습니다. 모든 필드를 포함합니다.")
        else:
            df_selected = df[existing_columns]
        
        # 날짜 열 표준화
        date_columns = [col for col in df_selected.columns if column_types.get(col) == "날짜"]
        for date_col in date_columns:
            if df_selected[date_col].dtype == 'object' or pd.api.types.is_datetime64_any_dtype(df_selected[date_col]):
                try:
                    # 날짜 형식 변환 (여러 가능한 포맷 처리)
                    df_selected[date_col] = pd.to_datetime(df_selected[date_col], errors='coerce')
                    # YYYY-MM-DD 형식으로 통일
                    df_selected[date_col] = df_selected[date_col].dt.strftime('%Y-%m-%d')
                except:
                    pass
        
        # 금액 열 표준화 (문자열에서 숫자로 변환, 콤마 제거)
        amount_columns = [col for col in df_selected.columns 
                 if any(amount_term in col.lower() for amount_term in AMOUNT_PATTERNS)]
        # 승인번호 및 가맹점번호 컬럼 식별
        approval_columns = [col for col in df_selected.columns 
                            if any(approval_term in col.lower() for approval_term in APPROVAL_PATTERNS)]
        merchant_id_columns = [col for col in df_selected.columns 
                              if "번호" in col.lower() and any(store_term in col.lower() for store_term in MERCHANT_PATTERNS)]

        # 숫자 변환 제외 컬럼
        exclude_columns = approval_columns + merchant_id_columns
        for amount_col in amount_columns:
             if amount_col not in exclude_columns and df_selected[amount_col].dtype == 'object':
                try:
                    df_selected[amount_col] = df_selected[amount_col].astype(str)
                    df_selected[amount_col] = df_selected[amount_col].str.replace(r'[^\d.-]', '', regex=True)
                    df_selected[amount_col] = pd.to_numeric(df_selected[amount_col], errors='coerce')
                except:
                    pass
        
        # 기본 컬럼 추가/표준화
        # 1. 식별된 날짜 컬럼이 없는 경우 빈 컬럼 추가
        date_col = next((col for col in df_selected.columns if column_types.get(col) == "날짜"), None)
        if date_col is None:
            df_selected['이용일자'] = None
            date_col = '이용일자'
            column_types['이용일자'] = "날짜"
        
        # 2. 식별된 금액 컬럼이 없는 경우 빈 컬럼 추가
        amount_col = next((col for col in df_selected.columns if column_types.get(col) == "금액"), None)
        if amount_col is None:
            df_selected['이용금액'] = None
            amount_col = '이용금액'
            column_types['이용금액'] = "금액"
        
        # 3. 식별된 가맹점 컬럼이 없는 경우 빈 컬럼 추가
        merchant_col = next((col for col in df_selected.columns if column_types.get(col) == "가맹점"), None)
        if merchant_col is None:
            df_selected['가맹점명'] = None
            merchant_col = '가맹점명'
            column_types['가맹점명'] = "가맹점"
        
        # 4. 부가세 예상 컬럼 추가 (금액의 1/11)
        vat_col = next((col for col in df_selected.columns if column_types.get(col) == "부가세"), None)
        if vat_col is None:
            # 부가세 컬럼이 없으면 금액에서 예상 부가세 계산 (1/11)
            if amount_col:
                df_selected['예상부가세'] = (df_selected[amount_col] / 11).round().fillna(0)
                vat_col = '예상부가세'
                column_types['예상부가세'] = "부가세"
            else:
                df_selected['예상부가세'] = 0
                vat_col = '예상부가세'
                column_types['예상부가세'] = "부가세"
        
        # 5. '월' 컬럼 추가
        if date_col in df_selected.columns:
            df_selected['거래월'] = pd.to_datetime(df_selected[date_col], errors='coerce').dt.strftime('%Y-%m')
            column_types['거래월'] = "월"
        
        # 6. 카테고리 및 부가세 공제 가능 여부 컬럼 추가 (로컬 함수 사용)
        if merchant_col in df_selected.columns:
            # 카테고리 분류 적용
            df_selected['카테고리'] = df_selected[merchant_col].apply(classify_merchant_category)
            # 부가세 공제 여부 설정
            df_selected['부가세공제'] = df_selected['카테고리'].apply(is_tax_deductible)
        else:
            df_selected['카테고리'] = "기타"
            df_selected['부가세공제'] = True
            
        column_types['카테고리'] = "카테고리"
        column_types['부가세공제'] = "부가세공제"
        
        # 7. 매입/매출 구분 추가 (카드 사용은 대부분 매입)
        df_selected['구분'] = '매입'
        column_types['구분'] = "거래구분"
        
        # 필요한 컬럼 순서 재정렬
        important_columns = ['거래월', date_col, merchant_col, '카테고리', '부가세공제', amount_col, vat_col, '구분']
        available_columns = [col for col in important_columns if col in df_selected.columns]
        other_columns = [col for col in df_selected.columns if col not in important_columns]
        df_selected = df_selected[available_columns + other_columns]
        
        return df_selected
        
    except Exception as e:
        st.error(f"데이터 전처리 중 오류가 발생했습니다: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return None