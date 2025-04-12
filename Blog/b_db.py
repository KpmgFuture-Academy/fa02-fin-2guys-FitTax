import streamlit as st
import streamlit.components.v1 as components # HTML 컴포넌트 사용을 위해 필요
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import sqlite3
import requests
import os

# --- Database Configuration ---
DB_URL = "https://raw.githubusercontent.com/nnnhh03/Fin_Feed/main/data/Fin_Feed.db" 

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILENAME = os.path.join(BASE_DIR, "Fin_Feed.db")

# DB_FILENAME = "Fin_Feed.db"
# !!! IMPORTANT: Adjust TABLE_NAME if your table name in the DB is different !!!
# === YOU MUST SET THE CORRECT TABLE NAME HERE ===
TABLE_NAME = "Feed" # <<<=== EXAMPLE NAME, CHANGE TO YOUR ACTUAL TABLE NAME
# =================================================

# === Field Names (Adjust if needed) ===
COL_NAME = "category"
COL_INTRO = "definition" 
COL_INGREDIENTS = "description" 
COL_STEPS = "example" 
COL_TIPS = "comparing" 
COL_FINISH = "마무리문장" 
# =====================================
# -----------------------------

# --- OpenAI Configuration ---
# 🔑 (보안 주의) OpenAI API 키 입력. 환경 변수나 Streamlit secrets 사용 권장.
OPENAI_API_KEY = "" # -- API 키
# --- Initialize OpenAI LLM ---
llm = None
chain = None
try:
    llm = ChatOpenAI(
        openai_api_key=OPENAI_API_KEY,
        temperature=0.7,
        model="gpt-3.5-turbo"
    )
except Exception as e:
    st.error(f"OpenAI API 키 또는 모델 초기화 중 오류 발생: {e}", icon="🚨")

# --- Langchain Setup ---
if llm:
    template = """
당신은 10년 차 금융 전문 피드 작성자입니다. 아래 주어진 요리를 네이버 블로그 피드에 적합한 형식으로 풍성하게 소개해 주세요.
사람들의 체류시간을 늘릴 수 있도록 내용을 풍성하게 몰입감 있게 작성해주세요. 

질문 내용: {dish}

금융 피드는 다음과 같은 형식을 따릅니다:

1. 상품 정의(질문에 대한 상세하고 깔끔한 정의 소개)
2. 상품의 종류
3. 상품 종류 상세 설명
4. 상품 종류의 장단점 비교(구체적 사례 들어 비교 설명하기)

네이버 블로그에 복사하여 붙여넣을 수 있는 HTML 형식으로 작성해주세요. 다음 사항을 지켜주세요:

1. 제목은 <h2> 태그를 사용하고 앞에 "🍳 "와 같은 이모지를 넣어주세요
2. 각 섹션의 소제목은 <h3> 태그를 사용하고 앞에 적절한 이모지를 넣어주세요
3. 상품 목록은 <ul><li> 태그를 사용하여 목록으로 표시해주세요
4. 상품 종류는 <ol><li> 태그를 사용하여 번호가 있는 목록으로 표시해주세요
5. 중요 팁이나 강조할 내용은 ✅ 또는 💡 이모지로 시작하는 문단으로 작성해주세요
6. 각 섹션 사이에는 <hr> 태그로 구분선을 추가해주세요
7. 강조할 부분은 <b> 태그, 기울임은 <i> 태그를 사용해주세요
8. 색상이 있는 텍스트는 <span style="color:#색상코드;"> 태그를 사용해주세요 (예: <span style="color:#FF6B6B;">중요한 내용</span>)

위의 형식을 정확히 사용하여 네이버 블로그에 복사하여 바로 붙여넣을 수 있는 HTML 형태로 작성해 주세요.
"""
    prompt = PromptTemplate(input_variables=["dish"], template=template)
    try:
        chain = LLMChain(llm=llm, prompt=prompt)
    except Exception as e:
        st.error(f"LangChain 초기화 중 오류 발생: {e}", icon="⛓️")
else:
    # llm 초기화 실패 시 chain도 None 상태 유지
    st.warning("OpenAI LLM 초기화 실패로 인해 AI 응답 생성이 비활성화되었습니다.", icon="⚠️")

# --- Database Functions ---
def download_db(url, filename):
    if not os.path.exists(filename):
        st.info(f"'{filename}' 다운로드 중...", icon="⏳")
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            st.success(f"'{filename}' 다운로드 완료.", icon="✅")
            return True
        except requests.exceptions.RequestException as e:
            st.error(f"DB 다운로드 실패: {e}", icon="❌")
            return False
    # 이미 파일이 존재하면 True 반환
    return True


def search_recipe_in_db(dish_name):
    if not os.path.exists(DB_FILENAME):
        st.warning(f"DB 파일 '{DB_FILENAME}' 없음. 다운로드를 시도합니다.", icon="⚠️")
        if not download_db(DB_URL, DB_FILENAME):
            return None

    conn = None
    try:
        conn = sqlite3.connect(DB_FILENAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        query = f"""
            SELECT "{COL_NAME}", "{COL_INTRO}", "{COL_INGREDIENTS}", "{COL_STEPS}", "{COL_TIPS}", "{COL_FINISH}"
            FROM "{TABLE_NAME}"
            WHERE "{COL_NAME}" LIKE ?
        """
        cursor.execute(query, (f'%{dish_name}%',))
        results = cursor.fetchall()
        return results
    except sqlite3.Error as e:
        if "no such table" in str(e):
             st.error(f"DB 오류: 테이블 '{TABLE_NAME}' 없음. 코드 상단 TABLE_NAME 확인 필요.", icon="🚨")
        else:
            st.error(f"DB 검색 오류: {e}", icon="🚨")
        return None
    finally:
        if conn:
            conn.close()

def format_db_recipe_to_blog(recipe_data):
    if not recipe_data: return "레시피 데이터 오류"
    name = recipe_data[COL_NAME] or "?"
    intro = recipe_data[COL_INTRO] or "소개 없음"
    ingredients = recipe_data[COL_INGREDIENTS] or "재료 정보 없음"
    steps = recipe_data[COL_STEPS] or "조리법 정보 없음"
    tips = recipe_data[COL_TIPS] or "팁 정보 없음"
    # finish = recipe_data[COL_FINISH] or f"오늘은 맛있는 <b>{name}</b> 레시피를 소개해드렸어요! 따뜻하고 즐거운 식사 시간 되시길 바랍니다. 😊"

    # HTML 형식으로 재료 목록 변환
    ingredients_list = ingredients.replace(',', '\n').split('\n')
    formatted_ingredients = "<ul>\n" + "\n".join([f"<li>{item.strip()}</li>" for item in ingredients_list if item.strip()]) + "\n</ul>"
    if len(ingredients_list) <= 1 and not ingredients_list[0].strip(): 
        formatted_ingredients = "<ul><li>상품 설명 정보 없음</li></ul>"

    # HTML 형식으로 조리법 단계 변환
    steps_list = steps.split('\n')
    formatted_steps = "<ol>\n" + "\n".join([f"<li>{step.strip()}</li>" for step in steps_list if step.strip()]) + "\n</ol>"
    if len(steps_list) <= 1 and not steps_list[0].strip():
        formatted_steps = "<ol><li>상품 예시 정보 없음</li></ol>"

    # HTML 블로그 포스트 생성
    blog_post = f"""<h2 style="font-size:24px;color:#333;">🍳 {name}</h2>

<h3 style="font-size:20px;color:#4A4A4A;">📝 <span style="color:#0066CC;">용어 설명</span></h3>
<p>{intro}</p>

<hr style="border:1px solid #EEEEEE;margin:20px 0;" />

<h3 style="font-size:20px;color:#4A4A4A;">📜 <span style="color:#0066CC;">종류</span></h3>
{formatted_ingredients}

<hr style="border:1px solid #EEEEEE;margin:20px 0;" />

<h3 style="font-size:20px;color:#4A4A4A;">🔪 <span style="color:#0066CC;">상세 설명</span></h3>
{formatted_steps}

<hr style="border:1px solid #EEEEEE;margin:20px 0;" />

<h3 style="font-size:20px;color:#4A4A4A;">💡 <span style="color:#0066CC;">비교 설명</span></h3>
<p>{tips}</p>

<hr style="border:1px solid #EEEEEE;margin:20px 0;" />

""" # <p>{finish}</p> # <h3 style="font-size:20px;color:#4A4A4A;">💖 <span style="color:#0066CC;">마무리</span></h3>
    return blog_post.strip()

# --- Streamlit App UI ---

# Use wide layout to accommodate sidebar and columns
st.set_page_config(layout="wide")

st.title("🍳 금융 피드 자동 생성기")
st.markdown("DB에서 정보를 찾거나, 없으면 AI가 생성하여 네이버 블로그 형식으로 만들어 드립니다.")

# Initialize session state
default_session_state = {
    'selected_recipe_data': None, 
    'search_results': None,
    'show_selection': False,
    'generated_content': None, 
    'last_searched_dish': ""
}
for key, default_value in default_session_state.items():
    if key not in st.session_state:
        st.session_state[key] = default_value

# Download DB on first run if needed
db_available = download_db(DB_URL, DB_FILENAME)

# Define columns with adjusted width
col1, col2 = st.columns([2, 3]) # Left column takes 2/5, Right column takes 3/5 width

# --- Left Column (Input & Controls) ---
with col1:
    st.subheader("1. 질문하세요")
    dish = st.text_input(f"질문을 입력하세요. DB 검색 필드: '{COL_NAME}'", key="dish_input")

    if st.button("✅ 피드 생성하기", key="generate_button", use_container_width=True):
        # Reset state
        st.session_state.selected_recipe_data = None
        st.session_state.search_results = None
        st.session_state.show_selection = False
        st.session_state.generated_content = None
        st.session_state.last_searched_dish = dish

        if dish:
            results = None
            if db_available:
                 with st.spinner(f"'{dish}' DB 검색 중..."):
                    results = search_recipe_in_db(dish)
            else:
                 st.warning("DB 사용 불가. AI 생성을 시도합니다.", icon="⚠️") # DB 없어도 AI 시도 가능하도록

            if results is not None and len(results) > 0 : # Found in DB
                if len(results) == 1:
                    selected_name = results[0][COL_NAME] or "이름 없는 레시피"
                    st.success(f"✅ DB에서 '{selected_name}' 찾음!", icon="👍")
                    st.session_state.selected_recipe_data = results[0]
                    st.session_state.generated_content = format_db_recipe_to_blog(st.session_state.selected_recipe_data)
                    st.session_state.show_selection = False
                else:
                    st.info(f"'{dish}' 관련 레시피 {len(results)}개 발견. 아래에서 하나를 선택하세요:", icon="👇")
                    st.session_state.search_results = results
                    st.session_state.show_selection = True
                    st.session_state.generated_content = None

            else: # Not found in DB or DB error/unavailable
                 if results is None and db_available: # DB search error case
                      st.warning("DB 검색 오류 발생. AI 생성을 시도합니다.", icon="⚠️")
                 elif results is None and not db_available: # DB unavailable case (handled above already)
                      pass # Warning already shown
                 else: # results == 0 (not found)
                      st.info("DB에 없음. AI 생성을 시도합니다.", icon="🤖")

                 if chain: # Try GPT if chain is initialized
                    try:
                        with st.spinner("AI 피드 생성 중..."):
                            gpt_result = chain.run(dish=dish)
                            st.session_state.generated_content = gpt_result
                            st.success("AI 피드 생성 완료!", icon="✨")
                            st.session_state.show_selection = False
                    except Exception as e:
                        st.error(f"AI 생성 오류: {e}", icon="🚨")
                        st.session_state.generated_content = None
                 else:
                    # Handle case where DB search failed/skipped AND GPT is unavailable
                    st.error("DB 및 AI 설명을 가져올 수 없습니다.", icon="❌")
                    st.session_state.generated_content = None
                    st.session_state.show_selection = False

        else: # No dish name entered
            st.warning("질문을 입력해주세요.", icon="👆")

    # Divider between input and selection list
    st.divider()

    # --- Display Selection Radio Buttons if multiple results ---
    if st.session_state.show_selection and st.session_state.search_results:
        st.subheader("2. 질문 상품 선택")
        recipe_names = [result[COL_NAME] for result in st.session_state.search_results]
        selected_index = st.radio(
            "선택할 상품군:",
            options=range(len(recipe_names)),
            format_func=lambda index: recipe_names[index] or f"이름 없는 레시피 {index+1}",
            key='recipe_selection',
            # horizontal=True, # Consider removing horizontal for narrower col1
        )

        if st.button("선택 완료", key="confirm_selection", use_container_width=True):
            if selected_index is not None:
                st.session_state.selected_recipe_data = st.session_state.search_results[selected_index]
                selected_name = st.session_state.selected_recipe_data[COL_NAME] or f"이름 없는 정보 {selected_index+1}"
                st.session_state.generated_content = format_db_recipe_to_blog(st.session_state.selected_recipe_data)
                st.success(f"✅ '{selected_name}' 선택 완료!", icon="👍")
                st.session_state.show_selection = False
                st.rerun()

# --- Right Column (Output Display) ---
with col2:
    # Container with border for the output section
    output_container = st.container(border=True)

    with output_container:
        # --- Display Generated/Selected Content ---
        if st.session_state.generated_content:
            st.markdown(f"### 📝 **{st.session_state.last_searched_dish or '레시피'}** 포스트")
            
            # HTML 내용 표시
            components.html(st.session_state.generated_content, height=600, scrolling=True)

           # st.divider() # Separator before copy section

            # st.markdown("### 📋 블로그 포스트 복사")
            # --- 텍스트 버전 복사 (클립보드 복사 포함) ---
            from bs4 import BeautifulSoup

            # HTML → 줄글 텍스트 변환 
            soup = BeautifulSoup(st.session_state.generated_content, 'html.parser')
            text_only = soup.get_text(separator=' ')  # ✅ \n 대신 공백으로 묶어서 줄글 만들기
            text_only = text_only.strip().replace("'", "\\'").replace('"', '\\"')
 
            # 복사 버튼 영역
            unique_id = "textOnlyCopyBox" 
            components.html(f"""
                <textarea id="{unique_id}" style="position:absolute; left:-9999px;">{text_only}</textarea>
                <button onclick="copyToClipboard_{unique_id}()" style="width:100%; padding:10px; background-color:#4CAF50; color:white; border:none; border-radius:4px; cursor:pointer; font-size:16px; margin-top:10px;">
                    📋 텍스트 복사하기
                </button>
                <div id="copyMessage_{unique_id}" style="display:none; text-align:center; margin-top:10px; padding:8px; background-color:#E8F5E9; color:#2E7D32; border-radius:4px;">
                    ✅ 클립보드에 복사되었습니다!
                </div>
                <script>
                function copyToClipboard_{unique_id}() {{
                    var copyText = document.getElementById("{unique_id}");
                    if (!copyText) return;
                    navigator.clipboard.writeText(copyText.value).then(function() {{
                        var msg = document.getElementById("copyMessage_{unique_id}");
                        msg.style.display = "block";
                        setTimeout(function() {{ msg.style.display = "none"; }}, 3000);
                    }}).catch(function(err) {{
                        alert('복사 실패. 수동 복사 부탁함 ㅠㅠ');
                        console.error('복사 실패:', err);
                    }});
                }}
                </script>
            """, height=80)

            st.markdown("### 📋 블로그 포스트 복사")
            
            # Using text_area and components.html button again
            st.text_area(
                "아래 HTML 코드를 복사하여 네이버 블로그 에디터(HTML 편집 모드)에 붙여넣으세요:",
                st.session_state.generated_content,
                height=200,
                key="copy_area"
            )

            # Copy Button using components.html
            unique_id_part = "".join(filter(str.isalnum, st.session_state.last_searched_dish)) or "recipe"
            result_for_html = st.session_state.generated_content \
                .replace('\\', '\\\\').replace('\n', '\\n').replace('`', '\\`') \
                .replace("'", "\\'").replace('"', '\\"')

            components.html(f"""
                <textarea id="blogCode_{unique_id_part}" style="position:absolute;left:-9999px;">{result_for_html}</textarea>
                <button onclick="copyToClipboard_{unique_id_part}()" style="width:100%;padding:10px;background-color:#4CAF50;color:white;border:none;border-radius:4px;cursor:pointer;font-size:16px;margin-top:10px;">
                    📋 HTML 코드 복사하기
                </button>
                <div id="copyMessage_{unique_id_part}" style="display:none;text-align:center;margin-top:10px;padding:8px;background-color:#E8F5E9;color:#2E7D32;border-radius:4px;">
                    ✅ 클립보드에 복사되었습니다!
                </div>
                <script>
                function copyToClipboard_{unique_id_part}() {{
                    var copyText = document.getElementById("blogCode_{unique_id_part}");
                    if (!copyText) {{ console.error('Copy source element not found'); return; }}
                    if (navigator.clipboard && window.isSecureContext) {{
                        navigator.clipboard.writeText(copyText.value).then(function() {{
                            var copyMessage = document.getElementById("copyMessage_{unique_id_part}");
                            if(copyMessage) {{ copyMessage.innerText = '✅ 클립보드에 복사되었습니다!'; copyMessage.style.display = "block"; setTimeout(function() {{ copyMessage.style.display = "none"; }}, 3000); }}
                        }}, function(err) {{ console.error('Async: Could not copy: ', err); alert('복사 실패. 수동 복사해주세요.'); }});
                    }} else {{
                        copyText.select(); copyText.setSelectionRange(0, 99999);
                        try {{
                            var successful = document.execCommand('copy');
                            var msg = successful ? '✅ 클립보드에 복사되었습니다!' : '❌ 복사 실패';
                            var copyMessage = document.getElementById("copyMessage_{unique_id_part}");
                            if(copyMessage) {{ copyMessage.innerText = msg; copyMessage.style.display = "block"; setTimeout(function() {{ copyMessage.style.display = "none"; }}, 3000); }}
                        }} catch (err) {{ console.error('Fallback copy error', err); alert('복사 실패. 수동 복사해주세요.'); }}
                    }}
                }}
                </script>
            """, height=60)

        # Removed redundant message for selection (handled in col1)
        elif not st.session_state.generated_content and not st.session_state.show_selection:
            # Show initial prompt only if not showing selection list and no content generated
            st.info("👈 왼쪽에서 질문을 입력하고 '피드 생성하기' 버튼을 눌러주세요.", icon="💡")


# --- Sidebar ---
# This section is restored as per your request
with st.sidebar:
    st.markdown("## 🔍 사용 방법")
    st.markdown(f"""
    1. 검색/생성할 질문을 입력하세요. (DB 컬럼: `{COL_NAME}`)
    2. **'피드 생성하기'** 버튼 클릭!
    3. DB에 관련 내용이 있으면 표시되고, 없으면 AI가 생성합니다.
    4. 여러 결과가 나오면 목록에서 하나를 **선택** 후 **'선택 완료'** 버튼을 누르세요.
    5. 생성/선택된 내용을 확인하고 **'HTML 코드 복사하기'** 버튼을 눌러 복사하세요.
    6. 네이버 블로그 에디터의 **HTML 편집 모드**에 붙여넣으세요.
    """)

    st.divider() # Use divider in sidebar too
    st.markdown("## 💡 특징")
    st.markdown(""" 
    - 로컬 DB에서 내용 우선 검색
    - DB에 없는 경우 GPT-4o로 자동 생성
    - 검색 결과가 여러 개일 경우 선택 기능 제공  
    - 네이버 블로그 HTML 형식에 맞춰 결과 제공
    - 복사 버튼으로 쉽게 내용 복사
    """)

    st.divider()
    st.markdown("## ⚙️ 설정")
    st.markdown(f"""
    - **데이터베이스**: `{DB_FILENAME}` (없으면 자동 다운로드)
    - **테이블 이름 (설정값)**: `{TABLE_NAME}` (**DB 파일 내부의 실제 테이블 이름으로 수정 필요 시 코드 상단 변경**)
    - **AI 모델**: GPT-3.5-turbo
    """)
    if not db_available:
        st.warning(f"`{DB_FILENAME}` 파일 다운로드 실패 또는 파일 없음. DB 검색 기능이 제한될 수 있습니다.", icon="⚠️")

    st.divider()
    st.markdown("## 📌 네이버 블로그 팁")
    st.markdown("""
    - 복사한 내용을 붙여넣을 때 반드시 **HTML 편집 모드**를 사용하세요.
    - 이모지(🍳, 📝, ✅)는 대부분의 에디터에서 잘 표시됩니다.
    - 네이버 블로그의 '글 쓰기' 페이지에서 우측 하단의 'HTML' 버튼을 클릭하여 HTML 편집 모드로 전환한 후 붙여넣으세요.
    - 붙여넣은 후 '확인' 버튼을 누르면 스마트에디터에서 서식이 적용된 상태로 표시됩니다.
    """)