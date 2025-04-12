"""
가맹점 카테고리 분류 모듈
"""

# 가맹점 카테고리 매핑
MERCHANT_CATEGORY_MAP = {
    # 식비
     "카카오페이": "교통비",
    "카카오t": "교통비",
    "스타벅스": "식비",
 
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
    "국밥": "식비",
    "중식당": "식비",
    "일식당": "식비",
    "한식당": "식비",
    "양식당": "식비",
    
    # 교통비
    "주유소": "교통비",
    "택시": "교통비",
    "대리운전": "교통비",
    "주차장": "교통비",
    "철도": "교통비",
    "고속도로": "교통비",
    "버스": "교통비",
    "지하철": "교통비",
    "교통카드": "교통비",
    "GS칼텍스": "교통비",
    "SK에너지": "교통비",
    "현대오일뱅크": "교통비",
    "쏘카": "교통비",
    "그린카": "교통비",
    
    # 사무용품
    "문구": "사무용품",
    "프린터": "사무용품",
    "복사": "사무용품",
    "오피스": "사무용품",
    "컴퓨터": "사무용품",
    "노트북": "사무용품",
    "모니터": "사무용품",
    "교보문고": "사무용품",
    "영풍문고": "사무용품",
    "알라딘": "사무용품",
    "예스24": "사무용품",
    "인터파크": "사무용품",
    
    # 통신비
    "통신": "통신비",
    "모바일": "통신비",
    "인터넷": "통신비",
    "전화": "통신비",
    "핸드폰": "통신비",
    "휴대폰": "통신비",
    "SKT": "통신비",
    "KT": "통신비",
    "LG유플러스": "통신비",
    
    # 광고홍보비
    "광고": "광고홍보비",
    "인쇄": "광고홍보비",
    "홍보": "광고홍보비",
    "디자인": "광고홍보비",
    "마케팅": "광고홍보비",
    "인쇄소": "광고홍보비",
    "배너": "광고홍보비",
    
    # 임대료
    "부동산": "임대료",
    "임대": "임대료",
    "관리비": "임대료",
    "건물": "임대료",
    "오피스텔": "임대료",
    "전기요금": "임대료",
    "가스요금": "임대료",
    "수도요금": "임대료",
    
    # 접대비
    "유흥": "접대비",
    "술집": "접대비",
    "노래방": "접대비",
    "주점": "접대비",
    "바(Bar)": "접대비",
    "클럽": "접대비",
    "룸싸롱": "접대비",
    "룸살롱": "접대비",
    
    # 여행 및 숙박
    "호텔": "여행숙박",
    "콘도": "여행숙박",
    "리조트": "여행숙박",
    "숙박": "여행숙박",
    "여행사": "여행숙박",
    "펜션": "여행숙박",
    "모텔": "여행숙박",
    
    # 의료비
    "병원": "의료비",
    "약국": "의료비",
    "의원": "의료비",
    "의료": "의료비",
    "치과": "의료비",
    "안과": "의료비",
    "한의원": "의료비",
    "피부과": "의료비",
    
    # 복리후생
    "복지": "복리후생",
    "직원": "복리후생",
    "교육": "복리후생",
    "연수": "복리후생",
    "세미나": "복리후생",
    "워크샵": "복리후생",
    "선물": "복리후생",
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

SPECIFIC_MERCHANT_MAPPING = {
    "카카오페이": "교통비",
    "카카오t": "교통비",
    "스타벅스": "식비",
    # 더 많은 가맹점 추가
}

def classify_merchant_category(merchant_name):
    if not merchant_name or not isinstance(merchant_name, str):
        return "기타"
    
    merchant_lower = str(merchant_name).lower().strip()
    
    # 특정 가맹점명 직접 매핑 먼저 확인
    for specific_name, category in SPECIFIC_MERCHANT_MAPPING.items():
        if specific_name.lower() in merchant_lower:
            return category
    
    # 키워드 패턴 기반 매칭
    keyword_patterns = {
        "식비": ["식당", "음식", "커피", "베이커리", "치킨", "피자", "분식", "카페", "음료", "마트", "스토어", "편의점"],
        "교통비": ["택시", "카카오", "주유", "주차", "철도", "고속도로", "버스", "지하철"],
        "통신비": ["통신", "모바일", "인터넷", "전화", "핸드폰", "skt", "kt", "lg"],
        "사무용품": ["문구", "프린터", "복사", "오피스", "컴퓨터", "노트북", "모니터", "서적", "문고"]
    }
    
    # 패턴 기반 매칭 - 부분 문자열 검색으로 변경
    for category, patterns in keyword_patterns.items():
        for pattern in patterns:
            if pattern in merchant_lower:
                return category
    
    # 기존 매핑 확인 - 부분 문자열 검색으로 변경
    for keyword, category in MERCHANT_CATEGORY_MAP.items():
        if keyword.lower() in merchant_lower:
            return category
    
    return "기타"

def is_tax_deductible(category):
    """
    카테고리별 부가세 공제 가능 여부 확인
    
    Args:
        category: 지출 카테고리
    
    Returns:
        부가세 공제 가능 여부 (True/False)
    """
    # 카테고리가 매핑에 있는지 확인
    if category in VAT_DEDUCTIBLE_MAP:
        return VAT_DEDUCTIBLE_MAP[category]
    
    # 매핑에 없으면 기본적으로 공제 가능으로 처리
    return True

def get_all_categories():
    """
    모든 카테고리 목록 반환
    
    Returns:
        카테고리 목록
    """
    return sorted(set(MERCHANT_CATEGORY_MAP.values()))

def get_category_tax_rules():
    """
    카테고리별 부가세 공제 규칙 반환
    
    Returns:
        카테고리별 부가세 공제 규칙 딕셔너리
    """
    return VAT_DEDUCTIBLE_MAP

def categorize_transactions(df, merchant_col):
    """
    데이터프레임의 가맹점 컬럼을 기반으로 카테고리 및 부가세 공제 여부 컬럼 추가
    
    Args:
        df: 데이터프레임
        merchant_col: 가맹점명 컬럼
    
    Returns:
        카테고리 및 부가세 공제 여부 컬럼이 추가된 데이터프레임
    """
    if merchant_col in df.columns:
        # 하드코딩된 매핑 추가
        def enhanced_classify(merchant):
            if not merchant or not isinstance(merchant, str):
                return "기타"
            
            merchant_str = str(merchant).lower()
            
            # 직접 매핑 처리
            if "카카오" in merchant_str:
                return "교통비"
            elif "스타벅스" in merchant_str or "스타박스" in merchant_str:
                return "식비"
            elif "택시" in merchant_str:
                return "교통비"
            elif "티머니" in merchant_str or "tmoney" in merchant_str:
                return "교통비"
            else:
                return classify_merchant_category(merchant)
        
        # 직접 분류 함수 적용
        df['카테고리'] = df[merchant_col].apply(enhanced_classify)
        df['부가세공제'] = df['카테고리'].apply(is_tax_deductible)
    else:
        df['카테고리'] = "기타"
        df['부가세공제'] = True
    
    return df