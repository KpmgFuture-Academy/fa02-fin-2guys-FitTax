from flask import Flask, render_template, request, session, redirect, url_for
import time, random

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 실제 배포 시에는 보다 안전한 키 사용

# 퀴즈 데이터에 난이도 필드 추가 (난이도: 하, 중, 상)
quizzes = [
    {
        'question': '친구가 알바하는데 월급에서 세금이 너무 많이 나간대. 왜 그런 걸까?',
        'options': ['친구가 돈을 너무 많이 벌어서', '소득세가 원래 그렇게 많이 나가서', '아마 4대 보험료가 포함돼서 그럴 거야', '친구가 세금을 안 내려고 꼼수를 부려서'],
        'answer': 2,
        'explanation': '아르바이트 급여에서 세금과 함께 4대 보험료(국민연금, 건강보험, 고용보험, 산재보험)가 공제될 수 있습니다.',
        'difficulty': '하'
    },
    {
        'question': '프리랜서로 웹사이트 디자인 알바를 하고 50만원을 받았어. 세금은 어떻게 해야 해?',
        'options': ['50만원 정도는 그냥 넘어가도 돼', '내년 5월에 종합소득세 신고해야 해', '받을 때 이미 세금 떼고 받았을 거야', '세금 내는 건 사업자만 하는 거 아니야?'],
        'answer': 1,
        'explanation': '프리랜서 소득은 내년 5월에 종합소득세 신고를 통해 정산해야 합니다. 소득 종류에 따라 원천징수되었을 수도 있습니다.',
        'difficulty': '중'
    },
    {
        'question': '연말정산 때 혼자 사는 \'청년\'에게 유리한 혜택이 있을까?',
        'options': ['응, 당연히 있지! 주택 관련 공제 같은 거', '아니, 결혼한 사람만 혜택이 많아', '잘 모르겠는데?', '혼자 살면 세금 더 내야 해'],
        'answer': 0,
        'explanation': '월세 세액공제, 주택자금대출 이자 상환액 공제 등 혼자 사는 청년도 받을 수 있는 세금 혜택이 있습니다.',
        'difficulty': '중'
    },
    {
        'question': '세금을 아끼려면 \'이것\'을 꼼꼼히 챙겨야 한다던데, \'이것\'은 뭘까?',
        'options': ['오늘 점심 메뉴', '친구들과의 약속', '영수증', '내일 할 일'],
        'answer': 2,
        'explanation': '각종 소득공제 및 세액공제를 받기 위해서는 관련 영수증을 잘 챙기는 것이 중요합니다.',
        'difficulty': '하'
    },
    {
        'question': '만약 세금을 안 내면 어떤 일이 벌어질까?',
        'options': ['운이 좋으면 그냥 넘어간다', '나중에 가산세가 붙어서 더 많은 돈을 내야 할 수도 있어', '바로 감옥에 간다', '아무 일도 안 일어난다'],
        'answer': 1,
        'explanation': '세금을 제때 납부하지 않으면 가산세가 부과될 수 있으며, 심한 경우 법적인 불이익을 받을 수도 있습니다.',
        'difficulty': '상'
    }
]

# 사전학습 데이터: 세금 관련 용어와 풀이 (예시)
pre_learning_data = {
    'terms': [
        {'term': '원천징수', 'definition': '지급 시 세금을 미리 떼어내는 제도'},
        {'term': '종합소득세', 'definition': '한 해 동안의 모든 소득에 대해 부과하는 세금'},
        {'term': '세액공제', 'definition': '납부할 세금에서 일정 금액을 공제해 주는 제도'},
        {'term': '소득공제', 'definition': '과세표준을 줄여 실제 납부해야 하는 세금을 낮추는 제도'},
        {'term': '4대 보험', 'definition': '국민연금, 건강보험, 고용보험, 산재보험을 통칭'}
    ],
    'explanations': [
        {'title': '원천징수', 'content': '원천징수는 급여 지급 시 미리 세금을 차감하여 국가에 납부하는 제도입니다.'},
        {'title': '종합소득세', 'content': '종합소득세는 개인의 모든 소득을 합산하여 부과되는 세금으로, 일정 소득 이상인 경우 신고 의무가 있습니다.'},
        {'title': '세액공제와 소득공제', 'content': '세액공제는 납부해야 할 세금 자체를 줄여주고, 소득공제는 과세표준을 줄여주는 방식입니다.'},
        {'title': '4대 보험', 'content': '4대 보험은 국민연금, 건강보험, 고용보험, 산재보험으로 구성되며, 사회 안전망 및 복지의 중요한 역할을 합니다.'}
    ]
}

# 사용자가 뒤집을 수 있는 최대 카드 수
MAX_FLIPS = 3

@app.route('/')
def index():
    return render_template('index.html')

# 사전학습 페이지 (용어와 풀이로 분리)
@app.route('/pre_learning')
def pre_learning():
    return render_template('pre_learning.html', data=pre_learning_data)

@app.route('/start_quiz')
def start_quiz():
    session['score'] = 0
    session['flip_count'] = 0
    # 퀴즈 데이터를 복사하고 무작위 순서로 섞은 후, 각 카드에 뒤집힘(flipped)과 답변 여부(answered) 플래그 추가
    cards = quizzes[:]  # 얕은 복사
    random.shuffle(cards)
    for card in cards:
        card['flipped'] = False
        card['answered'] = False
    session['cards'] = cards
    return redirect(url_for('cards'))

@app.route('/cards')
def cards():
    cards = session.get('cards', [])
    flip_count = session.get('flip_count', 0)
    can_flip_more = flip_count < MAX_FLIPS
    return render_template('cards.html', cards=cards, can_flip_more=can_flip_more, flip_count=flip_count, max_flips=MAX_FLIPS)

@app.route('/card/<int:card_id>', methods=['GET', 'POST'])
def card(card_id):
    cards = session.get('cards', [])
    if card_id < 0 or card_id >= len(cards):
        return redirect(url_for('cards'))
    card_data = cards[card_id]

    # 아직 뒤집히지 않은 카드면, 뒤집기 가능 여부(MAX_FLIPS 미만) 확인 후 뒤집음
    if not card_data.get('flipped', False):
        if session.get('flip_count', 0) >= MAX_FLIPS:
            return redirect(url_for('cards'))
        card_data['flipped'] = True
        session['flip_count'] = session.get('flip_count', 0) + 1
        session.modified = True

    if request.method == 'POST':
        selected_answer = request.form.get('answer')
        correct_answer_index = card_data['answer']
        if not card_data.get('answered', False):
            if selected_answer is not None and int(selected_answer) == correct_answer_index:
                session['score'] += 1
                feedback = {'correct': True, 'explanation': card_data['explanation']}
            else:
                feedback = {'correct': False, 'explanation': card_data['explanation'], 'correct_answer': card_data['options'][correct_answer_index]}
            card_data['answered'] = True
            session.modified = True
            session['last_feedback'] = feedback
            return redirect(url_for('feedback'))
    return render_template('card.html', card=card_data, card_id=card_id)

@app.route('/feedback')
def feedback():
    feedback_data = session.pop('last_feedback', None)
    if feedback_data:
        return render_template('feedback.html', feedback=feedback_data)
    else:
        return redirect(url_for('cards'))

@app.route('/result')
def result():
    score = session.get('score', 0)
    total_questions = MAX_FLIPS  # 3문제에 대한 점수
    # 세션 초기화
    session.pop('cards', None)
    session.pop('flip_count', None)
    session.pop('score', None)
    return render_template('result.html', score=score, total_questions=total_questions)

if __name__ == '__main__':
    app.run(debug=True)
