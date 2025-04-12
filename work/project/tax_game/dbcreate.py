# tax_game/dbcreate.py
import os
import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import sessionmaker, declarative_base

# 기본 설정
Base = declarative_base()
DATABASE_URL = "sqlite:///tax_game.db"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- 모델 정의 (변경 없음) ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False, unique=True, index=True)
    email = Column(String(100), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=True)
    score = Column(Integer, default=0)
    progress = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Scenario(Base):
    __tablename__ = "scenarios"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    initial_revenue = Column(Integer, nullable=False)
    max_deduction = Column(Integer, nullable=False)
    partial_deduction = Column(Integer, nullable=False)
    image_url = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Tutorial(Base):
    __tablename__ = "tutorials"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    content = Column(Text, nullable=True)
    image_url = Column(String(255), nullable=True)
    quiz_question = Column(String(255), nullable=True)
    quiz_answer = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class TaxBracket(Base):
    __tablename__ = "tax_brackets"
    id = Column(Integer, primary_key=True)
    min_income = Column(Integer, nullable=False)
    max_income = Column(Integer, nullable=False)
    tax_rate = Column(Float, nullable=False)
    progressive_deduction = Column(Integer, default=0)

class GameResult(Base):
    __tablename__ = "game_results"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", name="fk_gameresult_user"), nullable=True)
    scenario_id = Column(Integer, ForeignKey("scenarios.id", name="fk_gameresult_scenario"), nullable=False)
    decision = Column(String(50), nullable=False)
    revenue = Column(Integer, nullable=False)
    expense = Column(Integer, nullable=False)
    net_income = Column(Integer, nullable=False)
    tax = Column(Integer, nullable=False)
    score = Column(Integer, default=0)
    played_at = Column(DateTime(timezone=True), server_default=func.now())
# --- 모델 정의 끝 ---

# 데이터베이스 생성
def create_db():
    if os.path.exists("tax_game.db"):
        print("기존 tax_game.db 파일을 삭제합니다.")
        os.remove("tax_game.db")
    Base.metadata.create_all(bind=engine)
    print("데이터베이스 및 테이블이 생성되었습니다.")

# 시드 데이터 삽입 함수
def seed_data():
    session = SessionLocal()
    try:
        # 1. 사용자 데이터 (변경 없음)
        if session.query(User).first() is None:
            placeholder_user = User(username="player", email="player@example.com")
            session.add(placeholder_user); print("플레이스홀더 사용자 데이터 추가됨.")
        else: print("사용자 데이터가 이미 존재합니다.")

        # 2. 시나리오 데이터 (새 시나리오 추가)
        if session.query(Scenario).first() is None:
            scenario1 = Scenario(
                title="매출 급증 시나리오 (1억)",
                description="연 매출 1억원 달성! 필요 경비로 인정받을 수 있는 금액이 최대 5천만원까지 있지만, 꼼꼼히 챙기지 못하면 3천만원만 인정될 수도 있습니다. 어떤 선택이 세금에 어떤 영향을 미칠까요?",
                initial_revenue=100, max_deduction=50, partial_deduction=30,
                image_url="/static/images/scenario1_revenue_up.png"
            )
            scenario2 = Scenario(
                title="매출 안정기 시나리오 (5천)",
                description="연 매출 5천만원으로 안정적인 사업 운영 중. 필요 경비는 최대 2천만원까지 가능하지만, 1천만원만 처리할 수도 있습니다.",
                initial_revenue=50, max_deduction=20, partial_deduction=10,
                image_url="/static/images/scenario2_stable.png"
            )
            # --- 새 시나리오 추가 ---
            scenario3 = Scenario(
                title="프리랜서 첫 해 (3천)",
                description="디자이너로 독립한 첫 해! 연 수입 3천만원. 홈 오피스 비용, 소프트웨어 구독료 등을 경비 처리해야 하는데... 어디까지 인정될까?",
                initial_revenue=30, max_deduction=12, partial_deduction=6,
                image_url="/static/images/scenario3_freelancer.png" # 이미지 파일 준비 필요
            )
            scenario4 = Scenario(
                title="온라인 쇼핑몰 확장 (2억)",
                description="스마트 스토어 대박! 연 매출 2억원 돌파. 늘어난 광고비, 재고 관리 비용, 알바 인건비 등을 잘 처리해야 세금을 아낄 수 있다!",
                initial_revenue=200, max_deduction=90, partial_deduction=60,
                image_url="/static/images/scenario4_onlineshop.png" # 이미지 파일 준비 필요
            )
            # -----------------------
            # session.add_all 에 새 시나리오 포함
            session.add_all([scenario1, scenario2, scenario3, scenario4])
            print("시나리오 데이터 추가됨 (총 4개).")
        else:
            print("시나리오 데이터가 이미 존재합니다.")

        # 3. 튜토리얼 데이터 (변경 없음)
        if session.query(Tutorial).first() is None:
            tutorial1 = Tutorial(
                title="종합소득세, 어떻게 계산될까?",
                content="1년간의 총 수입(매출)에서 사업에 필요한 경비(비용)를 뺀 금액이 '소득금액'입니다. 이 소득금액에서 각종 공제를 제외한 '과세표준'에 세율을 곱해 세금이 결정됩니다. 경비 처리가 중요하겠죠?",
                image_url="https://via.placeholder.com/400x200.png?text=Tutorial+Image",
                quiz_question="수입에서 경비를 뺀 금액은 무엇일까요?", quiz_answer="소득금액"
            )
            session.add(tutorial1); print("튜토리얼 데이터 추가됨.")
        else: print("튜토리얼 데이터가 이미 존재합니다.")

        # 4. 누진세 구간 데이터 (변경 없음)
        if session.query(TaxBracket).first() is None:
            brackets = [
                TaxBracket(min_income=0, max_income=14, tax_rate=0.06, progressive_deduction=0),
                TaxBracket(min_income=14, max_income=50, tax_rate=0.15, progressive_deduction=126),
                TaxBracket(min_income=50, max_income=88, tax_rate=0.24, progressive_deduction=576),
                TaxBracket(min_income=88, max_income=150, tax_rate=0.35, progressive_deduction=1544),
                TaxBracket(min_income=150, max_income=300, tax_rate=0.38, progressive_deduction=1994),
                TaxBracket(min_income=300, max_income=500, tax_rate=0.40, progressive_deduction=2594),
                TaxBracket(min_income=500, max_income=1000, tax_rate=0.42, progressive_deduction=3594),
                TaxBracket(min_income=1000, max_income=999999, tax_rate=0.45, progressive_deduction=6594)
            ]
            session.add_all(brackets); print("누진세 구간 데이터 추가됨.")
        else: print("누진세 구간 데이터가 이미 존재합니다.")

        session.commit()
        print("모든 시드 데이터가 성공적으로 저장(또는 확인)되었습니다.")

    except Exception as e:
        print(f"데이터 시딩 중 오류 발생: {e}")
        session.rollback()
    finally:
        session.close()

# 메인 실행
if __name__ == "__main__":
    print("데이터베이스 생성 및 초기 데이터 삽입을 시작합니다...")
    create_db()
    seed_data()
    print("완료되었습니다.")