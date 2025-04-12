"""
전처리 모듈 패키지 초기화
"""
from tax_assistant.preprocessing.lotte_card import preprocess_lotte_card
from tax_assistant.preprocessing.shinhan_card import preprocess_shinhan_card
from tax_assistant.preprocessing.samsung_card import preprocess_samsung_card

# 카드사별 전처리 함수 매핑
preprocessing_functions = {
    "롯데카드": preprocess_lotte_card,
    "신한카드": preprocess_shinhan_card, 
    "삼성카드": preprocess_samsung_card,
    # 추후 다른 카드사 추가 가능
}

def get_preprocessing_function(card_company):
    """
    카드사에 맞는 전처리 함수 반환
    
    Args:
        card_company: 카드사 이름 (예: '롯데카드', '신한카드')
        
    Returns:
        전처리 함수
    """
    return preprocessing_functions.get(card_company, preprocess_lotte_card)  # 기본값은 롯데카드 처리 함수