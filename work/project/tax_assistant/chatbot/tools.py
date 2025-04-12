"""
LangChain 도구 모듈
"""
import re
from langchain.tools import BaseTool, tool
import pandas as pd
from tax_assistant.preprocessing.lotte_card import (
    DATE_PATTERNS, AMOUNT_PATTERNS, VAT_PATTERNS, 
    MERCHANT_PATTERNS, CATEGORY_PATTERNS
)

_dataframe = None
def update_dataframe(df):
    """
    데이터프레임 업데이트
    """
    global _dataframe
    _dataframe = df

@tool
def analyze_chart(query: str) -> str:
    """
    차트 데이터를 분석하는 도구입니다. 월별 추세, 이상점 감지, 패턴 분석 등을 수행합니다.
    예: '월별 사용 금액 분석', '지출 패턴 분석', '이상치 탐지'
    """
    global _dataframe
    
    if _dataframe is None or len(_dataframe) == 0:
        return "데이터가 로드되지 않았습니다. 먼저 데이터를 업로드해주세요."
    
    try:
        # 날짜와 금액 필드 찾기
        date_col = next((col for col in _dataframe.columns 
                      if any(date_term in col.lower() for date_term in DATE_PATTERNS)), None)
        
        amount_col = next((col for col in _dataframe.columns 
                        if any(amount_term in col.lower() for amount_term in AMOUNT_PATTERNS)), None)
        
        if not date_col or not amount_col:
            return "날짜 또는 금액 필드를 찾을 수 없습니다."
        
        # 날짜 필드 변환
        _dataframe[date_col] = pd.to_datetime(_dataframe[date_col], errors='coerce')
        
        # 월별 데이터 분석
        if "월별" in query or "추세" in query:
            # 거래월 컬럼 확인/생성
            if '거래월' in _dataframe.columns:
                month_col = '거래월'
            else:
                _dataframe['거래월'] = _dataframe[date_col].dt.strftime('%Y-%m')
                month_col = '거래월'
            
            monthly_data = _dataframe.groupby(month_col)[amount_col].agg(['sum', 'mean', 'count']).reset_index()
            monthly_data.columns = ['월', '합계', '평균', '건수']
            
            # 총액 및 평균 계산
            total_amount = monthly_data['합계'].sum()
            overall_avg = total_amount / monthly_data['건수'].sum() if monthly_data['건수'].sum() > 0 else 0
            
            # 추세 분석 (선형 회귀)
            if len(monthly_data) > 1:
                # 월별 합계 데이터로 간단한 추세 표현
                first_month = monthly_data['합계'].iloc[0]
                last_month = monthly_data['합계'].iloc[-1]
                trend = "증가" if last_month > first_month else "감소"
                
                # 가장 높은 달과 낮은 달
                max_month = monthly_data.loc[monthly_data['합계'].idxmax()]
                min_month = monthly_data.loc[monthly_data['합계'].idxmin()]
                
                result = f"""
                월별 사용 금액 분석 결과:
                
                총 사용 금액: {total_amount:,.0f}원
                
                월별 추이: {trend}하는 경향을 보입니다.
                
                월별 사용 금액:
                {monthly_data.to_string(index=False)}
                
                가장 지출이 많았던 달: {max_month['월']} ({max_month['합계']:,.0f}원)
                가장 지출이 적었던 달: {min_month['월']} ({min_month['합계']:,.0f}원)
                """
                return result
            else:
                return f"월별 분석을 위한 충분한 데이터가 없습니다. 현재 데이터 수: {len(_dataframe)}개"
        
        # 이상치 분석
        elif "이상" in query or "이상점" in query or "이상치" in query:
            # 이상치 탐지 (표준편차 방법)
            mean_val = _dataframe[amount_col].mean()
            std_val = _dataframe[amount_col].std()
            
            # 이상치 계산 (2배 표준편차 이상)
            outliers = _dataframe[abs(_dataframe[amount_col] - mean_val) > 2 * std_val]
            
            if len(outliers) > 0:
                outliers_info = outliers[[date_col, amount_col]].sort_values(by=amount_col, ascending=False)
                outliers_info[date_col] = outliers_info[date_col].dt.strftime('%Y-%m-%d')
                
                result = f"""
                이상치 분석 결과:
                
                평균 금액: {mean_val:,.0f}원
                표준편차: {std_val:,.0f}원
                
                이상치로 판단된 데이터 수: {len(outliers)}개
                
                이상치 목록 (상위 5개):
                """
                for i, (_, row) in enumerate(outliers_info.head(5).iterrows()):
                    result += f"- {row[date_col]}: {row[amount_col]:,.0f}원\n"
                
                return result
            else:
                return "이상치가 탐지되지 않았습니다. 데이터가 비교적 고르게 분포되어 있습니다."
        
        # 패턴 분석
        elif "패턴" in query or "경향" in query:
            # 월별 패턴
            if '거래월' in _dataframe.columns:
                month_col = '거래월'
            else:
                _dataframe['거래월'] = _dataframe[date_col].dt.strftime('%Y-%m')
                month_col = '거래월'
            
            monthly_pattern = _dataframe.groupby(month_col)[amount_col].mean().reset_index()
            monthly_pattern.columns = ['월', '평균금액']
            
            result = f"""
            지출 패턴 분석 결과:
            
            월별 평균 지출 금액:
            """
            for _, row in monthly_pattern.iterrows():
                result += f"- {row['월']}: {row['평균금액']:,.0f}원\n"
            
            result += f"""
            데이터 기반 인사이트:
            - 전체 데이터 기간: {_dataframe[date_col].min().strftime('%Y-%m-%d')} ~ {_dataframe[date_col].max().strftime('%Y-%m-%d')}
            - 총 데이터 수: {len(_dataframe)}개
            - 평균 지출 금액: {_dataframe[amount_col].mean():,.0f}원
            """
            return result
        
        # 일반적인 데이터 분석
        else:
            # 월별 데이터 집계
            if '거래월' in _dataframe.columns:
                month_col = '거래월'
            else:
                _dataframe['거래월'] = _dataframe[date_col].dt.strftime('%Y-%m')
                month_col = '거래월'
            
            monthly_sum = _dataframe.groupby(month_col)[amount_col].sum().reset_index()
            total_amount = monthly_sum[amount_col].sum()
            
            # 카테고리별 정보 (있는 경우)
            categories_analysis = ""
            for col in _dataframe.columns:
                if '카테고리' in col.lower() or 'category' in col.lower():
                    top_categories = _dataframe.groupby(col)[amount_col].sum().sort_values(ascending=False).head(3)
                    categories_info = ""
                    for cat, amt in top_categories.items():
                        categories_info += f"- {cat}: {amt:,.0f}원\n"
                    if categories_info:
                        categories_analysis = f"\n\n주요 지출 카테고리:\n{categories_info}"
                    break
            
            result = f"""
            차트 데이터 분석 결과:
            
            분석 기간: {_dataframe[date_col].min().strftime('%Y-%m-%d')} ~ {_dataframe[date_col].max().strftime('%Y-%m-%d')}
            총 사용 금액: {total_amount:,.0f}원
            데이터 수: {len(_dataframe)}개
            
            월별 사용 금액:
            """
            for _, row in monthly_sum.iterrows():
                result += f"- {row[month_col]}: {row[amount_col]:,.0f}원\n"
            
            result += categories_analysis
            return result
    
    except Exception as e:
        return f"차트 분석 중 오류가 발생했습니다: {str(e)}"
@tool
def get_young_entrepreneur_advice(query: str) -> str:
    """
    청년 창업자를 위한 세금 및 재무 관련 조언을 제공하는 도구입니다.
    청년 창업자 특화 세제 혜택, 지원 정책, 창업 초기 세금 관리 팁 등을 안내합니다.
    예: '청년 창업자 세제 혜택', '창업 초기 세금', '정부 지원 사업'
    """
    advice_dict = {
        "세제혜택": "청년 창업자(만 39세 이하)는 수입금액 4,800만원 이하인 경우 소득세 감면 혜택을 받을 수 있습니다. 또한 창업 후 5년간 매년 최대 1천만원까지 소득세 감면이 가능합니다.",
        "지원정책": "청년 창업자는 중소벤처기업부의 '청년창업사관학교', '창업성공패키지' 등의 지원사업에 지원할 수 있으며, 자금 지원, 교육, 컨설팅 등 다양한 혜택을 받을 수 있습니다.",
        "카드사용": "청년 창업자 전용 사업자 카드를 발급받으면 연회비 면제, 할인 혜택 등 다양한 특전을 받을 수 있습니다. 주요 은행 및 카드사의 청년 창업자 특화 상품을 확인해보세요.",
        "세금신고": "창업 첫해에는 직전년도 매출이 없어 부가세 예정고지가 없으므로, 반드시 신고 기한을 챙겨서 자진 신고해야 합니다. 홈택스 전자신고를 활용하면 편리합니다.",
        "장부관리": "창업 초기부터 체계적인 장부 관리가 중요합니다. 클라우드 기반 회계 프로그램을 활용하면 세금 신고와 경비 관리가 용이합니다.",
        "컨설팅": "창업 초기에는 무료 세무 컨설팅을 제공하는 정부 지원 서비스를 활용해보세요. 세무서의 '납세자보호담당관'이나 '소상공인지원센터'에서 도움을 받을 수 있습니다."
    }
    
    response = []
    for key, value in advice_dict.items():
        if key in query:
            response.append(value)
    
    if not response:
        # 특정 키워드가 없을 경우 일반적인 조언 제공
        response = [
            "청년 창업자는 다양한 세제 혜택과 정부 지원 정책을 활용할 수 있습니다.",
            "창업 초기에는 매출과 비용에 대한 명확한 증빙 관리가 중요합니다.",
            "청년 창업자 전용 금융 상품과 카드를 활용하면 경비 절감에 도움이 됩니다.",
            "부가세 신고는 1년에 2번, 소득세 신고는 매년 5월에 진행해야 합니다.",
            "정부의 청년 창업 지원 사업에 적극 참여하여 자금과 컨설팅 혜택을 활용하세요."
        ]
    
    return "\n\n".join(response)

@tool
def get_business_card_strategy(query: str) -> str:
    """
    사업자를 위한 카드 사용 전략과 팁을 제공하는 도구입니다.
    사업자 카드 선택, 효율적인 사용 방법, 세금 관리를 위한 카드 활용법 등을 안내합니다.
    예: '사업자 카드 추천', '카드 사용 팁', '세금 관리 카드'
    """
    strategy_dict = {
        "카드선택": "사업 규모와 성격에 맞는 카드를 선택하세요. 주유, 통신비, 사무용품 등 자주 사용하는 항목에 특화된 카드를 발급받으면 혜택이 큽니다. 개인카드와 사업자카드를 명확히 구분하여 사용하세요.",
        "혜택": "사업자 카드는 연말정산 시 소득공제 대상이 아니지만, 사업 경비로 100% 인정됩니다. 또한 부가세 신고 시 매입세액공제를 받을 수 있어 세금 부담을 줄일 수 있습니다.",
        "관리방법": "사업용과 개인용 카드를 철저히 구분하여 사용하고, 영수증은 항상 보관하세요. 카드사에서 제공하는 매출/매입 내역 서비스를 활용하면 세금 신고 시 편리합니다.",
        "부가세": "신용카드 매출전표는 세금계산서 없이도 매입세액공제가 가능합니다. 단, 공제를 위해서는 사업과 관련된 용도로만 사용해야 합니다.",
        "비용절감": "카드사별 제휴 혜택을 잘 활용하면 연간 수십만원의 비용을 절감할 수 있습니다. 특히 주유, 통신비, 오피스 용품 등 고정비 항목의 할인 혜택을 확인하세요."
    }
    
    response = []
    for key, value in strategy_dict.items():
        if key in query:
            response.append(value)
    
    if not response:
        response = [
            "사업자 카드는 개인 신용카드와 달리 사업 경비로 100% 인정받을 수 있습니다.",
            "모든 사업 관련 지출은 사업자 카드로 결제하여 세금 신고 시 누락을 방지하세요.",
            "카드사별 특화 서비스와 혜택을 비교하여 사업 특성에 맞는 카드를 선택하세요.",
            "카드 사용 내역은 월별, 분기별로 정기적으로 확인하여 불필요한 지출을 관리하세요.",
            "부가세 신고 시 카드 매입내역을 자동으로 활용할 수 있는 홈택스 기능을 활용하세요."
        ]
    
    return "\n\n".join(response)

@tool
def get_first_vat_report_guide(query: str) -> str:
    """
    첫 부가세 신고를 앞둔 사업자를 위한 상세 안내 가이드를 제공하는 도구입니다.
    신고 절차, 필요 서류, 주의사항, 자주 하는 실수 등을 단계별로 안내합니다.
    예: '첫 부가세 신고', '부가세 신고 준비', '부가세 신고 실수'
    """
    guide_dict = {
        "준비물": "부가세 신고를 위해 다음 자료를 준비하세요:\n1. 매출 세금계산서 및 신용카드 매출전표\n2. 매입 세금계산서 및 신용카드 매입전표\n3. 통장 거래내역\n4. 현금영수증 내역\n5. 필요시 세금계산서 합계표",
        "절차": "부가세 신고 절차:\n1. 홈택스(www.hometax.go.kr) 접속 및 로그인\n2. '신고/납부' 메뉴에서 '부가가치세' 선택\n3. '확정(예정)신고서' 선택\n4. 매출/매입 내역 입력\n5. 신고서 검토 및 제출\n6. 납부할 세액이 있는 경우 납부",
        "실수": "첫 부가세 신고 시 자주 하는 실수:\n1. 신고 기한 놓침\n2. 매입세액 공제 가능한 항목 누락\n3. 개인 용도 지출을 사업 비용으로 포함\n4. 적격 증빙 없는 비용 포함\n5. 과세/면세 매출 구분 오류",
        "감면": "소규모 사업자 세금 감면 제도:\n1. 간이과세자: 연 매출 8,000만원 미만\n2. 면세사업자: 의료, 교육 등 특정 업종\n3. 간이과세자 부가세 감면: 업종별 부가율 적용\n4. 소규모 일반과세자 감면: 연 매출 8,000만원 미만 간이과세 미적용자",
        "신고기한": "부가세 신고 기한:\n1. 1기 예정신고: 4월 1일~4월 25일 (1월~3월 실적)\n2. 1기 확정신고: 7월 1일~7월 25일 (4월~6월 실적 및 1기 전체 정산)\n3. 2기 예정신고: 10월 1일~10월 25일 (7월~9월 실적)\n4. 2기 확정신고: 다음해 1월 1일~1월 25일 (10월~12월 실적 및 2기 전체 정산)"
    }
    
    response = []
    for key, value in guide_dict.items():
        if key in query:
            response.append(value)
    
    if not response:
        response = [
            "첫 부가세 신고는 사업자로서 중요한 이정표입니다. 다음 단계를 따라 진행하세요:\n\n1. 과세기간 동안의 모든 매출/매입 자료를 정리합니다.\n2. 홈택스 웹사이트에 로그인하여 신고서 작성을 시작합니다.\n3. 매출과 매입 내역을 정확히 입력합니다.\n4. 신고서 검토 후 제출합니다.\n5. 납부할 세액이 있다면 납부기한 내에 납부합니다.",
            "신고 전에 카드사 매입/매출 내역, 세금계산서 발행/수취 내역을 모두 확인하세요. 누락된 항목이 없는지 꼼꼼히 체크하는 것이 중요합니다.",
            "첫 신고라면 세무서 납세자보호담당관이나 홈택스 고객센터(126)에 문의하여 도움을 받을 수 있습니다. 또한 세무사에게 자문을 구하는 것도 좋은 방법입니다.",
            "부가세 신고 후에는 신고내역을 보관하고, 다음 신고를 위한 자료 관리 시스템을 구축해두면 좋습니다. 클라우드 회계 프로그램 활용을 고려해보세요."
        ]
    
    return "\n\n".join(response)
   
@tool
def analyze_dataframe(query: str) -> str:
    """
    카드 사용 데이터프레임을 분석하는 도구입니다. 월별 금액, 가맹점별 지출, 부가세 등을 분석합니다.
    """
    global _dataframe
    
    if _dataframe is None or len(_dataframe) == 0:
        return "데이터가 로드되지 않았습니다. 먼저 카드사 데이터를 업로드해주세요."
    
    try:
        # 중요 컬럼 식별
        date_col = next((col for col in _dataframe.columns 
                      if any(date_term in col.lower() for date_term in DATE_PATTERNS)), None)
        
        amount_col = next((col for col in _dataframe.columns 
                        if any(amount_term in col.lower() for amount_term in AMOUNT_PATTERNS)), None)
        
        vat_col = next((col for col in _dataframe.columns 
                      if any(tax_term in col.lower() for tax_term in VAT_PATTERNS)), None)
        
        merchant_col = next((col for col in _dataframe.columns 
                          if any(store_term in col.lower() for store_term in MERCHANT_PATTERNS)), None)
        
        # 쿼리에 따라 다양한 분석 수행
        if "월별" in query and ("합계" in query or "총액" in query or "금액" in query):
            # 월별 금액 분석 코드...
            # (기존 코드와 동일한 분석 로직 구현)
            if date_col:
                # 날짜 열 변환
                _dataframe[date_col] = pd.to_datetime(_dataframe[date_col], errors='coerce')
                
                # 거래월 컬럼 확인/생성
                if '거래월' in _dataframe.columns:
                    month_col = '거래월'
                else:
                    _dataframe['거래월'] = _dataframe[date_col].dt.strftime('%Y-%m')
                    month_col = '거래월'
                
                # 금액 열 확인
                if amount_col:
                    monthly_summary = _dataframe.groupby(month_col)[amount_col].sum().reset_index()
                    total_amount = monthly_summary[amount_col].sum()
                    
                    result = f"월별 합계 정보:\n{monthly_summary.to_string(index=False)}\n\n"
                    result += f"총 합계: {total_amount:,.0f}원"
                    return result
                else:
                    return "금액 관련 열을 찾을 수 없습니다."
            else:
                return "날짜 관련 열을 찾을 수 없습니다."
        
        # 다른 분석 기능들을 여기에 계속 구현...
        # (기존 _run 메서드의 코드를 그대로 가져와 구현)
        
        # 기본 데이터 요약
        result = f"데이터프레임 정보: {len(_dataframe):,}개의 거래 내역이 있습니다.\n"
        if amount_col:
            total_amount = _dataframe[amount_col].sum()
            result += f"총 금액: {total_amount:,.0f}원\n"
        if vat_col:
            total_vat = _dataframe[vat_col].sum()
            result += f"총 부가세: {total_vat:,.0f}원\n"
        if date_col:
            _dataframe[date_col] = pd.to_datetime(_dataframe[date_col], errors='coerce')
            min_date = _dataframe[date_col].min()
            max_date = _dataframe[date_col].max()
            result += f"데이터 기간: {min_date.strftime('%Y-%m-%d')} ~ {max_date.strftime('%Y-%m-%d')}"
        
        return result
    
    except Exception as e:
        return f"분석 중 오류가 발생했습니다: {str(e)}"
        
class DataFrameTool(BaseTool):
    """
    카드 사용 데이터프레임을 분석하는 도구
    """
    name: str = "dataframe_tool"
    description: str = "카드 사용 데이터프레임을 분석하는 도구"
    
    def __init__(self, df=None):
        self.df = df
        super().__init__()
    
    def _run(self, query: str) -> str:
        """
        데이터프레임 분석 실행
        
        Args:
            query: 분석 쿼리
            
        Returns:
            분석 결과 텍스트
        """
        if self.df is None or len(self.df) == 0:
            return "데이터가 로드되지 않았습니다. 먼저 카드사 데이터를 업로드해주세요."
        
        try:
            # 중요 컬럼 식별
            date_col = next((col for col in self.df.columns 
                           if any(date_term in col.lower() for date_term in DATE_PATTERNS)), None)
            
            amount_col = next((col for col in self.df.columns 
                             if any(amount_term in col.lower() for amount_term in AMOUNT_PATTERNS)), None)
            
            vat_col = next((col for col in self.df.columns 
                          if any(tax_term in col.lower() for tax_term in VAT_PATTERNS)), None)
            
            merchant_col = next((col for col in self.df.columns 
                               if any(store_term in col.lower() for store_term in MERCHANT_PATTERNS)), None)
            
            # 쿼리에 따라 다양한 분석 수행
            if "월별" in query and ("합계" in query or "총액" in query or "금액" in query):
                # 날짜 열 확인
                if date_col:
                    # 날짜 열 변환
                    self.df[date_col] = pd.to_datetime(self.df[date_col], errors='coerce')
                    
                    # 거래월 컬럼 확인/생성
                    if '거래월' in self.df.columns:
                        month_col = '거래월'
                    else:
                        self.df['거래월'] = self.df[date_col].dt.strftime('%Y-%m')
                        month_col = '거래월'
                    
                    # 금액 열 확인
                    if amount_col:
                        monthly_summary = self.df.groupby(month_col)[amount_col].sum().reset_index()
                        total_amount = monthly_summary[amount_col].sum()
                        
                        result = f"월별 합계 정보:\n{monthly_summary.to_string(index=False)}\n\n"
                        result += f"총 합계: {total_amount:,.0f}원"
                        return result
                    else:
                        return "금액 관련 열을 찾을 수 없습니다."
                else:
                    return "날짜 관련 열을 찾을 수 없습니다."
                    
            elif "가맹점" in query and ("많이" in query or "순위" in query or "상위" in query or "TOP" in query.upper()):
                # 가맹점 열 확인
                if merchant_col:
                    # 금액 열 확인
                    if amount_col:
                        merchant_summary = self.df.groupby(merchant_col)[amount_col].sum().sort_values(ascending=False).reset_index().head(10)
                        result = f"가맹점별 사용 금액 상위 10개:\n{merchant_summary.to_string(index=False)}"
                        return result
                    else:
                        return "금액 관련 열을 찾을 수 없습니다."
                else:
                    return "가맹점 관련 열을 찾을 수 없습니다."
                    
            elif "부가세" in query and ("합계" in query or "총액" in query or "얼마" in query):
                # 부가세 열 확인
                if vat_col:
                    total_vat = self.df[vat_col].sum()
                    return f"부가세 합계: {total_vat:,.0f}원"
                else:
                    # 금액 열을 통한 부가세 추정
                    if amount_col:
                        total_amount = self.df[amount_col].sum()
                        estimated_vat = total_amount / 11  # 부가세 추정 (11분의 1)
                        return f"부가세 열이 없어 금액에서 추정합니다. 추정 부가세 합계: {estimated_vat:,.0f}원"
                    else:
                        return "부가세나 금액 관련 열을 찾을 수 없습니다."
            
            elif "기간" in query or "언제부터" in query or "언제까지" in query:
                # 날짜 범위 분석
                if date_col:
                    self.df[date_col] = pd.to_datetime(self.df[date_col], errors='coerce')
                    min_date = self.df[date_col].min()
                    max_date = self.df[date_col].max()
                    return f"데이터 기간: {min_date.strftime('%Y-%m-%d')} ~ {max_date.strftime('%Y-%m-%d')}"
                else:
                    return "날짜 관련 열을 찾을 수 없습니다."
            
            elif "건수" in query or "거래 수" in query or "횟수" in query:
                # 거래 건수 확인
                total_count = len(self.df)
                
                if date_col:
                    self.df[date_col] = pd.to_datetime(self.df[date_col], errors='coerce')
                    if '거래월' in self.df.columns:
                        month_col = '거래월'
                    else:
                        self.df['거래월'] = self.df[date_col].dt.strftime('%Y-%m')
                        month_col = '거래월'
                    
                    monthly_count = self.df.groupby(month_col).size().reset_index(name='건수')
                    result = f"월별 거래 건수:\n{monthly_count.to_string(index=False)}\n\n"
                    result += f"총 거래 건수: {total_count}건"
                    return result
                else:
                    return f"총 거래 건수: {total_count}건"
            
            elif "최대" in query or "가장 많은" in query or "최고" in query:
                # 최대 금액 거래 확인
                if amount_col:
                    max_amount_idx = self.df[amount_col].idxmax()
                    max_amount_row = self.df.loc[max_amount_idx]
                    
                    result = f"최대 금액 거래 정보:\n"
                    if date_col:
                        result += f"- 날짜: {max_amount_row[date_col]}\n"
                    if merchant_col:
                        result += f"- 가맹점: {max_amount_row[merchant_col]}\n"
                    result += f"- 금액: {max_amount_row[amount_col]:,.0f}원"
                    
                    return result
                else:
                    return "금액 관련 열을 찾을 수 없습니다."
            
            else:
                # 기본 데이터 요약
                result = f"데이터프레임 정보: {len(self.df):,}개의 거래 내역이 있습니다.\n"
                if amount_col:
                    total_amount = self.df[amount_col].sum()
                    result += f"총 금액: {total_amount:,.0f}원\n"
                if vat_col:
                    total_vat = self.df[vat_col].sum()
                    result += f"총 부가세: {total_vat:,.0f}원\n"
                if date_col:
                    self.df[date_col] = pd.to_datetime(self.df[date_col], errors='coerce')
                    min_date = self.df[date_col].min()
                    max_date = self.df[date_col].max()
                    result += f"데이터 기간: {min_date.strftime('%Y-%m-%d')} ~ {max_date.strftime('%Y-%m-%d')}"
                
                return result
        
        except Exception as e:
            return f"분석 중 오류가 발생했습니다: {str(e)}"
    
    def update_dataframe(self, df):
        """
        데이터프레임 업데이트
        
        Args:
            df: 새 데이터프레임
        """
        self.df = df


@tool
def get_tax_advice(query: str) -> str:
    """
    부가세 신고 관련 조언을 제공하는 도구입니다. 신고기한, 간이과세, 세액공제 등 부가세 관련 정보를 제공합니다.
    예: '부가세 신고기한', '간이과세 기준', '매입세액공제 요건'
    """
    
    advice_dict = {
        "신고기한": "부가세 신고는 일반과세자의 경우 분기별로 신고해야 합니다. 1기(1월~6월)는 7월 25일까지, 2기(7월~12월)는 다음해 1월 25일까지 신고해야 합니다.",
        "간이과세": "연 매출 8,000만원 미만인 사업자는 간이과세자로 신청할 수 있으며, 부가세 신고는 년 1회만 하면 됩니다. 신고 기한은 다음해 1월 25일까지입니다.",
        "세액공제": "세금계산서, 신용카드 매출전표 등의 적격 증빙을 수취하면 매입세액공제를 받을 수 있습니다.",
        "카드매출": "신용카드 매출은 자동으로 국세청에 통보되므로 누락 없이 신고해야 합니다.",
        "영수증": "간이영수증은 3만원 이하의 경우에만 매입세액공제가 가능합니다.",
        "필요경비": "업무용 경비는 증빙서류를 구비해야 세액공제가 가능합니다.",
        "전자세금계산서": "전자세금계산서는 국세청 홈택스에서 발행 가능하며, 종이세금계산서보다 세액공제 혜택이 큽니다.",
        "신고방법": "부가세 신고는 국세청 홈택스 웹사이트나 모바일 앱을 통해 전자신고할 수 있습니다.",
        "과세기간": "부가세 과세기간은 일반과세자의 경우 1기(1월~6월)와 2기(7월~12월)로 나누어집니다.",
        "예정신고": "예정신고는 1~3월(7월 25일까지), 7~9월(1월 25일까지) 중 발생한 거래에 대해 신고합니다.",
        "확정신고": "확정신고는 1~6월(7월 25일까지), 7~12월(다음해 1월 25일까지) 중 발생한 거래에 대해 신고합니다.",
        "매입세액": "매입세액은 사업자가 재화나 용역을 구입할 때 부담한 부가가치세로, 일정 요건 충족 시 매출세액에서 공제받을 수 있습니다.",
        "매출세액": "매출세액은 사업자가 재화나 용역을 판매할 때 거래상대방으로부터 받은 부가가치세입니다.",
        "경감세율": "간이과세자는 업종별로 다른 부가가치세 경감세율이 적용됩니다.",
        "납부세액": "납부세액은 매출세액에서 매입세액을 차감한 금액입니다.",
        "세금계산서": "세금계산서는 부가가치세가 과세되는 재화나 용역을 공급할 때 발행하는 증빙서류입니다."
    }
    
    response = []
    for key, value in advice_dict.items():
        if key in query:
            response.append(value)
    
    if not response:
        # 특정 키워드가 없을 경우 일반적인 조언 제공
        response = [
            "부가세 신고 시 모든 매출과 매입에 대한 증빙서류를 잘 정리해두는 것이 중요합니다.",
            "신용카드 매출전표, 세금계산서 등의 증빙은 5년간 보관해야 합니다.",
            "부가세 신고는 국세청 홈택스를 통해 간편하게 전자신고할 수 있습니다.",
            "자세한 사항은 국세청 세무상담센터(126)로 문의하시거나 세무사와 상담하시는 것이 좋습니다."
        ]
    
    return "\n".join(response)


@tool
def calculate_tax(query: str) -> str:
    """
    부가세 및 세금 계산을 수행하는 도구입니다. 금액을 입력받아 부가세, 공급가액 등을 계산합니다.
    예: '100만원에 대한 부가세', '500000원 부가세 역산', '1,200,000원 세전 금액'
    """
    # 금액 추출
    amount_pattern = r'(\d{1,3}(,\d{3})*|\d+)(\.\d+)?(원|만원)?'
    amount_match = re.search(amount_pattern, query)
    
    if not amount_match:
        return "계산할 금액을 찾을 수 없습니다. 예: '100만원에 대한 부가세 계산해줘'"
    
    # 금액 정제
    amount_str = amount_match.group(1).replace(',', '')
    amount = float(amount_str)
    
    # 단위 확인 (만원 단위 처리)
    if amount_match.group(4) == '만원':
        amount *= 10000
    
    # 계산 유형 결정
    if '부가세' in query or 'vat' in query.lower():
        vat = amount / 11  # 공급가액의 10%
        supply_value = amount - vat
        
        result = (
            f"금액 {amount:,.0f}원에 대한 부가세 계산 결과:\n"
            f"- 공급가액: {supply_value:,.0f}원\n"
            f"- 부가세액: {vat:,.0f}원\n"
            f"- 합계금액: {amount:,.0f}원"
        )
        return result
    
    elif '역산' in query or '역계산' in query:
        # 세금계산서 역산 (공급대가에서 공급가액과 세액 계산)
        supply_value = amount / 1.1  # 부가세 포함 금액에서 공급가액 계산
        vat = amount - supply_value
        
        result = (
            f"금액 {amount:,.0f}원에 대한 역산 결과:\n"
            f"- 공급가액: {supply_value:,.0f}원\n"
            f"- 부가세액: {vat:,.0f}원\n"
            f"- 합계금액: {amount:,.0f}원"
        )
        return result
    
    elif '세전' in query or '순이익' in query:
        # 세전 금액 계산 (부가세 제외)
        supply_value = amount / 1.1
        vat = amount - supply_value
        
        result = (
            f"금액 {amount:,.0f}원에 대한 세전 금액 계산 결과:\n"
            f"- 세전 금액(공급가액): {supply_value:,.0f}원\n"
            f"- 부가세액: {vat:,.0f}원"
        )
        return result
    
    else:
        # 기본적으로 부가세 계산
        vat = amount * 0.1
        total = amount + vat
        
        result = (
            f"금액 {amount:,.0f}원에 대한 부가세 계산 결과:\n"
            f"- 공급가액: {amount:,.0f}원\n"
            f"- 부가세액: {vat:,.0f}원\n"
            f"- 합계금액: {total:,.0f}원"
        )
        return result


@tool
def simulate_hometax_report(query: str) -> str:
    """
    홈택스 부가세 신고서 작성 시뮬레이션을 제공하는 도구입니다.
    카드 데이터를 기반으로 부가세 신고서 작성 과정을 안내합니다.
    """
    # 신고서 유형 확인
    report_type = None
    if "예정" in query:
        report_type = "예정신고"
    elif "확정" in query:
        report_type = "확정신고"
    else:
        report_type = "일반신고"
    
    # 신고 안내 제공
    guidance = f"""
{report_type} 신고서 작성 안내:

1. 홈택스(www.hometax.go.kr) 접속
2. 공동인증서(구 공인인증서)로 로그인
3. [신고/납부] > [부가가치세] > [{report_type}] 메뉴 선택
4. 사업자등록번호 및 과세기간 확인
5. 매출/매입 내역 입력:
   - [매입] 세금계산서/계산서 합계 입력
   - [매입] 신용카드/현금영수증 매입 합계 입력
   - [매출] 세금계산서/계산서 합계 입력
   - [매출] 신용카드/현금영수증 매출 합계 입력
6. 신고서 미리보기 확인
7. 전자신고 제출하기

※ 실제 신고 시에는 세무사와 상담하시거나 국세청 세무상담센터(126)로 문의하시는 것이 좋습니다.
※ 이 안내는 단순 참고용이며, 실제 홈택스 화면과 다를 수 있습니다.
"""
    return guidance


@tool
def get_tax_saving_tips(query: str) -> str:
    """
    개인사업자를 위한 절세 팁을 제공하는 도구입니다.
    세금 절약, 공제 혜택 등에 관한 정보를 제공합니다.
    """
    # 절세 팁 데이터
    tips = {
        "경비": [
            "업무 관련 경비는 증빙서류를 반드시 구비하여 필요경비로 인정받으세요.",
            "신용카드, 현금영수증, 세금계산서 등 적격증빙으로 경비 처리하세요.",
            "개인 신용카드보다 사업자 명의 카드 사용이 세금 관리에 유리합니다."
        ],
        "소득공제": [
            "사업자 본인의 국민연금, 건강보험료는 전액 필요경비로 인정됩니다.",
            "소기업·소상공인 공제부금(노란우산공제)은 사업소득금액에서 추가 공제 가능합니다.",
            "퇴직연금 납입액은 연 700만원까지 추가 세액공제 대상입니다."
        ],
        "부가세": [
            "간이과세자는 부가세 납부세액 경감 혜택이 있습니다.",
            "세금계산서 수취 시 매입세액공제를 받아 부가세 부담을 줄일 수 있습니다.",
            "영세율, 면세 대상 거래는 부가세가 과세되지 않습니다."
        ],
        "신고": [
            "종합소득세 확정신고는 매년 5월에 이루어집니다.",
            "성실신고확인제도를 활용하면 세액공제 혜택을 받을 수 있습니다.",
            "전자신고 시 세액공제 혜택이 있습니다."
        ],
        "장부": [
            "복식부기 작성 시 추가 세액공제 혜택이 있습니다.",
            "매출/매입 증빙은 5년간 보관해야 합니다.",
            "전자기록으로 장부를 관리하면 편리하고 세무조사 대응이 용이합니다."
        ]
    }
    
    # 쿼리에 맞는 팁 찾기
    selected_tips = []
    for category, category_tips in tips.items():
        if category in query or any(keyword in query for keyword in category_tips):
            selected_tips.extend([f"[{category}] {tip}" for tip in category_tips])
    
    # 선택된 팁이 없는 경우 일반적인 팁 반환
    if not selected_tips:
        general_tips = [
            "매출/매입 증빙을 꼼꼼히 관리하면 세금 부담을 줄일 수 있습니다.",
            "사업용 경비는 반드시 사업자 명의 카드나 계좌로 결제하세요.",
            "정기적으로 세무사와 상담하여 세무 관리를 효율적으로 하세요.",
            "기장을 성실히 하면 다양한 세액공제 혜택을 받을 수 있습니다.",
            "직원이 있다면 4대보험 가입 및 원천세 신고에 주의하세요."
        ]
        return "개인사업자 절세 팁:\n\n" + "\n\n".join(general_tips)
    
    return "개인사업자 절세 팁:\n\n" + "\n\n".join(selected_tips)