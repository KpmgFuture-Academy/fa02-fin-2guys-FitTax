import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import requests
import os

# ✅ 페이지 설정
st.set_page_config(page_title="연금 KPI 대시보드", layout="wide")

# ✅ 배경색 변경을 위한 CSS 삽입
st.markdown(
    """
    <style>
        body {
            background-color: #F4F6F9; /* 연한 회색 */
        } 

        .stApp {
            background-color: #F4F6F9;
        }
    </style>
    """,  
    unsafe_allow_html=True  
)
  
# ✅ DB 설정
DB_URL = "https://raw.githubusercontent.com/nnnhh03/Fin_Feed/main/data/연금.db"
DB_PATH = "연금.db"

@st.cache_data
def download_db_file(): 
    if not os.path.exists(DB_PATH):
        try:
            r = requests.get(DB_URL)
            with open(DB_PATH, "wb") as f:
                f.write(r.content)
            return True
        except Exception as e:
            st.error(f"DB 다운로드 실패: {e}")
            return False
    return True

@st.cache_data
def load_table_summary(modifier=""):
    conn = sqlite3.connect(DB_PATH)
    table_names = ["IRP", "ISA", "연금저축생명보험", "연금저축손해보험", "연금저축신탁", "연금저축펀드"]
    summary = []
    total_products = 0
    total_deposit = 0
    total_balance = 0

    for table in table_names:
        try: 
            df = pd.read_sql(f"SELECT * FROM '{table}'", conn)
            if table == "IRP":
                product_count = len(df) // 5
            else:
                product_count = len(df)

            deposit_col = next((c for c in df.columns if '납입원금' in c), None)
            balance_col = next((c for c in df.columns if '적립금' in c), None)

            deposit_sum = pd.to_numeric(df[deposit_col].astype(str).str.replace(',', ''), errors='coerce').sum() if deposit_col else 0
            balance_sum = pd.to_numeric(df[balance_col].astype(str).str.replace(',', ''), errors='coerce').sum() if balance_col else 0

            total_products += product_count
            total_deposit += deposit_sum
            total_balance += balance_sum

            summary.append({
                "테이블명": table,
                "상품 수": product_count,
                "납입원금 합계": deposit_sum,
                "적립금 합계": balance_sum
            })

        except Exception as e:
            st.warning(f"⚠️ 테이블 '{table}' 처리 중 오류: {e}")

    conn.close()
    return pd.DataFrame(summary), total_products, total_deposit, total_balance

# 캐시 키 변경을 위해, load_table_summary 함수 호출 시 modifier 값으로 현재 시간이나 고유값 전달:
import time
summary_df, total_products, total_deposit, total_balance = load_table_summary(modifier=time.time())

# ✅ 실행
### <1번> KPI
if download_db_file():
    st.title("📊 연금 상품 대시보드")

    # summary_df = load_table_summary()
    summary_df, total_products, total_deposit, total_balance = load_table_summary()

    total_products = summary_df["상품 수"].sum()
    total_deposit = summary_df["납입원금 합계"].sum()
    total_balance = summary_df["적립금 합계"].sum()

    # ✅ 상단 KPI 카드 (컨테이너 박스 스타일)
    with st.container():
        k1, k2, k3 = st.columns(3)

        with k1:
            st.markdown(f"<h1 style='text-align:center; color:#111;'>{total_products:,}</h1>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align:center; font-size:18px; font-weight:bold;'>📦 상품 수</p>", unsafe_allow_html=True)

        with k2:
            st.markdown(f"<h1 style='text-align:center; color:#111;'>{int(total_deposit):,} <span style='font-size:16px;'>(단위 : 백만원)</span></h1>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align:center; font-size:18px; font-weight:bold;'>💰 납입원금 합계</p>", unsafe_allow_html=True)

        with k3:
            st.markdown(f"<h1 style='text-align:center; color:#111;'>{int(total_balance):,} <span style='font-size:16px;'>(단위 : 백만원)</span></h1>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align:center; font-size:18px; font-weight:bold;'>🏦 적립금 합계</p>", unsafe_allow_html=True)
    # ✅ KPI 아래: 파이차트(좌) + Raw 데이터 보기(우)
    st.divider()

    with st.container(): 
        col1, col2, col3 = st.columns([1, 1, 2]) 

        with col1:
            st.markdown("<h3 style='text-align: center;'>💡 납입원금 합계 비중 </h3>", unsafe_allow_html=True)

            fig1 = px.pie(
                summary_df,
                names="테이블명",
                values="납입원금 합계",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Bold,
            )
            fig1.update_traces(
                textinfo="label+percent",
                hovertemplate="<b>%{label}</b><br>납입원금: %{value:,} 원<extra></extra>", 
                textfont=dict(size=16, color='black')
            )
            st.plotly_chart(fig1, use_container_width=True)
            
        with col2:
            # st.markdown("<h4 style='text-align: center;'>적립금 합계 비중</h4>", unsafe_allow_html=True)
            st.markdown("<h3 style='text-align: center;'>💡 적립금 합계 비중 </h3>", unsafe_allow_html=True)
            fig_balance = px.pie(
                summary_df,
                names="테이블명",
                values="적립금 합계",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Dark24
            )
            fig_balance.update_traces(
                textinfo="label+percent",
                hovertemplate="<b>%{label}</b><br>적립금: %{value:,} 원<extra></extra>",
                marker=dict(line=dict(color='black', width=2)),
                textfont=dict(size=16, color='black')
            ) 
            st.plotly_chart(fig_balance, use_container_width=True, key="balance_chart")

        with col3:
            col_title, col_select = st.columns([1, 2])  # 비율 조정 가능

            with col_title:
                st.markdown("### 📋 상품 정보 보기")

            with col_select:
                table_options = ["IRP", "ISA", "연금저축생명보험", "연금저축손해보험", "연금저축신탁", "연금저축펀드"]
                selected_table = st.selectbox("📊 상품 선택 ", table_options, key = "테이블 선택")

            # st.markdown("<h3 style='text-align: center;'>📋 상품 정보 보기</h3>", unsafe_allow_html=True)

            # table_options = ["IRP", "ISA", "연금저축생명보험", "연금저축손해보험", "연금저축신탁", "연금저축펀드"]
            # selected_table = st.selectbox("🔽 테이블 선택", table_options)

            def clean_numeric_columns(df, columns):
                for col in columns:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", ""), errors="coerce")
                return df

            try:
                conn = sqlite3.connect(DB_PATH)
                df_raw = pd.read_sql(f"SELECT * FROM '{selected_table}'", conn)
                df_raw = clean_numeric_columns(df_raw, ['납입원금', '적립금', '납입원금(24년)', '적립금(24년)', '납입원금(24-4)', '적립금(24-4)'])
                conn.close()

                st.dataframe(df_raw, use_container_width=True, height=400)
                
                # 👇 여기 아래에 챗봇 추가 (챗봇)
                # ✅ 챗봇 인터페이스
                st.markdown("### 🤖 연금 상품 챗봇에게 물어보세요!") 

                # OpenAI API 키를 사이드바에서 입력받습니다.
                openai_api_key = "" # 별도의 api key

                # 사용자 자연어 질문 입력 (기존의 'query' 변수와 중복되지 않게 별도로 관리)
                chatbot_query = st.text_input("질문을 입력하세요.", 
                                              placeholder="예: 수익률dl 가장 높은 상품은 무엇인가요?", 
                                              key="chatbot_query")

                # 챗봇 처리: API 키와 질문이 모두 입력되었을 때 실행 
                if openai_api_key and chatbot_query:
                    try:
                        with st.spinner('데이터베이스 준비 중...'):
                            from langchain_openai import ChatOpenAI
                            from langchain_community.utilities import SQLDatabase
                            from langchain_experimental.sql import SQLDatabaseChain

                            # 선택된 테이블 기반 쿼리 처리 
                            db_uri = f"sqlite:///{DB_PATH}"
                            db = SQLDatabase.from_uri(db_uri)

                            # OpenAI 모델 설정
                            llm = ChatOpenAI(api_key=openai_api_key, model="gpt-3.5-turbo", temperature=0)

                            # LangChain SQL 체인 생성
                            db_chain = SQLDatabaseChain.from_llm(llm, db, verbose=False)

                            # 프롬프트 구성: 선택된 테이블과 해당 테이블의 수치 컬럼 전처리 사항 포함
                            query_prompt = f"""
                            현재 선택된 테이블은 '{selected_table}'입니다.
                            

                            위 사항을 참고하여 아래 자연어 질문에 대해 SQL을 작성하고 실행한 후, 요약 결과를 제시해주세요.

                            질문: {chatbot_query}
                            """ # 이 테이블의 수치 컬럼은 문자열(예: '1,000')로 저장되어 있으며, 계산 시 다음과 같이 처리해야 합니다:

                            # NCAST(REPLACE(컬럼명, ',', '') AS REAL)

                        with st.spinner('질문을 분석하고 응답을 생성 중입니다...'):
                            result = db_chain.run(query_prompt)  

                        # 결과 출력
                        st.subheader("📌 결과")
                        st.write(result)

                    except Exception as e:
                        st.error(f"❌ 챗봇 처리 중 오류가 발생했습니다: {e}")

            except Exception as e: 
                st.warning(f"⚠️ '{selected_table}' 테이블 로딩 오류: {e}")

    st.divider()
    
    import plotly.graph_objects as go

    # ✅ TOP & BOTTOM 복합 시각화 
    # ✅ 전체 테이블 통합 (IRP 테이블은 그룹화 처리)
    conn = sqlite3.connect(DB_PATH)
    table_names = ["연금저축생명보험", "연금저축손해보험", "연금저축신탁", "연금저축펀드"]
    combined_df = pd.DataFrame()

    for table in table_names:
        try:
            df = pd.read_sql(f"SELECT * FROM '{table}'", conn)
            df["테이블명"] = table
 
            # ✅ 수치 컬럼 이름 고정
            if table == "IRP":
                deposit_col = "납입원금(24-4)"
                balance_col = "적립금(24-4)"
            else:
                deposit_col = "납입원금(24년)"
                balance_col = "적립금(24년)"
            df[deposit_col] = pd.to_numeric(df[deposit_col].astype(str).str.replace(",", ""), errors="coerce")
            df[balance_col] = pd.to_numeric(df[balance_col].astype(str).str.replace(",", ""), errors="coerce")
            df['테이블'] = table

            if table == "IRP":
                # IRP는 사업자명 + 형태명 기준으로 그룹화
                df = df.groupby(["사업자명", "형태명"], as_index=False)[[deposit_col, balance_col]].sum()
                df["상품명"] = df["사업자명"] + " - " + df["형태명"]
            else:
                df["상품명"] = df["상품명"].fillna("이름없음") 

            combined_df = pd.concat([combined_df, df], ignore_index=True)

        except Exception as e:
            st.warning(f"⚠️ '{table}' 테이블 로딩 오류: {e}") 
    conn.close() 

    # ✅ 기준 설정
    # ✅ 기준 및 테이블 선택 추가
    col_metric, blank1, col_table, blank2 = st.columns([1,1,1,1])
    with col_metric:
        metric_option = st.selectbox("📌 기준 선택", ["납입원금", "적립금"], key="기준선택")
    with col_table:
        selected_table_option = st.selectbox("📊 테이블 선택", ["전체"] + table_names, key="테이블선택")

    target_col = "납입원금(24년)" if metric_option == "납입원금" else "적립금(24년)"
    line_col = "적립금(24년)" if target_col == "납입원금(24년)" else "납입원금(24년)"

    # ✅ 선택한 테이블 기준 필터링
    if selected_table_option != "전체":
        filtered_df = combined_df[combined_df["테이블"] == selected_table_option].copy()
    else:
        filtered_df = combined_df.copy()

    # 상하위 10 추출
    top10 = filtered_df.sort_values(by=target_col, ascending=False).head(10)
    bottom10 = filtered_df.sort_values(by=target_col, ascending=True).head(10)

    # 📈 복합 그래프 함수 정의
    def plot_combo(df, title, color):
        # 정렬된 순서를 유지하려면 상품명을 Categorical로 설정
        df["상품명"] = pd.Categorical(df["상품명"], categories=df["상품명"], ordered=True)

        fig = go.Figure()
 
        fig.add_trace(go.Bar(
            x=df["상품명"],
            y=df[target_col],
            name=target_col,
            marker_color=color, 
            text=df[target_col],
            textposition='auto'
        ))

        fig.add_trace(go.Scatter( 
            x=df["상품명"],
            y=df[line_col], 
            name=line_col,
            mode='lines+markers', 
            marker=dict(color='black', size=8),
            line=dict(width=2),
            yaxis='y2'
        ))

        fig.update_layout(
            title=title,
            xaxis=dict(title="상품명"), 
            yaxis=dict(title=target_col),
            yaxis2=dict(title=line_col, overlaying='y', side='right'),
            legend=dict(x=0.01, y=1.15, orientation="h"),
            height=500,
            margin=dict(t=80, b=40)
        )
        return fig
    
    # ✅ 좌우 배치
    col1, col2, col3 = st.columns([1, 1, 1])
 
    with col1:
        st.markdown(f"#### 🟦 {metric_option} 기준 상위 10개 상품")
        st.plotly_chart(plot_combo(top10, f"상위 10 상품 ({metric_option})", '#4169E1'), use_container_width=True)

    with col2:
        st.markdown(f"#### 🟥 {metric_option} 기준 하위 10개 상품")
        st.plotly_chart(plot_combo(bottom10, f"하위 10 상품 ({metric_option})",'lightsalmon'), use_container_width=True)

    with col3:
        st.markdown("#### 📈 수익률 기준 TOP 10 상품")

        # 수치화
        filtered_df["납입원금(24-4)"] = pd.to_numeric(filtered_df["납입원금(24-4)"].astype(str).str.replace(",", ""), errors="coerce")
        filtered_df["적립금(24-4)"] = pd.to_numeric(filtered_df["적립금(24-4)"].astype(str).str.replace(",", ""), errors="coerce")

        # ✅ 수익률 계산: (적립금 - 납입원금) / 납입원금
        filtered_df["수익률"] = ((filtered_df["적립금(24-4)"] - filtered_df["납입원금(24-4)"]) / filtered_df["납입원금(24-4)"]).round(4)

        roi_top10 = filtered_df.sort_values(by="수익률", ascending=False).head(10)
        roi_top10["상품명"] = pd.Categorical(roi_top10["상품명"], categories=roi_top10["상품명"], ordered=True)

        fig_roi = go.Figure()
        fig_roi.add_trace(go.Bar(
            x=roi_top10["상품명"],
            y=roi_top10["수익률"] * 100,
            marker_color='mediumseagreen',
            text=(roi_top10["수익률"] * 100).round(2),
            textposition='auto',
            name='수익률 (%)'
        ))

        fig_roi.update_layout(
            xaxis_title="상품명",
            yaxis_title="수익률 (%)",
            height=500,
            margin=dict(t=50, b=40),
            showlegend=False
        )

        st.plotly_chart(fig_roi, use_container_width=True)
        
    # ... (이전 코드 계속)

    ### <4번>
    # 좌우 배치하여 3개 그래프 출력 완료 후, 해석 리포트 영역 추가
    # st.divider()
    # st.markdown("## GPT 기반 해석 리포트")
    st.info("각 그래프에 대한 해석 리포트를 OpenAI API를 통해 생성합니다. 잠시 기다려주세요!")

    # ✅ GPT 해석 리포트 생성 함수 (예시)
    def generate_report(prompt, llm):
        """
        LangChain의 llm 객체를 이용하여 주어진 프롬프트에 대한 해석 리포트를 생성합니다.
        """
        return llm.predict(prompt)

    # OpenAI API 키가 존재하면 리포트 생성 진행 (앞서 입력된 openai_api_key 사용)
    try:
        # LangChain GPT 모델 (모델명 및 온도 조절은 필요에 따라 조정)
        # 버전에 따라 아래 import 구문은 달라질 수 있음:
        # from langchain_openai import ChatOpenAI
        from langchain.chat_models import ChatOpenAI
        llm_report = ChatOpenAI(api_key=openai_api_key, model="gpt-4o", temperature=0.7)
    except Exception as e:
        st.error(f"LLM 초기화 실패: {e}")
        llm_report = None

    if llm_report:
        st.markdown(
    """
    <style>
    .border-box {
        border: 2px solid #ddd;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
        background-color: #ffffff;
    }
    </style>
    """, unsafe_allow_html=True
) 
        col1, col2, col3 = st.columns([1,1,1])
        # 1. 상위 10 상품 해석 리포트 생성
        with col1:
            try:
                with st.spinner("상위 10 상품 그래프 해석 리포트 생성 중..."): 
                    prompt_top = f"""
        다음은 {metric_option} 기준 상위 10 상품의 데이터 요약입니다.
        데이터:
        {top10[['상품명', target_col, line_col]].to_csv(index=False)}

        이 데이터를 기반으로 상깊이 있는 간단 해석 리포트를 작성해 주세요. 각 상품에 대한 구체적인 리포트 말고, 대략적인 인사이트를 뽑아주세요.
        - 납입원금과 적립금을 중점으로 분석해 주세요. 예를 들어, 납입원금 대비 적립금이 유도 크거나 작은 상품이 있다면 이에 대해 중점적으로 분석해주세요.
                    """
                    report_top = generate_report(prompt_top, llm_report)
                    # st.markdown("### 🟦 상위 10 상품 해석 리포트")
                    st.write(report_top)
            except Exception as e: 
                st.error(f"상위 10 상품 해석 리포트 생성 중 오류: {e}") 
        with col2:
            # 2. 하위 10 상품 해석 리포트 생성
            try:
                with st.spinner("하위 10 상품 그래프 해석 리포트 생성 중..."):
                    prompt_bottom = f"""
        다음은 {metric_option} 기준 하위 10 상품의 데이터 요약입니다. 
        데이터:
        {bottom10[['상품명', target_col, line_col]].to_csv(index=False)}

        이 데이터를 기반으로 하위 10 상품에 대한 간단 해석 리포트를 작성해 주세요. 각 상품에 대한 구체적인 리포트 말고, 대략적인 인사이트를 뽑아주세요.
        - 납입원금과 적립금을 중점으로 분석해 주세요. 예를 들어, 납입원금 대비 적립금이 유도 크거나 작은 상품이 있다면 이에 대해 중점적으로 분석해주세요.
                    """
                    report_bottom = generate_report(prompt_bottom, llm_report)
                    st.markdown("### 🟥 하위 10 상품 해석 리포트")
                    st.write(report_bottom)
            except Exception as e:
                st.error(f"하위 10 상품 해석 리포트 생성 중 오류: {e}")
        with col3:
            # 3. 수익률 TOP 10 상품 해석 리포트 생성
            try:
                with st.spinner("수익률 TOP 10 상품 그래프 해석 리포트 생성 중..."):
                    prompt_roi = f"""
        다음은 수익률 TOP 10 상품 데이터 요약입니다.
        데이터:
        {roi_top10[['상품명', '수익률']].to_csv(index=False)}

        이 데이터를 기반으로 수익률에 따른 해석 및 심층 분석 리포트를 작성해 주세요.
        - 어떤 요인들이 높은 수익률에 영향을 미쳤는지, 
        - 또 어떤 회사의 상품들이 특히 수익률이 좋은지에 대해 분석해 주세요.
                    """
                    report_roi = generate_report(prompt_roi, llm_report)
                    st.markdown("### 📈 수익률 TOP 10 상품 해석 리포트")
                    st.write(report_roi)
            except Exception as e:
                st.error(f"수익률 TOP 10 상품 해석 리포트 생성 중 오류: {e}") 

else:
    st.error("❌ 연금.db 파일을 다운로드할 수 없습니다.")
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
  
 
 
 