"""
챗봇 모듈 패키지 초기화
"""
from tax_assistant.chatbot.tools import (
    analyze_dataframe,  # DataFrameTool 대신 함수 사용
    update_dataframe,   # update_dataframe 함수 추가
    get_tax_advice,
    calculate_tax,
    simulate_hometax_report,
    get_tax_saving_tips,
    analyze_chart , # 새로 추가한 함수
    get_young_entrepreneur_advice,  # 청년 창업자 조언
    get_business_card_strategy,    # 사업자 카드 전략
    get_first_vat_report_guide     # 첫 부가세 신고 가이드
)
from tax_assistant.chatbot.agent import create_tax_assistant_agent, TaxAssistantSession
from tax_assistant.chatbot.prompts import TAX_ASSISTANT_PROMPT