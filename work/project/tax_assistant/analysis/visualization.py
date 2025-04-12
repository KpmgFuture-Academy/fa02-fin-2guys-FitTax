"""
데이터 시각화 모듈
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from tax_assistant.preprocessing.lotte_card import (
    DATE_PATTERNS, AMOUNT_PATTERNS, VAT_PATTERNS, MERCHANT_PATTERNS
)

def create_monthly_chart(df):
    """
    월별 사용 금액 차트 생성 - 정확한 필드명 사용
    
    Args:
        df: 전처리된 데이터프레임
        
    Returns:
        plotly 그래프 객체
    """
    import pandas as pd
    import plotly.express as px
    
    # 필요한 필드명 확인
    date_col = '매출일자'  # 날짜 필드
    amount_col = '매출금액'  # 금액 필드
    
    # 필드 존재 확인
    if date_col not in df.columns:
        return px.bar(
            pd.DataFrame({'월': ['필드 없음'], '금액': [0]}), 
            x='월', 
            y='금액',
            title=f'월별 사용 금액 (필드 {date_col}를 찾을 수 없음)'
        )
    
    if amount_col not in df.columns:
        return px.bar(
            pd.DataFrame({'월': ['필드 없음'], '금액': [0]}), 
            x='월', 
            y='금액',
            title=f'월별 사용 금액 (필드 {amount_col}를 찾을 수 없음)'
        )
    
    # 날짜 필드 확인 및 변환
    df_copy = df.copy()
    
    # 날짜 변환 (이미 변환되지 않은 경우)
    if not pd.api.types.is_datetime64_dtype(df_copy[date_col]):
        try:
            if pd.api.types.is_numeric_dtype(df_copy[date_col]):
                # Excel 날짜 숫자 형식 변환
                df_copy[date_col] = pd.to_datetime(df_copy[date_col], unit='D', origin='1899-12-30', errors='coerce')
            else:
                # 일반 문자열 형식 변환
                df_copy[date_col] = pd.to_datetime(df_copy[date_col], errors='coerce')
        except:
            pass
    
    # 거래월 필드 확인 및 생성
    if '거래월' not in df_copy.columns:
        if pd.api.types.is_datetime64_dtype(df_copy[date_col]):
            df_copy['거래월'] = df_copy[date_col].dt.strftime('%Y-%m')
        else:
            df_copy['거래월'] = '날짜오류'
    
    # 금액 필드가 숫자가 아닌 경우 변환
    if not pd.api.types.is_numeric_dtype(df_copy[amount_col]):
        try:
            df_copy[amount_col] = df_copy[amount_col].astype(str).str.replace(',', '').str.replace('원', '').astype(float)
        except:
            pass
    
    # 월별 합계 계산
    monthly_data = df_copy.groupby('거래월')[amount_col].sum().reset_index()
    
    # 데이터가 없는 경우 처리
    if monthly_data.empty:
        return px.bar(
            pd.DataFrame({'월': ['데이터 없음'], '금액': [0]}), 
            x='월', 
            y='금액',
            title='월별 사용 금액 (유효 데이터 없음)'
        )
    
    # '날짜오류' 행 제외
    if '날짜오류' in monthly_data['거래월'].values:
        error_amount = monthly_data.loc[monthly_data['거래월'] == '날짜오류', amount_col].sum()
        monthly_data = monthly_data[monthly_data['거래월'] != '날짜오류']
        # 모든 데이터가 날짜오류인 경우
        if monthly_data.empty:
            return px.bar(
                pd.DataFrame({'월': ['날짜오류'], '금액': [error_amount]}), 
                x='월', 
                y='금액',
                title='월별 사용 금액 (날짜 변환 실패)',
                text_auto=True
            )
    
    # 날짜 순으로 정렬 
    try:
        # YYYY-MM 형식의 거래월인 경우 정렬
        if all(monthly_data['거래월'].str.match(r'\d{4}-\d{2}')):
            monthly_data['정렬키'] = pd.to_datetime(monthly_data['거래월'] + '-01')
            monthly_data = monthly_data.sort_values('정렬키')
            monthly_data = monthly_data.drop(columns=['정렬키'])
    except:
        # 정렬 실패 시 원래 순서 유지
        pass
    
    # 차트 생성
    fig = px.bar(
        monthly_data, 
        x='거래월', 
        y=amount_col,
        title='월별 사용 금액',
        labels={'거래월': '월', amount_col: '금액'},
        text_auto=True
    )
    
    # 차트 스타일 수정
    fig.update_layout(
        xaxis_title='월',
        yaxis_title='금액 (원)',
        yaxis_tickformat=',',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Malgun Gothic, Arial", size=12),
        height=500
    )
    
    return fig

def create_merchant_chart(df, top_n=10):
    """
    가맹점별 사용 금액 차트 생성 - 정확한 필드명 사용
    
    Args:
        df: 전처리된 데이터프레임
        top_n: 상위 몇 개의 가맹점을 표시할지 결정
        
    Returns:
        plotly 그래프 객체
    """
    import pandas as pd
    import plotly.express as px
    
    # 필요한 필드명 확인
    merchant_col = '가맹점명'  # 가맹점 필드
    amount_col = '매출금액'  # 금액 필드
    
    # 필드 존재 확인
    if merchant_col not in df.columns:
        return px.bar(
            pd.DataFrame({'가맹점': ['필드 없음'], '금액': [0]}), 
            x='가맹점', 
            y='금액',
            title=f'가맹점별 사용 금액 (필드 {merchant_col}를 찾을 수 없음)'
        )
    
    if amount_col not in df.columns:
        return px.bar(
            pd.DataFrame({'가맹점': ['필드 없음'], '금액': [0]}), 
            x='가맹점', 
            y='금액',
            title=f'가맹점별 사용 금액 (필드 {amount_col}를 찾을 수 없음)'
        )
    
    # 데이터 복사 및 전처리
    df_clean = df.copy()
    
    # 금액 필드가 숫자가 아닌 경우 변환
    if not pd.api.types.is_numeric_dtype(df_clean[amount_col]):
        try:
            df_clean[amount_col] = df_clean[amount_col].astype(str).str.replace(',', '').str.replace('원', '').astype(float)
        except:
            # 변환 실패 시 더미 차트 반환
            return px.bar(
                pd.DataFrame({'가맹점': ['데이터 변환 오류'], '금액': [0]}), 
                x='가맹점', 
                y='금액',
                title='가맹점별 사용 금액 (금액 데이터 변환 오류)'
            )
    
    # 결측치 제거
    df_clean = df_clean.dropna(subset=[merchant_col, amount_col])
    
    # 빈 문자열 제거
    df_clean = df_clean[df_clean[merchant_col] != '']
    
    # 데이터가 없는 경우 처리
    if df_clean.empty:
        return px.bar(
            pd.DataFrame({'가맹점': ['데이터 없음'], '금액': [0]}), 
            x='가맹점', 
            y='금액',
            title='가맹점별 사용 금액 (유효 데이터 없음)'
        )
    
    # 가맹점별 합계
    merchant_summary = df_clean.groupby(merchant_col)[amount_col].sum().reset_index()
    
    # 금액 기준 내림차순 정렬 및 상위 N개 추출
    merchant_summary = merchant_summary.sort_values(by=amount_col, ascending=False).head(top_n)
    
    # 차트 생성
    fig = px.bar(
        merchant_summary, 
        x=merchant_col, 
        y=amount_col,
        title=f'가맹점별 사용 금액 (상위 {top_n}개)',
        labels={merchant_col: '가맹점', amount_col: '금액'},
        text_auto=True
    )
    
    # 차트 스타일 수정
    fig.update_layout(
        xaxis_title='가맹점',
        yaxis_title='금액 (원)',
        yaxis_tickformat=',',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Malgun Gothic, Arial", size=12),
        height=600
    )
    
    # 긴 가맹점명 처리
    fig.update_xaxes(tickangle=45)
    
    return fig

def create_category_chart(df):
    """
    카테고리별 지출 차트 생성 - 정확한 필드명 사용
    
    Args:
        df: 전처리된 데이터프레임
        
    Returns:
        plotly 그래프 객체
    """
    import pandas as pd
    import plotly.express as px
    
    if '카테고리' not in df.columns:
        # 더미 차트 반환
        return px.bar(
            pd.DataFrame({'카테고리': ['데이터 없음'], '금액': [0]}), 
            x='카테고리', 
            y='금액',
            title='카테고리별 지출 (카테고리 데이터 없음)'
        )
    
    # 금액 열 지정
    amount_col = '매출금액'
    
    if amount_col not in df.columns:
        # 더미 차트 반환
        return px.bar(
            pd.DataFrame({'카테고리': ['데이터 없음'], '금액': [0]}), 
            x='카테고리', 
            y='금액',
            title='카테고리별 지출 (금액 데이터 없음)'
        )
    
    # 데이터 전처리
    df_clean = df.copy()
    
    # 금액 필드가 숫자가 아닌 경우 변환
    if not pd.api.types.is_numeric_dtype(df_clean[amount_col]):
        try:
            df_clean[amount_col] = df_clean[amount_col].astype(str).str.replace(',', '').str.replace('원', '').astype(float)
        except:
            # 변환 실패 시 더미 차트 반환
            return px.bar(
                pd.DataFrame({'카테고리': ['데이터 변환 오류'], '금액': [0]}), 
                x='카테고리', 
                y='금액',
                title='카테고리별 지출 (금액 데이터 변환 오류)'
            )
    
    # 카테고리별 합계
    category_data = df_clean.groupby('카테고리')[amount_col].sum().reset_index()
    
    # 기타 카테고리가 너무 많은 경우 필터링 (기타 외 카테고리가 하나도 없으면 무시)
    if len(category_data) > 1 and '기타' in category_data['카테고리'].values:
        non_etc_count = len(category_data[category_data['카테고리'] != '기타'])
        if non_etc_count == 0:  # 모든 값이 '기타'인 경우
            import streamlit as st
            st.warning("모든 가맹점이 '기타'로 분류되었습니다. 카테고리 매핑을 확인하세요.")
        
    # 금액 기준 내림차순 정렬
    category_data = category_data.sort_values(by=amount_col, ascending=False)
    
    # 차트 생성
    fig = px.pie(
        category_data, 
        names='카테고리', 
        values=amount_col,
        title='카테고리별 지출 분석',
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    # 차트 스타일 수정
    fig.update_layout(
        legend_title='카테고리',
        font=dict(family="Malgun Gothic, Arial", size=12),
        height=500
    )
    
    # 금액 및 비율 표시 형식 변경
    fig.update_traces(
        texttemplate='%{label}<br>%{value:,}원<br>(%{percent})', 
        textposition='inside'
    )
    
    return fig

def create_category_bar_chart(df):
    """
    카테고리별 지출 막대 차트 생성 - 정확한 필드명 사용
    
    Args:
        df: 전처리된 데이터프레임
        
    Returns:
        plotly 그래프 객체
    """
    import pandas as pd
    import plotly.express as px
    
    if '카테고리' not in df.columns:
        # 더미 차트 반환
        return px.bar(
            pd.DataFrame({'카테고리': ['데이터 없음'], '금액': [0]}), 
            x='카테고리', 
            y='금액',
            title='카테고리별 지출 (카테고리 데이터 없음)'
        )
    
    # 금액 열 지정
    amount_col = '매출금액'
    
    if amount_col not in df.columns:
        # 더미 차트 반환
        return px.bar(
            pd.DataFrame({'카테고리': ['데이터 없음'], '금액': [0]}), 
            x='카테고리', 
            y='금액',
            title='카테고리별 지출 (금액 데이터 없음)'
        )
    
    # 데이터 전처리
    df_clean = df.copy()
    
    # 금액 필드가 숫자가 아닌 경우 변환
    if not pd.api.types.is_numeric_dtype(df_clean[amount_col]):
        try:
            df_clean[amount_col] = df_clean[amount_col].astype(str).str.replace(',', '').str.replace('원', '').astype(float)
        except:
            # 변환 실패 시 더미 차트 반환
            return px.bar(
                pd.DataFrame({'카테고리': ['데이터 변환 오류'], '금액': [0]}), 
                x='카테고리', 
                y='금액',
                title='카테고리별 지출 (금액 데이터 변환 오류)'
            )
    
    # 카테고리별 합계
    category_data = df_clean.groupby('카테고리')[amount_col].sum().reset_index()
    
    # 금액 기준 내림차순 정렬
    category_data = category_data.sort_values(by=amount_col, ascending=False)
    
    # 차트 생성
    fig = px.bar(
        category_data, 
        x='카테고리', 
        y=amount_col,
        title='카테고리별 지출 분석',
        color='카테고리',
        text_auto=True,
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    # 차트 스타일 수정
    fig.update_layout(
        xaxis_title='카테고리',
        yaxis_title='금액 (원)',
        yaxis_tickformat=',',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Malgun Gothic, Arial", size=12),
        height=500,
        showlegend=False
    )
    
    return fig

def create_daily_trend_chart(df):
    """
    일별 사용 금액 추이 차트 생성 - 정확한 필드명 사용
    
    Args:
        df: 전처리된 데이터프레임
        
    Returns:
        plotly 그래프 객체
    """
    import pandas as pd
    import plotly.express as px
    
    # 날짜 및 금액 필드 지정
    date_col = '매출일자'
    amount_col = '매출금액'
    
    if date_col not in df.columns or amount_col not in df.columns:
        # 더미 차트 반환
        return px.line(
            pd.DataFrame({'날짜': ['데이터 없음'], '금액': [0]}), 
            x='날짜', 
            y='금액',
            title='일별 지출 추이 (데이터를 찾을 수 없음)'
        )
    
    # 데이터 전처리
    df_clean = df.copy()
    
    # 날짜 필드 변환
    if not pd.api.types.is_datetime64_dtype(df_clean[date_col]):
        try:
            if pd.api.types.is_numeric_dtype(df_clean[date_col]):
                # Excel 날짜 숫자 형식 변환
                df_clean[date_col] = pd.to_datetime(df_clean[date_col], unit='D', origin='1899-12-30', errors='coerce')
            else:
                # 일반 문자열 형식 변환
                df_clean[date_col] = pd.to_datetime(df_clean[date_col], errors='coerce')
        except:
            # 날짜 변환 실패 시 더미 차트 반환
            return px.line(
                pd.DataFrame({'날짜': ['변환 오류'], '금액': [0]}), 
                x='날짜', 
                y='금액',
                title='일별 지출 추이 (날짜 변환 오류)'
            )
    
    # 금액 필드가 숫자가 아닌 경우 변환
    if not pd.api.types.is_numeric_dtype(df_clean[amount_col]):
        try:
            df_clean[amount_col] = df_clean[amount_col].astype(str).str.replace(',', '').str.replace('원', '').astype(float)
        except:
            # 변환 실패 시 더미 차트 반환
            return px.line(
                pd.DataFrame({'날짜': ['데이터 변환 오류'], '금액': [0]}), 
                x='날짜', 
                y='금액',
                title='일별 지출 추이 (금액 데이터 변환 오류)'
            )
    
    # 일별 합계
    daily_data = df_clean.groupby(date_col)[amount_col].sum().reset_index()
    
    # 데이터가 없는 경우 처리
    if daily_data.empty:
        return px.line(
            pd.DataFrame({'날짜': ['데이터 없음'], '금액': [0]}), 
            x='날짜', 
            y='금액',
            title='일별 지출 추이 (유효 데이터 없음)'
        )
    
    # 날짜 정렬
    daily_data = daily_data.sort_values(by=date_col)
    
    # 차트 생성
    fig = px.line(
        daily_data, 
        x=date_col, 
        y=amount_col,
        title='일별 지출 추이',
        markers=True
    )
    
    # 차트 스타일 수정
    fig.update_layout(
        xaxis_title='날짜',
        yaxis_title='금액 (원)',
        yaxis_tickformat=',',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Malgun Gothic, Arial", size=12),
        height=500
    )
    
    return fig


def create_tax_deduction_chart(df):
    """
    부가세 공제 가능/불가능 분석 차트
    """
    import pandas as pd
    import plotly.express as px
    import streamlit as st
    
    if '부가세공제여부' not in df.columns:
        return px.pie(
            pd.DataFrame({'부가세공제': ['데이터 없음'], '금액': [0]}), 
            names='부가세공제', 
            values='금액',
            title='부가세 공제 가능/불가능 분석 (데이터 없음)'
        )
    
    # 디버깅: 부가세공제여부 값 확인
    #st.write("부가세공제여부 데이터 타입:", df['부가세공제여부'].dtype)
    #st.write("부가세공제여부 샘플 값:", df['부가세공제여부'].head(5).tolist())
    #st.write("부가세공제여부 고유값:", df['부가세공제여부'].unique())
        # 금액 열 지정
    amount_col = '매출금액'
    
    if amount_col not in df.columns:
        return px.pie(
            pd.DataFrame({'부가세공제': ['데이터 없음'], '금액': [0]}), 
            names='부가세공제', 
            values='금액',
            title='부가세 공제 가능/불가능 분석 (금액 데이터 없음)'
        )
    
    # 데이터 전처리
    df_clean = df.copy()
    
    # 부가세공제여부 문자열 'True'/'False'를 불리언으로 변환
    try:
        if df_clean['부가세공제여부'].dtype == 'object':
            # 'True'/'False' 문자열을 불리언으로 변환
            df_clean['부가세공제여부_bool'] = df_clean['부가세공제여부'].map(
                lambda x: True if str(x).lower() == 'true' else False
            )
            #st.write("변환 후 부가세공제여부_bool 값:", df_clean['부가세공제여부_bool'].head(5).tolist())
        else:
            df_clean['부가세공제여부_bool'] = df_clean['부가세공제여부']
    except Exception as e:
        st.error(f"부가세공제여부 변환 오류: {str(e)}")
    
    # 공제여부 레이블 생성
    df_clean['공제여부'] = df_clean['부가세공제여부_bool'].map({True: '공제 가능', False: '공제 불가능'})
    
    # 누락된 값 처리
    df_clean['공제여부'] = df_clean['공제여부'].fillna('공제 불가능')
    
    # 디버깅: 공제여부 결과 확인
    #st.write("공제여부 결과:", df_clean['공제여부'].value_counts().to_dict())
    
    # 금액 필드가 숫자가 아닌 경우 변환
    if not pd.api.types.is_numeric_dtype(df_clean[amount_col]):
        try:
            df_clean[amount_col] = pd.to_numeric(df_clean[amount_col], errors='coerce')
        except:
            return px.pie(
                pd.DataFrame({'부가세공제': ['데이터 변환 오류'], '금액': [0]}), 
                names='부가세공제', 
                values='금액',
                title='부가세 공제 가능/불가능 분석 (금액 데이터 변환 오류)'
            )
    
    # 부가세 공제 가능/불가능별 합계
    deduction_data = df_clean.groupby('공제여부')[amount_col].sum().reset_index()
    st.write("최종 차트 데이터:", deduction_data)
    
    # 차트 생성
    fig = px.pie(
        deduction_data, 
        names='공제여부', 
        values=amount_col,
        title='부가세 공제 가능/불가능 분석',
        color='공제여부',
        color_discrete_map={'공제 가능': 'green', '공제 불가능': 'red'},
        hole=0.4
    )
    
    # 차트 스타일 수정
    fig.update_layout(
        legend_title='부가세 공제 여부',
        font=dict(family="Malgun Gothic, Arial", size=12),
        height=400
    )
    
    # 금액 및 비율 표시 형식 변경
    fig.update_traces(
        texttemplate='%{label}<br>%{value:,}원<br>(%{percent})', 
        textposition='inside'
    )
    
    return fig

def create_category_heatmap(df):
    """
    월별 카테고리 지출 히트맵 생성 - 정확한 필드명 사용
    
    Args:
        df: 전처리된 데이터프레임
        
    Returns:
        plotly 그래프 객체
    """
    import pandas as pd
    import plotly.express as px
    import numpy as np
    
    # 필요한 필드 확인
    if '카테고리' not in df.columns or '거래월' not in df.columns:
        # 필요한 필드가 없는 경우 - 매출일자에서 거래월 생성 시도
        if '카테고리' in df.columns and '매출일자' in df.columns:
            df_copy = df.copy()
            
            # 날짜 변환
            if not pd.api.types.is_datetime64_dtype(df_copy['매출일자']):
                try:
                    if pd.api.types.is_numeric_dtype(df_copy['매출일자']):
                        df_copy['매출일자'] = pd.to_datetime(df_copy['매출일자'], unit='D', origin='1899-12-30', errors='coerce')
                    else:
                        df_copy['매출일자'] = pd.to_datetime(df_copy['매출일자'], errors='coerce')
                except:
                    # 변환 실패 시 더미 차트 반환
                    return px.imshow(
                        [[0]],
                        x=['데이터 없음'],
                        y=['데이터 없음'],
                        title='월별 카테고리 지출 분석 (날짜 변환 실패)'
                    )
            
            # 변환 성공 시 거래월 생성
            if pd.api.types.is_datetime64_dtype(df_copy['매출일자']):
                df_copy['거래월'] = df_copy['매출일자'].dt.strftime('%Y-%m')
            else:
                # 변환 실패 시 더미 차트 반환
                return px.imshow(
                    [[0]],
                    x=['데이터 없음'],
                    y=['데이터 없음'],
                    title='월별 카테고리 지출 분석 (날짜 변환 실패)'
                )
        else:
            # 필요한 필드가 없는 경우 더미 차트 반환
            return px.imshow(
                [[0]],
                x=['데이터 없음'],
                y=['데이터 없음'],
                title='월별 카테고리 지출 분석 (필요한 필드 없음)'
            )
    else:
        df_copy = df.copy()
    
    # 금액 열 지정
    amount_col = '매출금액'
    
    if amount_col not in df_copy.columns:
        # 더미 차트 반환
        return px.imshow(
            [[0]],
            x=['데이터 없음'],
            y=['데이터 없음'],
            title='월별 카테고리 지출 분석 (금액 데이터 없음)'
        )
    
    # 금액 필드가 숫자가 아닌 경우 변환
    if not pd.api.types.is_numeric_dtype(df_copy[amount_col]):
        try:
            df_copy[amount_col] = df_copy[amount_col].astype(str).str.replace(',', '').str.replace('원', '').astype(float)
        except:
            # 변환 실패 시 더미 차트 반환
            return px.imshow(
                [[0]],
                x=['데이터 없음'],
                y=['데이터 없음'],
                title='월별 카테고리 지출 분석 (금액 데이터 변환 실패)'
            )
    
    # 월별 & 카테고리별 합계
    try:
        heatmap_data = df_copy.pivot_table(
            index='거래월',
            columns='카테고리',
            values=amount_col,
            aggfunc='sum',
            fill_value=0
        ).reset_index()
    except Exception as e:
        # 피벗 테이블 생성 실패 시 더미 차트 반환
        return px.imshow(
            [[0]],
            x=['데이터 없음'],
            y=['데이터 없음'],
            title=f'월별 카테고리 지출 분석 (피벗 테이블 생성 실패: {str(e)})'
        )
    
    # 날짜 형식 변환하여 정렬 (YYYY-MM 형식 가정)
    try:
        heatmap_data['정렬키'] = pd.to_datetime(heatmap_data['거래월'] + '-01', errors='coerce')
        heatmap_data = heatmap_data.sort_values('정렬키')
        heatmap_data = heatmap_data.drop(columns=['정렬키'])
    except:
        # 정렬 실패 시 원래 데이터 유지
        pass
    
    # 피벗 테이블 변환
    heatmap_matrix = heatmap_data.set_index('거래월')
    
    # 히트맵 생성
    fig = px.imshow(
        heatmap_matrix.values,
        x=heatmap_matrix.columns,
        y=heatmap_matrix.index,
        labels=dict(x='카테고리', y='거래월', color='금액'),
        title='월별 카테고리 지출 분석',
        color_continuous_scale='Viridis',
        text_auto=True
    )
    
    # 차트 스타일 수정
    fig.update_layout(
        font=dict(family="Malgun Gothic, Arial", size=12),
        height=600
    )
    
    return fig

def create_vat_comparison_chart(df):
    """
    월별 금액 및 부가세 비교 차트 생성 - 정확한 필드명 사용
    
    Args:
        df: 전처리된 데이터프레임
        
    Returns:
        plotly 그래프 객체
    """
    import pandas as pd
    import plotly.graph_objects as go
    import plotly.express as px
    
    # 날짜 필드 지정
    date_col = '매출일자'
    
    # 금액 및 부가세 필드 지정
    amount_col = '매출금액'
    vat_col = '부가세'
    
    if date_col not in df.columns or amount_col not in df.columns:
        # 더미 차트 반환
        return px.bar(
            pd.DataFrame({'월': ['데이터 없음'], '금액': [0]}), 
            x='월', 
            y='금액',
            title='월별 금액 및 부가세 비교 (필요한 데이터 없음)'
        )
    
    # 데이터 전처리
    df_clean = df.copy()
    
    # 날짜 데이터 변환
    if not pd.api.types.is_datetime64_dtype(df_clean[date_col]):
        try:
            if pd.api.types.is_numeric_dtype(df_clean[date_col]):
                df_clean[date_col] = pd.to_datetime(df_clean[date_col], unit='D', origin='1899-12-30', errors='coerce')
            else:
                df_clean[date_col] = pd.to_datetime(df_clean[date_col], errors='coerce')
        except:
            # 날짜 변환 실패 시 더미 차트 반환
            return px.bar(
                pd.DataFrame({'월': ['변환 오류'], '금액': [0]}), 
                x='월', 
                y='금액',
                title='월별 금액 및 부가세 비교 (날짜 변환 오류)'
            )
    
    # 거래월 필드 확인 및 생성
    if '거래월' in df_clean.columns:
        month_col = '거래월'
    elif pd.api.types.is_datetime64_dtype(df_clean[date_col]):
        df_clean['거래월'] = df_clean[date_col].dt.strftime('%Y-%m')
        month_col = '거래월'
    else:
        # 거래월 생성 실패 시 더미 차트 반환
        return px.bar(
            pd.DataFrame({'월': ['변환 오류'], '금액': [0]}), 
            x='월', 
            y='금액',
            title='월별 금액 및 부가세 비교 (거래월 생성 실패)'
        )
    
    # 금액 필드가 숫자가 아닌 경우 변환
    if not pd.api.types.is_numeric_dtype(df_clean[amount_col]):
        try:
            df_clean[amount_col] = df_clean[amount_col].astype(str).str.replace(',', '').str.replace('원', '').astype(float)
        except:
            # 변환 실패 시 더미 차트 반환
            return px.bar(
                pd.DataFrame({'월': ['변환 오류'], '금액': [0]}), 
                x='월', 
                y='금액',
                title='월별 금액 및 부가세 비교 (금액 데이터 변환 오류)'
            )
    
    # 부가세가 없는 경우 추정
    if vat_col not in df_clean.columns:
        df_clean['예상부가세'] = df_clean[amount_col] / 11
        vat_col = '예상부가세'
    elif not pd.api.types.is_numeric_dtype(df_clean[vat_col]):
        try:
            # 부가세 필드 숫자 변환 시도
            df_clean[vat_col] = df_clean[vat_col].astype(str).str.replace(',', '').str.replace('원', '').astype(float)
        except:
            # 변환 실패 시 추정값 사용
            df_clean['예상부가세'] = df_clean[amount_col] / 11
            vat_col = '예상부가세'
    
    # 월별 집계
    monthly_data = df_clean.groupby(month_col).agg({
        amount_col: 'sum',
        vat_col: 'sum'
    }).reset_index()
    
    # 데이터가 없는 경우 처리
    if monthly_data.empty:
        return px.bar(
            pd.DataFrame({'월': ['데이터 없음'], '금액': [0]}), 
            x='월', 
            y='금액',
            title='월별 금액 및 부가세 비교 (집계 데이터 없음)'
        )
    
    # 월 순서로 정렬
    try:
        # YYYY-MM 형식인 경우
        monthly_data['정렬키'] = pd.to_datetime(monthly_data[month_col] + '-01')
        monthly_data = monthly_data.sort_values(by='정렬키')
        monthly_data = monthly_data.drop(columns=['정렬키'])
    except:
        # 정렬 실패 시 원래 순서 유지
        pass
    
    # 차트 생성
    fig = go.Figure()
    
    # 공급가액 바 추가 (매출금액 - 부가세)
    supply_values = monthly_data[amount_col] - monthly_data[vat_col]
    fig.add_trace(go.Bar(
        x=monthly_data[month_col],
        y=supply_values,
        name='공급가액',
        text=supply_values.apply(lambda x: f"{x:,.0f}원"),
        textposition='auto'
    ))
    
    # 부가세 바 추가
    fig.add_trace(go.Bar(
        x=monthly_data[month_col],
        y=monthly_data[vat_col],
        name='부가세',
        text=monthly_data[vat_col].apply(lambda x: f"{x:,.0f}원"),
        textposition='auto'
    ))
    
    # 차트 레이아웃 설정
    fig.update_layout(
        title='월별 금액 및 부가세 비교',
        xaxis_title='월',
        yaxis_title='금액 (원)',
        yaxis_tickformat=',',
        barmode='stack',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Malgun Gothic, Arial", size=12),
        height=500
    )
    
    return fig


def create_pie_chart(df):
    """
    지출 구성 원형 차트 생성 - 정확한 필드명 사용
    
    Args:
        df: 전처리된 데이터프레임
        
    Returns:
        plotly 그래프 객체
    """
    import pandas as pd
    import plotly.express as px
    
    # 가맹점 필드 및 금액 필드 지정
    merchant_col = '가맹점명'
    amount_col = '매출금액'
    
    if merchant_col not in df.columns or amount_col not in df.columns:
        # 더미 차트 반환
        return px.pie(
            pd.DataFrame({'가맹점': ['데이터 없음'], '금액': [0]}), 
            names='가맹점', 
            values='금액',
            title='지출 구성 (데이터를 찾을 수 없음)'
        )
    
    # 데이터 전처리
    df_clean = df.copy()
    
    # 금액 필드가 숫자가 아닌 경우 변환
    if not pd.api.types.is_numeric_dtype(df_clean[amount_col]):
        try:
            df_clean[amount_col] = df_clean[amount_col].astype(str).str.replace(',', '').str.replace('원', '').astype(float)
        except:
            # 변환 실패 시 더미 차트 반환
            return px.pie(
                pd.DataFrame({'가맹점': ['데이터 변환 오류'], '금액': [0]}), 
                names='가맹점', 
                values='금액',
                title='지출 구성 (금액 데이터 변환 오류)'
            )
    
    # 결측치 및 빈 문자열 제거
    df_clean = df_clean.dropna(subset=[merchant_col, amount_col])
    df_clean = df_clean[df_clean[merchant_col] != '']
    
    # 데이터가 없는 경우 처리
    if df_clean.empty:
        return px.pie(
            pd.DataFrame({'가맹점': ['데이터 없음'], '금액': [0]}), 
            names='가맹점', 
            values='금액',
            title='지출 구성 (유효 데이터 없음)'
        )
    
    # 가맹점별 합계
    merchant_summary = df_clean.groupby(merchant_col)[amount_col].sum().reset_index()
    
    # 상위 5개 가맹점 추출, 나머지는 '기타'로 처리
    top_merchants = merchant_summary.sort_values(by=amount_col, ascending=False).head(5)
    
    # 기타 금액 계산
    other_amount = merchant_summary[amount_col].sum() - top_merchants[amount_col].sum()
    
    if other_amount > 0:
        other_row = pd.DataFrame({merchant_col: ['기타'], amount_col: [other_amount]})
        pie_data = pd.concat([top_merchants, other_row], ignore_index=True)
    else:
        pie_data = top_merchants
    
    # 차트 생성
    fig = px.pie(
        pie_data, 
        names=merchant_col, 
        values=amount_col,
        title='지출 구성',
        hole=0.4
    )
    
    # 차트 스타일 수정
    fig.update_layout(
        legend_title='가맹점',
        font=dict(family="Malgun Gothic, Arial", size=12),
        height=500
    )
    
    # 금액 및 비율 표시 형식 변경
    fig.update_traces(
        texttemplate='%{label}<br>%{value:,}원<br>(%{percent})', 
        textposition='inside'
    )
    
    return fig
