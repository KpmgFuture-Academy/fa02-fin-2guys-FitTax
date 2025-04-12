import streamlit as st
import pandas as pd
import io
from datetime import datetime
import json

# 페이지 기본 설정
st.set_page_config(page_title="롯데카드 데이터 전처리 도구", layout="wide")

# 카테고리 매핑 JSON 정의
CATEGORY_MAPPING_JSON = {
    "categories": {
        "사무용품/비품": {
            "keywords": ["교보문고", "알파문구", "샤피오피스", "오피스디포", "컴퓨존", "문구", "프린터", "바른문구", "모닝글로리"],
            "tax_deductible": True
        },
        "통신비": {
            "keywords": ["SK텔레콤", "KT", "LG유플러스", "SKB인터넷", "SKT", "통신"],
            "tax_deductible": True
        },
        "임차료": {
            "keywords": ["삼성생명", "부동산114", "한국전력공사", "관리비", "임대"],
            "tax_deductible": True
        },
        "광고/마케팅": {
            "keywords": ["네이버광고", "카카오광고", "페이스북", "인스타그램", "광고", "인쇄"],
            "tax_deductible": True
        },
        "교통/출장": {
            "keywords": ["티머니", "카카오T", "카카오택시", "카카오페이(택시)", "대한항공", "아시아나항공", 
                        "GS칼텍스", "SK에너지", "한국고속도로", "택시", "카카오", "주유", "철도"],
            "tax_deductible": True
        },
        "업무식대": {
            "keywords": ["스타벅스", "이디야커피", "투썸플레이스", "맥도날드", "롯데리아", "본죽", "김밥천국", 
                       "식당", "카페", "커피", "베이커리", "파리바게뜨", "빵집"],
            "tax_deductible": True
        },
        "소프트웨어/구독": {
            "keywords": ["MS오피스", "Adobe", "AWS", "GitHub", "소프트웨어"],
            "tax_deductible": True
        },
        "접대비": {
            "keywords": ["아웃백", "VIPS", "신세계백화점", "롯데백화점", "접대", "술집", "바"],
            "tax_deductible": True
        },
        "복리후생": {
            "keywords": ["쿠팡", "마켓컬리", "네이버페이", "복지"],
            "tax_deductible": True
        },
        "공제불가/개인용도": {
            "keywords": ["CGV", "메가박스", "롯데월드", "영화", "놀이"],
            "tax_deductible": False
        },
        "미분류": {
            "keywords": [],
            "tax_deductible": False
        }
    }
}

def categorize_merchant(merchant_name, mapping_json):
    """JSON 매핑 사용하여 가맹점명 카테고리 매핑"""
    if pd.isna(merchant_name):
        return "미분류", None
    
    # 문자열로 변환 (숫자 등의 경우 대비)
    merchant_name = str(merchant_name)
    
    # 각 카테고리의 키워드 확인
    for category, info in mapping_json["categories"].items():
        # 정확히 일치하는 키워드 먼저 확인
        if merchant_name in info["keywords"]:
            return category, merchant_name
        
        # 포함된 키워드 확인
        for keyword in info["keywords"]:
            if keyword in merchant_name:
                return category, keyword
    
    # 매칭되는 키워드가 없으면 미분류
    return "미분류", None

def is_tax_deductible(category, mapping_json):
    """카테고리별 부가세 공제 여부 확인"""
    return mapping_json["categories"].get(category, {}).get("tax_deductible", False)

def calculate_vat(amount):
    """부가세 계산 (금액의 1/11)"""
    return round(amount / 11, 0)

def process_lotte_card(file, mapping_json):
    """롯데카드 데이터 처리 - JSON 매핑 사용 버전"""
    try:
        # 엑셀 파일 읽기
        df = pd.read_excel(file, header=5)
        
        # '총합계' 행 제거
        if '총합계' in df.values:
            df = df[~df.isin(['총합계']).any(axis=1)]
        
        # 가맹점명 컬럼 찾기
        merchant_col = None
        for col in df.columns:
            if '가맹점명' in str(col):
                merchant_col = col
                break
                
        if not merchant_col:
            for col in df.columns:
                if '가맹점' in str(col) or '상호' in str(col):
                    merchant_col = col
                    break
        
        if not merchant_col:
            st.error("가맹점명 컬럼을 찾을 수 없습니다.")
            return None
            
        # 금액 컬럼 찾기
        amount_col = None
        for col in df.columns:
            if '매출금액' in str(col):
                amount_col = col
                break
                
        if not amount_col:
            for col in df.columns:
                if '금액' in str(col) or '합계' in str(col):
                    amount_col = col
                    break
        
        if not amount_col:
            st.error("금액 컬럼을 찾을 수 없습니다.")
            return None
            
        # 날짜 컬럼 찾기
        date_col = None
        for col in df.columns:
            if '날짜' in str(col) or '일자' in str(col) or '승인일' in str(col):
                date_col = col
                break
        
        # 날짜 형식 변환 (텍스트 형태로 YYYY-MM-DD)
        if date_col:
            try:
                df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
                df[date_col] = df[date_col].dt.strftime('%Y-%m-%d')
            except:
                st.warning(f"날짜 형식 변환 중 오류가 발생했습니다. 원본 형식을 유지합니다.")
        
        # 금액 컬럼 숫자로 변환
        df[amount_col] = pd.to_numeric(df[amount_col], errors='coerce')
        
        st.success(f"처리 중... 가맹점 컬럼: {merchant_col}, 금액 컬럼: {amount_col}")
        
        # 가맹점별 카테고리 매핑 - JSON 기반
        df[['카테고리', '매칭키워드']] = df[merchant_col].apply(
            lambda x: pd.Series(categorize_merchant(x, mapping_json))
        )
        
        # 부가세 공제 여부
        df['부가세공제여부'] = df['카테고리'].apply(lambda x: is_tax_deductible(x, mapping_json))
        
        # 부가세 컬럼 확인
        vat_col = None
        for col in df.columns:
            if '부가세' in str(col):
                vat_col = col
                break
        
        # 부가세 값이 없거나 모두 0인 경우 계산
        if vat_col is None or df[vat_col].sum() == 0:
            df['부가세'] = df.apply(lambda row: calculate_vat(row[amount_col]) if row['부가세공제여부'] else 0, axis=1)
        else:
            df['부가세'] = df[vat_col]
            
        # 거래월 추가
        if date_col:
            try:
                df['거래월'] = df[date_col].str[:7]  # YYYY-MM 형태로 추출
            except:
                pass
        
        return {
            'processed_data': df,
            'merchant_col': merchant_col,
            'amount_col': amount_col,
            'date_col': date_col
        }
        
    except Exception as e:
        st.error(f"파일 처리 중 오류 발생: {str(e)}")
        return None

def to_csv(df):
    """데이터프레임을 CSV 형식으로 변환"""
    return df.to_csv(index=False).encode('utf-8-sig')  # 한글 깨짐 방지

def main():
    st.title("롯데카드 데이터 전처리 도구")
    
    st.markdown("""
    ### 사용 방법
    1. 롯데카드 엑셀 파일을 업로드하세요.
    2. 가맹점별 카테고리 분류와 부가세 계산이 자동으로 진행됩니다.
    3. 처리된 결과를 CSV 파일로 다운로드할 수 있습니다.
    """)
    
    # 파일 업로드
    uploaded_file = st.file_uploader("롯데카드 엑셀 파일 업로드", type=['xls', 'xlsx'])
    
    if uploaded_file is not None:
        with st.spinner("데이터 처리 중..."):
            # 데이터 처리
            results = process_lotte_card(uploaded_file, CATEGORY_MAPPING_JSON)
            
            if results:
                # 결과 표시
                st.success("데이터 처리 완료!")
                
                # 처리된 데이터 미리보기
                st.subheader("처리된 데이터 미리보기")
                st.dataframe(results['processed_data'].head(5), use_container_width=True)
                
                # 통계 요약 (간단히)
                processed_df = results['processed_data']
                st.text(f"총 {len(processed_df)}개 거래, {processed_df['카테고리'].nunique()}개 카테고리로 분류됨")
                
                # JSON 다운로드 버튼
                json_str = json.dumps(CATEGORY_MAPPING_JSON, ensure_ascii=False, indent=2)
                st.download_button(
                    label="📥 카테고리 매핑 JSON 다운로드",
                    data=json_str.encode('utf-8'),
                    file_name="category_mapping.json",
                    mime="application/json"
                )
                
                # CSV 다운로드 버튼
                csv_data = to_csv(processed_df)
                st.download_button(
                    label="📥 처리된 데이터 CSV 다운로드",
                    data=csv_data,
                    file_name=f"롯데카드_처리결과_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )

if __name__ == "__main__":
    main()