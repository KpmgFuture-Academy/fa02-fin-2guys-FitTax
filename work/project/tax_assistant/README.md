# 개인사업자 부가세 신고 어시스턴트

개인사업자의 부가세 신고를 돕는 AI 기반 챗봇 어시스턴트입니다. 카드사 데이터 자동 전처리, 부가세 계산, 신고 관련 조언 등 다양한 기능을 제공합니다.

## 주요 기능

- **카드사 데이터 자동 전처리**: 다양한 카드사(롯데, 신한, 삼성 등)의 엑셀 데이터 분석
- **데이터 시각화**: 월별 및 가맹점별 지출 현황 시각화
- **부가세 계산**: 공급가액, 부가세 등 자동 계산
- **AI 기반 챗봇**: 부가세 신고 관련 질의응답
- **세금 계산기**: 부가세 계산 및 세금계산서 작성 도우미

## 설치 방법

### 1. 저장소 클론

```bash
git clone https://github.com/yourusername/tax_assistant.git
cd tax_assistant
```

### 2. 가상환경 생성 및 활성화

```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. 패키지 설치

```bash
pip install -e .
```

## 사용 방법

```bash
streamlit run run.py
```

브라우저에서 `http://localhost:8501`으로 접속하여 애플리케이션을 사용할 수 있습니다.

## 프로젝트 구조

```
tax_assistant/
├── preprocessing/       # 카드사 데이터 전처리 모듈
│   ├── __init__.py
│   ├── lotte_card.py    # 롯데카드 전처리
│   ├── shinhan_card.py  # 신한카드 전처리
│   └── samsung_card.py  # 삼성카드 전처리
├── analysis/            # 데이터 분석 모듈
│   ├── __init__.py
│   ├── summary.py       # 데이터 요약
│   └── visualization.py # 시각화
├── chatbot/             # AI 챗봇 모듈
│   ├── __init__.py
│   ├── agent.py         # LangChain 에이전트
│   ├── tools.py         # 커스텀 도구
│   └── prompts.py       # 프롬프트 템플릿
├── utils/               # 유틸리티 모듈
│   ├── __init__.py
│   └── helpers.py       # 유틸리티 함수
├── app.py               # 메인 Streamlit 애플리케이션
└── requirements.txt     # 패키지 의존성
```

## API 키 설정

애플리케이션에서 챗봇 기능을 사용하기 위해서는 OpenAI API 키가 필요합니다:

1. OpenAI 계정 생성 및 API 키 발급: [OpenAI API](https://platform.openai.com/)
2. 애플리케이션 사이드바에 API 키 입력

## 지원하는 카드사

- 롯데카드
- 신한카드
- 삼성카드
- 기타 (기본 전처리 로직 적용)

추가 카드사 지원은 계속 업데이트될 예정입니다.

## 라이센스

이 프로젝트는 MIT 라이센스를 따릅니다.

## 주의사항

- 이 애플리케이션은 부가세 신고 참고용으로만 사용하시고, 정확한 세무 처리는 전문가와 상담하시기 바랍니다.
- 카드사 데이터 형식이 변경될 경우 전처리 오류가 발생할 수 있습니다.
- OpenAI API 사용에 따른 비용이 발생할 수 있습니다.