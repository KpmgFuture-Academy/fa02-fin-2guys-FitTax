# tax_game/app.py
import os
import json
import secrets
import random # 랜덤 이벤트, 미니게임 등 위해 필요
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort, jsonify # jsonify 추가
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from sqlalchemy import func

app = Flask(__name__)
# Session 사용을 위해 Secret Key 필요 (환경 변수 사용 권장)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(16))
# --- 사용자 지정 데이터베이스 절대 경로 ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///C:/project/tax_game/tax_game.db'
# ------------------------------------
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- 모델 정의 ---
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True, index=True)
    username = db.Column(db.String(50), nullable=False, unique=True, index=True)
    email = db.Column(db.String(100), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=True) # 인증 없으므로 nullable
    score = db.Column(db.Integer, default=0)
    progress = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Scenario(db.Model):
    __tablename__ = "scenarios"
    id = db.Column(db.Integer, primary_key=True, index=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    initial_revenue = db.Column(db.Integer, nullable=False) # 단위: 백만원
    max_deduction = db.Column(db.Integer, nullable=False)   # 단위: 백만원
    partial_deduction = db.Column(db.Integer, nullable=False) # 단위: 백만원
    image_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Tutorial(db.Model):
    __tablename__ = "tutorials"
    id = db.Column(db.Integer, primary_key=True, index=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    quiz_question = db.Column(db.String(255), nullable=True)
    quiz_answer = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class TaxBracket(db.Model):
    __tablename__ = "tax_brackets"
    id = db.Column(db.Integer, primary_key=True)
    min_income = db.Column(db.Integer, nullable=False)      # 단위: 백만원
    max_income = db.Column(db.Integer, nullable=False)      # 단위: 백만원
    tax_rate = db.Column(db.Float, nullable=False)
    progressive_deduction = db.Column(db.Integer, default=0) # 누진 공제액 (단위: 만원)

class GameResult(db.Model):
    __tablename__ = "game_results"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) # nullable=True
    scenario_id = db.Column(db.Integer, db.ForeignKey('scenarios.id'), nullable=False)
    decision = db.Column(db.String(50), nullable=False)
    revenue = db.Column(db.Integer, nullable=False)          # 단위: 백만원
    expense = db.Column(db.Integer, nullable=False)          # 단위: 백만원 (미니게임 보너스 없음)
    net_income = db.Column(db.Integer, nullable=False)       # 단위: 백만원 (과세표준)
    tax = db.Column(db.Integer, nullable=False)              # 단위: 만원
    score = db.Column(db.Integer, default=0)                 # 최종 점수 (랜덤 이벤트 포함)
    played_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

# --- 관리자 모드 (Flask-Admin) ---
admin = Admin(app, name='TaxGame Admin', template_mode='bootstrap4')
admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Scenario, db.session))
admin.add_view(ModelView(Tutorial, db.session))
admin.add_view(ModelView(TaxBracket, db.session))
admin.add_view(ModelView(GameResult, db.session))

# --- 누진세 계산 함수 (수정 완료된 버전) ---
def calculate_progressive_tax(income_million):
    """
    과세표준(백만원 단위)을 입력받아 누진세를 계산합니다.
    세금은 만원 단위로 반환합니다. (세금액, 적용세율) 튜플 반환.
    """
    if income_million <= 0:
        print(f"정보: 소득 {income_million}백만원 <= 0 이므로 세금 없음.")
        return 0, 0.0
    bracket = TaxBracket.query.filter(
        TaxBracket.min_income < income_million, TaxBracket.max_income >= income_million
    ).first()
    if not bracket:
        print(f"정보: 소득 {income_million}백만원에 대한 정확한 구간 없음. 최고 구간 검색 시도.")
        bracket = TaxBracket.query.filter(
            TaxBracket.min_income < income_million
        ).order_by(TaxBracket.max_income.desc()).first()
    if not bracket:
        print(f"경고: 소득 {income_million}백만원에 적용할 세율 구간을 찾을 수 없습니다. DB 데이터를 확인하세요.")
        return 0, 0.0
    print(f"정보: 소득 {income_million}백만원에 적용될 구간: ID={bracket.id}, Rate={bracket.tax_rate}, Min={bracket.min_income}, Max={bracket.max_income}, ProgDeduct={bracket.progressive_deduction}")
    tax_amount_won = (income_million * 10000 * bracket.tax_rate) - bracket.progressive_deduction
    final_tax = int(max(0, tax_amount_won))
    return final_tax, bracket.tax_rate

# --- 랜덤 이벤트 정의 ---
RANDOM_EVENTS = [
    {'description': "💡 새로운 절세 아이디어가 떠올랐습니다! 다음번엔 더 잘할 수 있을 거예요!", 'score_bonus': 5},
    {'description': "💸 길에서 우연히 1만원을 주웠습니다! 소소한 행운이네요.", 'score_bonus': 1},
    {'description': "✨ 당신의 가게/서비스가 SNS에서 좋은 반응을 얻고 있습니다!", 'score_bonus': 3},
    {'description': "☕️ 너무 열심히 일했나요? 커피 한 잔 마시며 잠시 쉬었습니다.", 'score_bonus': 0},
    {'description': "🤔 세금 관련 기사를 읽으며 유용한 정보를 얻었습니다.", 'score_bonus': 2},
    {'description': "앗! 노트북에 음료수를 살짝 쏟았지만 다행히 고장나진 않았어요.", 'score_bonus': -1},
]
EVENT_PROBABILITY = 0.30 # 이벤트 발생 확률 30%

# --- 라우트 정의 ---
@app.route('/')
def index():
    scenarios = Scenario.query.order_by(Scenario.id).all()
    tutorials = Tutorial.query.order_by(Tutorial.id).all()
    # 세션 정리
    session.pop('decision', None)
    session.pop('scenario_id', None)
    session.pop('minigame_score', None)
    return render_template('index.html', scenarios=scenarios, tutorials=tutorials)

@app.route('/tutorial/<int:tutorial_id>')
def tutorial(tutorial_id):
    tutorial_item = db.get_or_404(Tutorial, tutorial_id)
    return render_template('tutorial.html', tutorial=tutorial_item)

# 시나리오 페이지: 결정 시 바로 결과 페이지로 리디렉션
@app.route('/scenario/<int:scenario_id>', methods=['GET', 'POST'])
def scenario(scenario_id):
    scenario_item = db.get_or_404(Scenario, scenario_id)
    if request.method == 'POST':
        decision = request.form.get('decision')
        if decision not in ['max_expense', 'partial_expense']:
             flash('유효하지 않은 선택입니다.', 'error')
             return redirect(url_for('scenario', scenario_id=scenario_id))
        session['decision'] = decision
        session['scenario_id'] = scenario_item.id
        return redirect(url_for('result')) # 결과 페이지로 바로 이동
    return render_template('scenario.html', scenario=scenario_item)


# --- 미니게임 라우트 (독립 실행) ---
# 미니게임 페이지 표시
@app.route('/practice/documents') # URL 경로 (터미널 출력 기준)
def document_finder_practice(): # 함수 이름 = 엔드포인트 이름 (터미널 출력 기준)
    print("독립 실행형 미니게임 페이지 로드") # 서버 로그에 표시
    return render_template('receipt_minigame.html', time_limit=15)

# 미니게임 결과 제출 처리
@app.route('/practice/submit', methods=['POST']) # URL 경로 (터미널 출력 기준)
def submit_practice_result(): # 함수 이름 = 엔드포인트 이름 (터미널 출력 기준)
    data = request.get_json()
    if data is None: return jsonify({'status': 'error', 'message': 'Invalid request data'}), 400
    minigame_score = data.get('bonus', 0) # 'bonus' 키로 점수(찾은 개수) 받음
    try: minigame_score = int(minigame_score)
    except (ValueError, TypeError): return jsonify({'status': 'error', 'message': 'Invalid score value'}), 400

    session['minigame_score'] = max(0, minigame_score) # 세션에 점수 임시 저장
    print(f"독립 미니게임 결과: 점수 {session['minigame_score']} 저장됨")
    return jsonify({'status': 'success', 'redirect_url': url_for('minigame_result_page')}) # 결과 페이지 URL 전달

# 미니게임 결과 표시 페이지
@app.route('/minigame/result') # 결과 페이지 URL
def minigame_result_page(): # 결과 페이지 함수 = 엔드포인트 이름
    score = session.pop('minigame_score', 0) # 세션에서 점수 가져오고 삭제
    return render_template('minigame_result.html', score=score)
# --- 미니게임 라우트 끝 ---


# 결과 페이지 (시나리오 결과)
@app.route('/result')
def result():
    decision = session.get('decision')
    scenario_id = session.get('scenario_id')

    if not decision or not scenario_id:
        flash('잘못된 접근입니다. 시나리오를 먼저 진행해주세요.', 'warning')
        session.pop('decision', None); session.pop('scenario_id', None)
        return redirect(url_for('index'))

    scenario_item = db.get_or_404(Scenario, scenario_id)
    revenue = scenario_item.initial_revenue
    expense = 0
    alternative_expense = 0

    if decision == "max_expense":
        expense = scenario_item.max_deduction
        feedback = f"최대 비용({expense}백만원) 공제를 선택했습니다."
        alternative_expense = scenario_item.partial_deduction
    elif decision == "partial_expense":
        expense = scenario_item.partial_deduction
        feedback = f"일부 비용({expense}백만원) 공제를 선택했습니다."
        alternative_expense = scenario_item.max_deduction

    net_income = max(0, revenue - expense)
    tax, tax_rate = calculate_progressive_tax(net_income)

    alternative_net_income = max(0, revenue - alternative_expense)
    alternative_tax, _ = calculate_progressive_tax(alternative_net_income)
    tax_difference = alternative_tax - tax
    initial_score = int(max(0, tax_difference) / 10)

    event_description = None; final_score = initial_score
    if random.random() < EVENT_PROBABILITY:
        selected_event = random.choice(RANDOM_EVENTS)
        event_description = selected_event['description']
        score_bonus = selected_event.get('score_bonus', 0)
        final_score = max(0, initial_score + score_bonus)
        if score_bonus != 0: feedback += f" (✨깜짝 이벤트: 점수 {score_bonus:+}점!)"

    placeholder_user = User.query.filter_by(username="player").first()
    user_id = placeholder_user.id if placeholder_user else None
    try:
        game_result = GameResult(
            user_id=user_id, scenario_id=scenario_item.id, decision=decision,
            revenue=revenue, expense=expense, net_income=net_income, tax=tax,
            score=final_score
        )
        db.session.add(game_result); db.session.commit()
    except Exception as e:
        db.session.rollback(); print(f"게임 결과 저장 오류: {e}")
        flash("게임 결과를 저장하는 중 오류가 발생했습니다.", "error")

    session.pop('decision', None)
    session.pop('scenario_id', None)

    return render_template('result.html',
                           revenue=revenue, expense=expense, net_income=net_income,
                           tax_rate=tax_rate * 100, tax=tax, score=final_score,
                           feedback=feedback, scenario_image_url=scenario_item.image_url,
                           alternative_expense=alternative_expense, alternative_tax=alternative_tax,
                           tax_difference=tax_difference, event_description=event_description
                           )

# --- 애플리케이션 실행 ---
if __name__ == '__main__':
    # 디버깅용 라우트 출력 코드 제거됨
    with app.app_context(): db.create_all()
    app.run(debug=True)