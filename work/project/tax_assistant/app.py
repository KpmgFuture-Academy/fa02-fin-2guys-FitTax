"""
개인사업자 부가세 신고 어시스턴트 메인 애플리케이션
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from tax_assistant.analysis.visualization import *

from flask import Flask, request, render_template
from tax_assistant.chatbot.agent import TaxAssistantSession

# 한글 폰트 설정 (matplotlib)
matplotlib.rcParams['font.family'] = 'Malgun Gothic'  # 윈도우의 경우
matplotlib.rcParams['axes.unicode_minus'] = False     # 마이너스 기호 깨짐 방지

# 모듈 임포트
# preprocessing 모듈 임포트 제거됨
from tax_assistant.analysis.summary import (
    calculate_vat_summary, 
    get_merchant_summary,
    get_category_summary,
    analyze_chart
)

from tax_assistant.analysis.visualization import (
    create_monthly_chart,
    create_merchant_chart,
    create_pie_chart,
    create_category_chart,
    create_category_bar_chart,
    create_daily_trend_chart,
    create_category_heatmap,
    create_tax_deduction_chart,
    create_vat_comparison_chart
)

from tax_assistant.chatbot.tools import (
    analyze_dataframe,
    update_dataframe,
    get_tax_advice,
    calculate_tax,
    simulate_hometax_report,
    get_tax_saving_tips,
    analyze_chart,  # 여기로 이동
    get_young_entrepreneur_advice,  # 새 도구 추가
    get_business_card_strategy,
    get_first_vat_report_guide
)


from  tax_assistant.utils import (
    save_uploaded_file,
    cleanup_temp_file,
    get_current_tax_period,
    get_tax_due_date,
    export_to_csv
)
#from langchain.callbacks import StreamlitCallbackHandler
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler

def main():
    """메인 Streamlit 애플리케이션"""
    # 페이지 설정
    st.set_page_config(page_title="개인사업자 부가세 신고 어시스턴트", layout="wide")
    
    # 세션 상태 초기화
    if 'processed_df' not in st.session_state:
        st.session_state.processed_df = None

    if 'tax_assistant' not in st.session_state:
        st.session_state.tax_assistant = TaxAssistantSession()
    #if 'df_tool' not in st.session_state:
    #    st.session_state.df_tool = DataFrameTool()
    
    # 사이드바 구성
    st.sidebar.title("개인사업자 부가세 신고 어시스턴트")
    st.sidebar.image("https://i.ibb.co/qjSGt5R/tax-assistant.png", width=200)  # 임의의 이미지 URL (실제 구현 시 로컬 이미지 사용)
    
    # 사이드바 과세기간 설정
    st.sidebar.subheader("현재 과세기간")
    tax_period = st.sidebar.selectbox(
        "과세기간 선택",
        [
            f"{datetime.now().year}년 1기 (1월~6월)",
            f"{datetime.now().year}년 2기 (7월~12월)",
            f"{datetime.now().year-1}년 1기 (1월~6월)",
            f"{datetime.now().year-1}년 2기 (7월~12월)"
        ],
        index=0
    )
    st.session_state.tax_assistant.tax_period = tax_period
    
    # 신고 기한 표시
    st.sidebar.info(f"신고 기한: {get_tax_due_date(tax_period)}")
    
    # OpenAI API 키 입력
    #openai_api_key = st.sidebar.text_input("OpenAI API 키 입력", type="password")

    # OpenAI API 키 미리 입력 (프로토타입용)
    openai_api_key = st.sidebar.text_input("OpenAI API 키 입력", 
                                      value="",  # 여기에 실제 API 키를 넣으세요
                                      type="password")

    
    # 탭 구성
    tab1, tab2, tab3 = st.tabs(["데이터 업로드", "챗봇 어시스턴트", "세금 계산기"])
    
    # 탭 1: 데이터 업로드 (전처리 대신)
    with tab1:
        st.header("데이터 업로드")
        
        uploaded_file = st.file_uploader("전처리된 엑셀/CSV 파일을 업로드하세요", type=['xls', 'xlsx', 'csv'])
        
        if uploaded_file is not None:
            try:
                # 파일 확장자 확인
                file_extension = uploaded_file.name.split('.')[-1].lower()
                
                with st.spinner("데이터 로드 중..."):
                    # 파일 형식에 따라 데이터프레임으로 변환
                    if file_extension == 'csv':
                        processed_df = pd.read_csv(uploaded_file, encoding='utf-8')
                    else:  # xls, xlsx 파일
                        # 모든 데이터를 문자열로 로드
                        processed_df = pd.read_excel(uploaded_file, dtype=str)
                    
                    # 날짜 필드(매출일자) 처리 - 텍스트 형식 날짜 처리
                    if '매출일자' in processed_df.columns:
                        # 원본 형식 확인
                        #st.write("원본 매출일자 형식:", processed_df['매출일자'].dtype)
                        #st.write("매출일자 샘플:", processed_df['매출일자'].head(3).tolist())
                        
                        # 숫자 문자열을 정수로 변환한 다음 Excel 날짜로 변환
                        try:
                            # 먼저 문자열을 정수로 변환
                            date_numbers = processed_df['매출일자'].astype(float).astype(int)
                            
                            # Excel의 일련번호를 pandas datetime으로 변환 (1899년 12월 30일 기준)
                            processed_df['매출일자'] = pd.to_datetime(date_numbers, unit='D', origin='1899-12-30')
                            
                            # 변환 결과 확인
                           # st.success("날짜 변환 성공!")
                            #st.write("변환된 매출일자 샘플:", processed_df['매출일자'].head(3).dt.strftime('%Y-%m-%d').tolist())
                            
                            # 거래월 추가
                            processed_df['거래월'] = processed_df['매출일자'].dt.strftime('%Y-%m')
                        except Exception as e:
                            st.error(f"날짜 변환 중 오류 발생: {str(e)}")
                   # 매출금액 및 부가세 데이터 처리
                    try:
                        # 매출금액 처리
                        if '매출금액' in processed_df.columns:
                            # 매출금액을 문자열로 변환 후 숫자만 남기기
                            processed_df['매출금액'] = processed_df['매출금액'].astype(str).str.replace(r'[^0-9.]', '', regex=True)
                            # 앞 8자리만 유지
                            processed_df['매출금액'] = processed_df['매출금액'].apply(lambda x: x[:8] if len(x) > 8 else x)
                            # 숫자로 변환
                            processed_df['매출금액'] = pd.to_numeric(processed_df['매출금액'], errors='coerce')
                           # st.success("매출금액 데이터 정리 완료!")
                          #  st.write("처리된 매출금액 샘플:", processed_df['매출금액'].head(3).tolist())
                        
                        # 부가세 처리
                        if '부가세' in processed_df.columns:
                            # 부가세를 문자열로 변환 후 숫자만 남기기
                            processed_df['부가세'] = processed_df['부가세'].astype(str).str.replace(r'[^0-9.]', '', regex=True)
                            # 앞 5자리만 유지
                            processed_df['부가세'] = processed_df['부가세'].apply(lambda x: x[:5] if len(x) > 5 else x)
                            # 숫자로 변환
                            processed_df['부가세'] = pd.to_numeric(processed_df['부가세'], errors='coerce')
                            st.success("부가세 데이터 정리 완료!")
                            #st.write("처리된 부가세 샘플:", processed_df['부가세'].head(3).tolist())
                            
                            # 부가세 값 검증: 매출금액의 10%를 초과하면 매출금액의 10%로 설정
                            if '매출금액' in processed_df.columns:
                                mask = (processed_df['부가세'] > processed_df['매출금액'] * 0.1) & (processed_df['매출금액'] > 0)
                                processed_df.loc[mask, '부가세'] = processed_df.loc[mask, '매출금액'] * 0.1
                                
                    except Exception as e:
                        st.error(f"데이터 처리 중 오류 발생: {str(e)}")
                        
                        # 로직이 실패하면 기본 값으로 설정
                        if '매출금액' in processed_df.columns:
                            try:
                                # 매출금액의 문자열 길이를 확인하고 숫자 변환
                                processed_df['매출금액_길이'] = processed_df['매출금액'].astype(str).apply(len)
                                avg_length = processed_df['매출금액_길이'].mean()
                                
                                if avg_length > 10:  # 비정상적으로 긴 숫자들
                                    st.warning(f"매출금액 평균 길이: {avg_length}자리. 값이 비정상적으로 큽니다.")
                                    # 임의 값으로 대체
                                    default_values = [100000, 200000, 300000, 150000, 250000]
                                    processed_df['매출금액'] = [default_values[i % len(default_values)] for i in range(len(processed_df))]
                                
                                processed_df = processed_df.drop('매출금액_길이', axis=1)
                            except:
                                pass
                        
                        if '부가세' in processed_df.columns and '매출금액' in processed_df.columns:
                            try:
                                # 매출금액이 숫자라면 부가세 추정
                                if pd.api.types.is_numeric_dtype(processed_df['매출금액']):
                                    processed_df['부가세'] = processed_df['매출금액'] * 0.1
                            except:
                                pass
                    
                    # # 금액 필드(매출금액) 숫자 변환 확인
                    # if '매출금액' in processed_df.columns and not pd.api.types.is_numeric_dtype(processed_df['매출금액']):
                    #     try:
                    #         # 콤마 등 제거 후 숫자로 변환
                    #         processed_df['매출금액'] = processed_df['매출금액'].astype(str).str.replace(',', '').str.replace('원', '').astype(float)
                    #         st.success("'매출금액' 필드가 숫자로 변환되었습니다.")
                    #     except Exception as e:
                    #         st.warning(f"'매출금액' 필드 숫자 변환 중 오류: {str(e)}")
                    
                    st.session_state.processed_df = processed_df
                    update_dataframe(processed_df)
                
                st.success("파일이 성공적으로 로드되었습니다!")
                
                # 데이터 미리보기
                st.subheader("데이터 미리보기")
                st.dataframe(processed_df.head())
                
                # 전체 데이터 및 사용된 열 정보
                col1, col2 = st.columns(2)
                with col1:
                    st.info(f"총 거래 수: {len(processed_df)}")
                with col2:
                    st.info(f"사용된 필드: {', '.join(processed_df.columns)}")
                
                # 부가세 요약 정보
                st.subheader("부가세 요약")
                summary_df = calculate_vat_summary(processed_df)
                st.dataframe(summary_df)
                
                # 데이터 시각화
                st.subheader("데이터 시각화")
                
                viz_tab1, viz_tab2, viz_tab3, viz_tab4, viz_tab5 = st.tabs([
                     "월별 사용 금액", 
                     "카테고리별 분석", 
                     "가맹점별 분석", 
                     "일별 사용 추이", 
                      "부가세 분석"
                        ])
                
                with viz_tab1:
                    # 월별 차트 - 수정된 함수 호출
                    monthly_chart = create_monthly_chart(processed_df)
                    st.plotly_chart(monthly_chart, use_container_width=True)
                    
                    # 월별 카테고리 히트맵
                    st.subheader("월별 카테고리 지출 히트맵")
                    heatmap_chart = create_category_heatmap(processed_df)
                    st.plotly_chart(heatmap_chart, use_container_width=True)

                with viz_tab2:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # 카테고리별 파이 차트
                        category_pie_chart = create_category_chart(processed_df)
                        st.plotly_chart(category_pie_chart, use_container_width=True)
                    
                    with col2:
                        # 카테고리별 바 차트
                        category_bar_chart = create_category_bar_chart(processed_df)
                        st.plotly_chart(category_bar_chart, use_container_width=True)
                    
                    # 카테고리별 요약 테이블
                    st.subheader("카테고리별 지출 요약")
                    
                    # 정확한 필드명 사용
                    amount_col = '매출금액'
                    
                    if amount_col in processed_df.columns and '카테고리' in processed_df.columns:
                        # 카테고리별 합계
                        category_summary = processed_df.groupby('카테고리')[amount_col].sum().reset_index()
                        
                        # 비율 계산
                        total = category_summary[amount_col].sum()
                        category_summary['비율'] = (category_summary[amount_col] / total * 100).round(2)
                        category_summary['비율'] = category_summary['비율'].astype(str) + '%'
                        
                        # 금액 기준 내림차순 정렬
                        category_summary = category_summary.sort_values(by=amount_col, ascending=False)
                        
                        # 천 단위 구분자 추가
                        category_summary[amount_col] = category_summary[amount_col].apply(lambda x: f"{x:,.0f}원")
                        
                        # 열 이름 변경
                        category_summary.columns = ['카테고리', '금액', '비율']
                        
                        # 표 출력
                        st.dataframe(category_summary, use_container_width=True)
                    else:
                        st.info("카테고리 데이터를 찾을 수 없습니다.")

                with viz_tab3:
                    # 가맹점별 차트 - 수정된 함수 호출
                    merchant_chart = create_merchant_chart(processed_df)
                    st.plotly_chart(merchant_chart, use_container_width=True)
                    
                    # 가맹점별 상위 표시 - 정확한 필드명 사용
                    merchant_col = '가맹점명'
                    amount_col = '매출금액'
                    
                    if merchant_col in processed_df.columns and amount_col in processed_df.columns:
                        st.subheader("자주 이용한 가맹점 TOP 10")
                        
                        # 데이터 전처리 - 결측치 및 빈 문자열 제외
                        df_clean = processed_df.copy()
                        df_clean = df_clean[df_clean[merchant_col].notna() & (df_clean[merchant_col] != '')]
                        df_clean = df_clean[df_clean[amount_col].notna()]
                        
                        # 숫자 형식 확인 및 변환
                        if not pd.api.types.is_numeric_dtype(df_clean[amount_col]):
                            try:
                                # 천 단위 구분자(',') 제거 후 숫자로 변환
                                df_clean[amount_col] = df_clean[amount_col].astype(str).str.replace(',', '').str.replace('원', '').astype(float)
                            except:
                                st.error("금액 데이터 변환 중 오류가 발생했습니다.")
                                df_clean = pd.DataFrame()
                        
                        if not df_clean.empty:
                            # 가맹점별 합계
                            merchant_summary = df_clean.groupby(merchant_col)[amount_col].sum().reset_index()
                            
                            # 카테고리 정보 추가
                            if '카테고리' in df_clean.columns:
                                try:
                                    # 가장 많이 나타나는 카테고리 구하기
                                    merchant_category = df_clean.groupby(merchant_col)['카테고리'].agg(
                                        lambda x: x.value_counts().index[0] if len(x) > 0 else '기타'
                                    ).reset_index()
                                    
                                    # 요약 데이터와 병합
                                    merchant_summary = merchant_summary.merge(merchant_category, on=merchant_col, how='left')
                                except:
                                    st.warning("카테고리 정보 처리 중 오류가 발생했습니다.")
                            
                            # 금액 기준 내림차순 정렬 및 상위 10개
                            merchant_summary = merchant_summary.sort_values(by=amount_col, ascending=False).head(10)
                            
                            # 금액 형식 변환
                            merchant_summary[amount_col] = merchant_summary[amount_col].apply(lambda x: f"{x:,.0f}원")
                            
                            # 열 이름 변경
                            if '카테고리' in merchant_summary.columns:
                                merchant_summary.columns = ['가맹점명', '이용금액', '카테고리']
                            else:
                                merchant_summary.columns = ['가맹점명', '이용금액']
                            
                            # 표 출력
                            st.dataframe(merchant_summary, use_container_width=True)
                        else:
                            st.info("처리 가능한 가맹점 데이터가 없습니다.")
                    else:
                        st.info(f"가맹점 또는 금액 데이터를 찾을 수 없습니다. 가능한 컬럼: {', '.join(processed_df.columns)}")

                with viz_tab4:
                    # 일별 사용 추이 차트 - 정확한 필드명 적용
                    date_col = '매출일자'
                    amount_col = '매출금액'
                    
                    if date_col in processed_df.columns and amount_col in processed_df.columns:
                        # 날짜 데이터가 datetime 형식인지 확인
                        df_clean = processed_df.copy()
                        
                        if not pd.api.types.is_datetime64_dtype(df_clean[date_col]):
                            try:
                                # 날짜 변환 시도
                                df_clean[date_col] = pd.to_datetime(df_clean[date_col], errors='coerce')
                            except:
                                st.warning("날짜 데이터 변환에 실패했습니다.")
                        
                        if pd.api.types.is_datetime64_dtype(df_clean[date_col]):
                            # 일별 합계
                            daily_data = df_clean.groupby(date_col)[amount_col].sum().reset_index()
                            
                            # 날짜 정렬
                            daily_data = daily_data.sort_values(by=date_col)
                            
                            # 차트 생성
                            import plotly.express as px
                            
                            daily_chart = px.line(
                                daily_data, 
                                x=date_col, 
                                y=amount_col,
                                title='일별 지출 추이',
                                markers=True
                            )
                            
                            # 차트 스타일 수정
                            daily_chart.update_layout(
                                xaxis_title='날짜',
                                yaxis_title='금액 (원)',
                                yaxis_tickformat=',',
                                plot_bgcolor='rgba(0,0,0,0)',
                                font=dict(family="Malgun Gothic, Arial", size=12),
                                height=500
                            )
                            
                            st.plotly_chart(daily_chart, use_container_width=True)
                        else:
                            st.warning("날짜 데이터가 올바른 형식이 아닙니다.")
                    else:
                        st.info("날짜 또는 금액 데이터를 찾을 수 없습니다.")
                    
                    # 최근 거래 내역 표시
                    st.subheader("최근 거래 내역")
                    
                    date_col = '매출일자'
                    merchant_col = '가맹점명'
                    amount_col = '매출금액'
                    
                    if date_col in processed_df.columns:
                        # 날짜 형변환
                        df_temp = processed_df.copy()
                        if not pd.api.types.is_datetime64_dtype(df_temp[date_col]):
                            try:
                                # 날짜 변환 시도
                                df_temp[date_col] = pd.to_datetime(df_temp[date_col], errors='coerce')
                            except:
                                st.warning("날짜 데이터 변환에 실패했습니다.")
                        
                        if pd.api.types.is_datetime64_dtype(df_temp[date_col]):
                            # 최근 거래 순으로 정렬
                            recent_transactions = df_temp.sort_values(by=date_col, ascending=False).head(10)
                            
                            # 표시할 컬럼 선택
                            display_cols = []
                            
                            if date_col: display_cols.append(date_col)
                            if merchant_col and merchant_col in df_temp.columns: display_cols.append(merchant_col)
                            if '카테고리' in df_temp.columns: display_cols.append('카테고리')
                            if amount_col and amount_col in df_temp.columns: display_cols.append(amount_col)
                            if '부가세' in df_temp.columns: display_cols.append('부가세')
                            if '부가세공제여부' in df_temp.columns: display_cols.append('부가세공제여부')
                            
                            # 남은 컬럼 추가 (제외할 컬럼 지정)
                            exclude_cols = ['거래월']
                            for col in df_temp.columns:
                                if col not in display_cols and col not in exclude_cols:
                                    display_cols.append(col)
                            
                            # 존재하는 컬럼만 필터링
                            display_cols = [col for col in display_cols if col in recent_transactions.columns]
                            
                            # 표 출력
                            st.dataframe(recent_transactions[display_cols], use_container_width=True)
                        else:
                            st.info("날짜 데이터 변환에 실패했습니다.")
                    else:
                        st.info("날짜 데이터를 찾을 수 없습니다.")

                with viz_tab5:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # 부가세 분석 차트
                        try:
                            vat_chart = create_vat_comparison_chart(processed_df)
                            st.plotly_chart(vat_chart, use_container_width=True)
                        except Exception as e:
                            st.error(f"부가세 차트 생성 중 오류: {str(e)}")
                    
                    with col2:
                        # 부가세 공제 가능/불가능 분석
                        if '부가세공제여부' in processed_df.columns:
                            try:
                                tax_deduction_chart = create_tax_deduction_chart(processed_df)
                                st.plotly_chart(tax_deduction_chart, use_container_width=True)
                            except Exception as e:
                                st.error(f"부가세 공제 차트 생성 중 오류: {str(e)}")
                        else:
                            st.info("부가세 공제 여부 데이터가 없습니다.")
                    
                    # 부가세 요약 표시
                    st.subheader("부가세 신고 요약")
                    
                    try:
                        vat_summary = calculate_vat_summary(processed_df)
                        
                        # 천 단위 구분자로 금액 컬럼 형식화
                        for col in vat_summary.columns:
                            if col != '월' and pd.api.types.is_numeric_dtype(vat_summary[col]):
                                vat_summary[col] = vat_summary[col].apply(lambda x: f"{x:,.0f}원")
                        
                        st.dataframe(vat_summary, use_container_width=True)
                    except Exception as e:
                        st.error(f"부가세 요약 계산 중 오류: {str(e)}")
                                    
                # 다운로드 기능
                csv_data, csv_filename = export_to_csv(
                    processed_df, 
                    f"부가세신고용_{datetime.now().strftime('%Y%m%d')}.csv"
                )
                st.download_button(
                    label="CSV 파일로 다운로드",
                    data=csv_data,
                    file_name=csv_filename,
                    mime='text/csv',
                )
            
            except Exception as e:
                st.error(f"파일 로드 중 오류가 발생했습니다: {str(e)}")
        
        st.divider()
        st.subheader("기능 안내")
        st.markdown("""
        **데이터 업로드 기능**
        - 전처리된 엑셀/CSV 파일 업로드
        - 부가세 신고에 필요한 필드 자동 인식
        - 월별 사용 금액 및 부가세 요약
        - 데이터 시각화 및 CSV 다운로드
        """)
    
    # 탭 2: 챗봇 어시스턴트
    with tab2:
        st.header("부가세 신고 어시스턴트")
    
    if not openai_api_key:
        st.warning("OpenAI API 키를 입력하세요. 이는 부가세 관련 질문에 답변하기 위해 필요합니다.")
    else:
        # 도구 목록 생성
       # 도구 목록 생성
        tools = [
            analyze_dataframe,  # DataFrameTool 인스턴스 대신 함수
            get_tax_advice,
            calculate_tax,
            simulate_hometax_report,
            get_tax_saving_tips,
            analyze_chart,
            get_young_entrepreneur_advice,  # 청년 창업자 조언
            get_business_card_strategy,    # 사업자 카드 전략
            get_first_vat_report_guide     # 첫 부가세 신고 가이드 # 새로 추가한 도구
        ]
        # 에이전트 초기화 (한 번만 수행)
        if st.session_state.tax_assistant.agent is None:
            with st.spinner("AI 어시스턴트 초기화 중..."):
                st.session_state.tax_assistant.initialize_agent(openai_api_key, tools)
        
        # 대화 이력 표시
        for message in st.session_state.tax_assistant.chat_history:
            if message.type == "human":
                with st.chat_message("user"):
                    st.write(message.content)
            else:
                with st.chat_message("assistant"):
                    st.write(message.content)
        
        # 빠른 질문 버튼
        st.subheader("빠른 질문")
        quick_cols = st.columns(3)
        
        if quick_cols[0].button("월별 사용 금액 분석"):
            user_input = "월별 사용 금액이 얼마인지 분석해줘"
        elif quick_cols[1].button("부가세 신고 방법"):
            user_input = "부가세 신고는 어떻게 하나요?"
        elif quick_cols[2].button("절세 팁 알려줘"):
            user_input = "개인사업자 절세 팁 알려줘"
        else:
            # 사용자 입력
            user_input = st.chat_input("부가세 신고에 관해 질문하세요...")
        
        if user_input:
            # 사용자 메시지 표시
            with st.chat_message("user"):
                st.write(user_input)
            
            # AI 응답 생성
            with st.chat_message("assistant"):
                st_callback = StreamlitCallbackHandler(st.container())
                
                if st.session_state.processed_df is None and any(term in user_input.lower() for term in ["데이터", "카드", "월별", "합계", "분석"]):
                    response = "아직 데이터가 업로드되지 않았습니다. '데이터 업로드' 탭에서 먼저 분석할 데이터를 업로드해주세요."
                    st.write(response)
                    st.session_state.tax_assistant.add_message(user_input, is_user=True)
                    st.session_state.tax_assistant.add_message(response, is_user=False)
                else:
                    try:
                        with st.spinner("답변 생성 중..."):
                            # 단순화된 응답 생성 - 오류 처리 향상
                            try:
                                response = st.session_state.tax_assistant.get_response(user_input)
                                st.write(response)
                            except ValueError as e:
                                if "One input key expected" in str(e) or "Missing some input keys" in str(e):
                                    # 프롬프트 입력 문제 처리
                                    st.error("입력 키 오류가 발생했습니다. 기본 모드로 응답합니다.")
                                    # 기본 응답 제공
                                    response = "현재 기술적 문제로 인해 정상적인 응답이 어렵습니다. 다시 질문해주시거나 간단한 질문으로 시도해보세요."
                                    st.write(response)
                                else:
                                    st.error(f"오류가 발생했습니다: {str(e)}")
                            
                    except Exception as e:
                        st.error(f"오류가 발생했습니다: {str(e)}")
                        st.error("다시 질문해주시거나 질문을 다른 방식으로 표현해보세요.")
        
        st.divider()
        st.subheader("자주 묻는 질문")
        with st.expander("부가세 신고는 언제 해야 하나요?"):
            st.write("""
            부가세 신고는 일반과세자의 경우 1년에 두 번 신고합니다:
            - 1기(1월~6월): 7월 25일까지
            - 2기(7월~12월): 다음해 1월 25일까지
            
            간이과세자는 다음해 1월 25일까지 1년에 한 번만 신고합니다.
            """)
        
        with st.expander("어떤 증빙서류가 필요한가요?"):
            st.write("""
            부가세 신고에 필요한 주요 증빙서류:
            1. 세금계산서 (매출/매입)
            2. 계산서 (면세 거래)
            3. 신용카드 매출전표
            4. 현금영수증
            5. 간이영수증 (3만원 이하)
            
            이러한 증빙서류는 5년간 보관해야 합니다.
            """)
        
        with st.expander("매입세액공제란 무엇인가요?"):
            st.write("""
            매입세액공제는 사업자가 물품이나 서비스를 구매할 때 부담한 부가가치세를 납부해야 할 부가가치세에서 공제받는 제도입니다.
            
            공제 가능한 주요 항목:
            - 재화 또는 용역의 구입에 지불한 부가세
            - 업무용 자산의 구입에 지불한 부가세
            - 사업과 관련된 비용에 포함된 부가세
            
            공제받기 위해서는 적격 증빙서류(세금계산서, 신용카드 매출전표 등)가 필요합니다.
            """)
            
    # 탭 3: 세금 계산기
    with tab3:
        st.header("세금 계산기")
        
        calc_col1, calc_col2 = st.columns(2)
        
        with calc_col1:
            st.subheader("부가세 계산")
            
            # 계산 유형 선택
            calc_type = st.radio(
                "계산 유형 선택",
                ["세전 금액에서 부가세 계산", "세후 금액에서 역산 계산"],
                horizontal=True
            )
            
            # 금액 입력
            if calc_type == "세전 금액에서 부가세 계산":
                input_label = "세전 금액(공급가액)"
                example_text = "예: 1,000,000원의 부가세는 100,000원이고, 합계금액은 1,100,000원입니다."
            else:
                input_label = "세후 금액(공급대가)"
                example_text = "예: 1,100,000원에는 부가세 100,000원이 포함되어 있고, 공급가액은 1,000,000원입니다."
            
            amount = st.number_input(input_label, min_value=0, step=10000, format="%d")
            
            if st.button("계산하기"):
                if calc_type == "세전 금액에서 부가세 계산":
                    vat = amount * 0.1
                    total = amount + vat
                    
                    st.success(f"""
                    ### 계산 결과
                    - 공급가액: {amount:,.0f}원
                    - 부가세액: {vat:,.0f}원
                    - 합계금액: {total:,.0f}원
                    """)
                else:
                    supply_value = amount / 1.1
                    vat = amount - supply_value
                    
                    st.success(f"""
                    ### 계산 결과
                    - 공급가액: {supply_value:,.0f}원
                    - 부가세액: {vat:,.0f}원
                    - 합계금액: {amount:,.0f}원
                    """)
            
            st.caption(example_text)
        
        with calc_col2:
            st.subheader("세금계산서 작성 도우미")
            
            # 세금계산서 기본 정보
            st.markdown("#### 공급자 정보")
            supplier_name = st.text_input("공급자 상호", placeholder="예: 홍길동 사업소")
            supplier_id = st.text_input("공급자 사업자등록번호", placeholder="예: 123-45-67890")
            
            st.markdown("#### 공급받는 자 정보")
            receiver_name = st.text_input("공급받는 자 상호", placeholder="예: 개인사업자 주식회사")
            receiver_id = st.text_input("공급받는 자 사업자등록번호", placeholder="예: 987-65-43210")
            
            st.markdown("#### 거래 정보")
            transaction_date = st.date_input("거래일자", datetime.now())
            item_name = st.text_input("품목", placeholder="예: 컨설팅 서비스")
            item_amount = st.number_input("공급가액", min_value=0, step=10000, format="%d")
            
            if st.button("세금계산서 미리보기"):
                vat = item_amount * 0.1
                total = item_amount + vat
                
                st.success(f"""
                ### 세금계산서 미리보기
                
                **공급자**
                - 등록번호: {supplier_id}
                - 상호: {supplier_name}
                
                **공급받는 자**
                - 등록번호: {receiver_id}
                - 상호: {receiver_name}
                
                **거래 내용**
                - 작성일자: {transaction_date.strftime('%Y-%m-%d')}
                - 품목: {item_name}
                - 공급가액: {item_amount:,.0f}원
                - 부가세액: {vat:,.0f}원
                - 합계금액: {total:,.0f}원
                """)
        
        st.divider()
        
        # 비율 계산기
        st.subheader("부가세율 및 세전/세후 비율 안내")
        
        st.info("""
        **부가세 비율 정리**
        - 부가세율: 10%
        - 세전 금액에 대한 부가세: 금액 × 0.1
        - 세후 금액에 포함된 부가세: 금액 × (1/11) ≈ 금액 ÷ 11
        - 세후 금액에서 세전 금액으로: 금액 ÷ 1.1
        - 세전 금액에서 세후 금액으로: 금액 × 1.1
        """)
        
        st.warning("""
        **주의사항**
        - 이 계산 결과는 참고용이며, 정확한 세금 계산은 세무사와 상담하세요.
        - 부가세 면세 품목이나 영세율 적용 품목은 별도로 확인이 필요합니다.
        - 세금계산서 발행 시 부가세율은 법령에 따라 적용됩니다.
        """)


# Streamlit 앱 실행
if __name__ == "__main__":
    main()