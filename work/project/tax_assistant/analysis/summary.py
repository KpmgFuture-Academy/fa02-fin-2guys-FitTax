"""
데이터 요약 모듈
"""
import pandas as pd
from tax_assistant.preprocessing.lotte_card import (
    DATE_PATTERNS, AMOUNT_PATTERNS, VAT_PATTERNS, MERCHANT_PATTERNS, CATEGORY_PATTERNS
)
#from tax_assistant.chatbot.tools import analyze_chart
from tax_assistant.chatbot.tools import analyze_chart

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
    

def calculate_vat_summary(df):
    """
    부가세 신고를 위한 요약 정보 계산
    
    Args:
        df: 전처리된 데이터프레임
    
    Returns:
        부가세 요약 정보가 담긴 데이터프레임
    """
    if df is None or len(df) == 0:
        return pd.DataFrame()
    
    # 부가세 열 식별
    vat_col = next((col for col in df.columns 
                   if any(tax_term in col.lower() for tax_term in VAT_PATTERNS)), None)
    
    # 금액 열 식별
    amount_col = next((col for col in df.columns 
                      if any(amount_term in col.lower() for amount_term in AMOUNT_PATTERNS) 
                      and col != vat_col), None)
    
    # 날짜 열 식별
    date_col = next((col for col in df.columns 
                    if any(date_term in col.lower() for date_term in DATE_PATTERNS)), None)
    
    # 구분 열 식별
    category_col = next((col for col in df.columns 
                        if any(category_term in col.lower() for category_term in CATEGORY_PATTERNS + ['구분'])), None)
    
    # 열을 식별하지 못한 경우 예외 처리
    if not all([date_col, amount_col]):
        return pd.DataFrame({'오류': ['데이터에서 필요한 열을 찾을 수 없습니다']})
    
    # 날짜 데이터 변환
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    
    # 요약 데이터 준비
    if '거래월' in df.columns:
        month_col = '거래월'
    else:
        df['거래월'] = df[date_col].dt.strftime('%Y-%m')
        month_col = '거래월'
    
    # 매입/매출 구분이 있는 경우
    if category_col and '구분' in category_col.lower():
        # 월별 & 구분별 요약
        agg_dict = {amount_col: 'sum'}
        if vat_col:
            agg_dict[vat_col] = 'sum'
        
        monthly_summary = df.groupby([month_col, category_col]).agg(agg_dict).reset_index()
        
        # 전체 합계 행 추가
        total_row = pd.DataFrame({
            month_col: ['합계'],
            category_col: [''],
            amount_col: [df[amount_col].sum()]
        })
        
        if vat_col:
            total_row[vat_col] = [df[vat_col].sum()]
        
        monthly_summary = pd.concat([monthly_summary, total_row], ignore_index=True)
        
    else:
        # 월별 요약 (구분 없음)
        agg_dict = {amount_col: 'sum'}
        if vat_col:
            agg_dict[vat_col] = 'sum'
        
        monthly_summary = df.groupby(month_col).agg(agg_dict).reset_index()
        
        # 전체 합계 행 추가
        total_row = pd.DataFrame({
            month_col: ['합계'],
            amount_col: [df[amount_col].sum()]
        })
        
        if vat_col:
            total_row[vat_col] = [df[vat_col].sum()]
        
        monthly_summary = pd.concat([monthly_summary, total_row], ignore_index=True)
    
    return monthly_summary

def get_merchant_summary(df, top_n=10):
    """
    가맹점별 사용 금액 요약
    
    Args:
        df: 전처리된 데이터프레임
        top_n: 상위 몇 개의 가맹점을 표시할지 결정
        
    Returns:
        가맹점별 요약 정보 데이터프레임
    """
    if df is None or len(df) == 0:
        return pd.DataFrame()
    
    # 가맹점 열 식별
    merchant_col = next((col for col in df.columns 
                        if any(store_term in col.lower() for store_term in MERCHANT_PATTERNS)), None)
    
    # 금액 열 식별
    amount_col = next((col for col in df.columns 
                      if any(amount_term in col.lower() for amount_term in AMOUNT_PATTERNS)), None)
    
    if not merchant_col or not amount_col:
        return pd.DataFrame({'오류': ['데이터에서 필요한 열을 찾을 수 없습니다']})
    
    # 가맹점별 합계
    merchant_summary = df.groupby(merchant_col)[amount_col].sum().reset_index()
    
    # 금액 기준 내림차순 정렬
    merchant_summary = merchant_summary.sort_values(by=amount_col, ascending=False).head(top_n)
    
    # 비율 계산
    total_amount = merchant_summary[amount_col].sum()
    merchant_summary['비율'] = (merchant_summary[amount_col] / total_amount * 100).round(1)
    merchant_summary['비율'] = merchant_summary['비율'].astype(str) + '%'
    
    return merchant_summary

def get_category_summary(df):
    """
    카테고리별 금액 요약
    
    Args:
        df: 전처리된 데이터프레임
        
    Returns:
        카테고리별 요약 정보
    """
    if '카테고리' not in df.columns:
        return pd.DataFrame({'오류': ['카테고리 정보가 없습니다.']})
    
    # 금액 열 식별
    amount_col = next((col for col in df.columns 
                     if any(amount_term in col.lower() for amount_term in AMOUNT_PATTERNS)), None)
    
    if not amount_col:
        return pd.DataFrame({'오류': ['금액 컬럼을 찾을 수 없습니다.']})
    
    # 카테고리별 합계
    category_summary = df.groupby('카테고리')[amount_col].sum().reset_index()
    
    # 금액 기준 내림차순 정렬
    category_summary = category_summary.sort_values(by=amount_col, ascending=False)
    
    # 비율 계산
    total_amount = category_summary[amount_col].sum()
    category_summary['비율'] = (category_summary[amount_col] / total_amount * 100).round(1)
    category_summary['비율'] = category_summary['비율'].astype(str) + '%'
    
    return category_summary