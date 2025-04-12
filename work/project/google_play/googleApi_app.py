from google_play_scraper import reviews, Sort
import pandas as pd
import re  # URL에서 앱 ID를 추출하기 위한 정규 표현식

#창업세무

urlList=[{'ID':1,
          'Site':'https://play.google.com/store/apps/details?id=com.emmental.bznav.mobile&hl=ko',
          'count':1000 },

         {'ID':2,
          'Site':'https://play.google.com/store/apps/details?id=com.taxbyapp.taxby&hl=ko',
          'count':1000},
         {'ID':3,
          'Site':'https://play.google.com/store/apps/details?id=com.kicc.easyshop.autobooks&hl=ko',
          'count':1000},
         {'ID':4,
          'Site': 'https://play.google.com/store/apps/details?id=com.findsemu.app.android.user&hl=ko',
          'count':1000},
         {'ID':5,
         'Site': 'https://play.google.com/store/apps/details?id=com.seduri.mobile&hl=ko',
         'count':1000},
         {'ID':6,
         'Site':'https://play.google.com/store/apps/details?id=com.semutong.mobile&hl=ko',
         'count':1000},
         {'ID':7,
         'Site': 'https://play.google.com/store/apps/details?id=cashnote.com.albatross&hl=ko',
         'count':1000},
         {'ID':8,
         'Site': 'https://play.google.com/store/apps/details?id=kr.co.taxnet.taxDiary&hl=ko',
         'count':1000},
         {'ID':9,
          'Site':'https://play.google.com/store/apps/details?id=com.nullee.ssem&hl=ko',
         'count':500000},
         {'ID':10,
          'Site': 'https://play.google.com/store/apps/details?id=co.jobis.szs&hl=ko',
         'count':1000000}]


def get_korean_reviews(app_id, count):
    """
    구글 플레이 스토어에서 한국어 앱 리뷰를 가져옵니다.

    Args:
        app_id (str): 앱 ID (예: 'com.kakao.talk')
        count (int): 가져올 리뷰 개수

    Returns:
        list: 리뷰 목록 (오류 발생 시 빈 리스트 반환)
    """
    try:
        result, _ = reviews(
            app_id,
            lang='ko', #한국어 설정
            sort=Sort.NEWEST,
            count=count
        )
        return result
    except Exception as e:
        print(f"리뷰 수집 오류 발생: {e}")
        return

all_reviews_data =[]

# urlList의 각 딕셔너리에서 정보를 추출하고 리뷰를 가져와 리스트에 추가합니다.
for item in urlList:
    app_id = re.search(r'id=([^&]+)', item['Site']).group(1)
    count = item['count']
    app_id_num = item['ID']
    print(f"앱 ID ({app_id_num}): {app_id}, 가져올 리뷰 수: {count}")
    korean_reviews = get_korean_reviews(app_id, count)

    if korean_reviews:
        df = pd.DataFrame(korean_reviews)
        df['app_id_num'] = app_id_num  # 앱 ID를 데이터프레임에 추가
        all_reviews_data.append(df)
        print(f"앱 ID ({app_id_num}) 리뷰 수집 완료")
    else:
        print(f"앱 ID ({app_id_num})의 한국어 앱 리뷰 수집 실패")

# 모든 앱의 리뷰 데이터를 하나의 데이터프레임으로 합치기
if all_reviews_data:
    combined_df = pd.concat(all_reviews_data, ignore_index=True)
    filename = './all_korean_app_reviews1.csv'
    combined_df.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"모든 앱 리뷰 저장 완료: {filename}")
else:
    print("수집된 리뷰 데이터가 없습니다.")