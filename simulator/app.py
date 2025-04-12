from flask import Flask, request, render_template
import pandas as pd

app = Flask(__name__)

#  상품 데이터 통합 엑셀에서 시트별로 한 번에 불러오기
excel_path = "C:/Users/Admin/Desktop/coaching/my_flask_app/전처리_금융상품_DB_가입경로포함.xlsx"
sheet_names = ["IRP", "연금저축펀드", "연금저축생명보험", "연금저축손해보험", "연금저축신탁", "ISA"]
product_dfs = {name: pd.read_excel(excel_path, sheet_name=name) for name in sheet_names}

#  개별 DataFrame 변수로 추출 (사용 편의성 위해)
irp_df = product_dfs["IRP"]
pension_fund = product_dfs["연금저축펀드"]
pension_life = product_dfs["연금저축생명보험"]
pension_damage = product_dfs["연금저축손해보험"]
pension_trust = product_dfs["연금저축신탁"]
isa_df = product_dfs["ISA"]

def get_product_recommendations(strategy):
    if strategy == "maximize_tax_saving":
        return irp_df.head(3), pension_fund.head(3)  # 높은 수익률 순
    elif strategy == "stable_growth":
        return pension_life.head(3), pension_trust.head(3)  # 보험·신탁 우선
    elif strategy == "hybrid":
        return irp_df.head(2), pension_life.head(2), pension_trust.head(2)

def suggest_strategy_allocation(strategy, budget):
    # budget: 여유금액 (만원)
    irp_rate, pension_rate, yellow_rate = 0.0, 0.0, 0.0
    if strategy == "maximize_tax_saving":
        irp_rate, pension_rate, yellow_rate = 0.4, 0.4, 0.2
    elif strategy == "stable_growth":
        irp_rate, pension_rate, yellow_rate = 0.2, 0.3, 0.5
    elif strategy == "hybrid":
        irp_rate, pension_rate, yellow_rate = 0.3, 0.3, 0.4

    return {
        "IRP": int(budget * irp_rate),
        "연금저축": int(budget * pension_rate),
        "노란우산": int(budget * yellow_rate)
    }

# 세액공제율
def get_tax_credit_rate(income, income_type):
    if (income_type == "사업소득자" and income <= 40000000) or \
       (income_type == "근로소득자" and income <= 55000000):
        return 0.165
    return 0.132

# 계산 함수
def calculate_tax_benefit(user):
    income = user['income'] * 10000
    irp = user['irp'] * 10000
    pension = user['pension'] * 10000
    yellow = user['yellow_umbrella'] * 10000
    isa = user['isa_joined'] == 'true'
    age = user['age']
    income_type = user['income_type']

    irp_limit = 7000000
    pension_limit = 4000000
    total_limit = 9000000
    yellow_limit = 5000000

    # 분배 계산
    if irp + pension <= total_limit:
        irp_credit = min(irp, irp_limit)
        pension_credit = min(pension, pension_limit)
    else:
        pension_credit = min(pension, pension_limit)
        irp_credit = min(irp, total_limit - pension_credit)

    rate = get_tax_credit_rate(income, income_type)
    irp_benefit = irp_credit * rate
    pension_benefit = pension_credit * rate
    yellow_benefit = min(yellow, yellow_limit) * 0.08

    total_year = irp_benefit + pension_benefit + yellow_benefit

    return {
        "user": user,
        "세액공제_합계": round(irp_benefit + pension_benefit) ,
        "소득공제_합계": round(yellow_benefit) ,
        "ISA_절세효과": "청년형 ISA 가능 시 400만 원까지 비과세, 일반형은 200만 원까지 비과세" if isa else "ISA 미가입",
        "향후_5년_예상절세액": round(total_year * 5) ,
        "추가_납입_권장": {
            "irp": max(0, irp_limit - irp),
            "pension": max(0, pension_limit - pension),
            "yellow_umbrella": "추가 가능" if yellow < yellow_limit else "한도 도달"
        }
    }

def get_recommended_products(strategy, top_n=3):
    recommendations = {}

    if strategy == "maximize_tax_saving":
        recommendations["IRP 추천"] = irp_df.sort_values(by=irp_df.columns[8], ascending=False).head(top_n)
        recommendations["연금저축펀드 추천"] = pension_fund.sort_values(by=pension_fund.columns[8], ascending=False).head(top_n)

    elif strategy == "stable_growth":
        rec = irp_df[irp_df.iloc[:, 1].astype(str).str.contains("보장", na=False)].head(top_n)
        recommendations["안정형 IRP 추천"] = rec
        recommendations["생명보험 추천"] = pension_life.head(top_n)
        recommendations["신탁 추천"] = pension_trust.head(top_n)

    elif strategy == "hybrid":
        irp_top = irp_df.sort_values(by=irp_df.columns[8], ascending=False).head(2)
        life_top = pension_life.head(1)
        fund_top = pension_fund.sort_values(by=pension_fund.columns[8], ascending=False).head(1)
        recommendations["IRP 추천"] = irp_top
        recommendations["연금저축펀드 추천"] = fund_top
        recommendations["생명보험 추천"] = life_top

    # 가입경로 포함된 엑셀 기반이므로 이미 가입경로 열 존재
    for key in recommendations:
        df = recommendations[key].copy()
        recommendations[key] = df[[df.columns[0], df.columns[1], df.columns[8], "가입경로"]]

    return recommendations


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/products")
def products():
    return render_template("products.html", irp_list=irp_df, pension_list=pension_df, isa_list=isa_df)

@app.route("/dashboard/products")
def product_dashboard():
    products = {
        "IRP 상품": irp_df,
        "연금저축 펀드": pension_fund,
        "연금저축 생명보험": pension_life,
        "연금저축 손해보험": pension_damage,
        "연금저축 신탁": pension_trust,
        "ISA 상품": isa_df
    }
    return render_template("pddashboard.html", products=products)

@app.route("/dashboard", methods=["POST"])
def dashboard():
    form = request.form
    user = {
        "age": int(form['age']),
        "income": int(form['income']),
        "income_type": form['income_type'],
        "yellow_umbrella": int(form['yellow_umbrella']),
        "irp": int(form['irp']),
        "pension": int(form['pension']),
        "isa_joined": form['isa_joined']
    }
    # 기존 시뮬레이션 결과
    result = calculate_tax_benefit(user)

    # 🔥 전략 및 예산 추가 처리
    strategy = form['strategy']
    extra_budget = int(form['extra_budget'])  # 만원 단위
    allocation = suggest_strategy_allocation(strategy, extra_budget)
    result["전략별_제안"] = allocation


    # ⭐️ 전략 기반 추천 상품 가져오기
    recommended = get_recommended_products(strategy)

    # ⭐️ 추천 결과도 함께 템플릿에 전달
    return render_template("dashboard.html", user=user, result=result, recommended=recommended)

if __name__ == "__main__":
    app.run(debug=True)
