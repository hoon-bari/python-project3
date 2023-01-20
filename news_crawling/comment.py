# step1. 관련 패키지 및 모듈 불러오기
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from datetime import datetime
import time
import pandas as pd


# step2. 네이버 뉴스 댓글정보 수집 함수
def get_naver_news_comments(url, wait_time=5, delay_time=0.1):
    
    # 크롬 드라이버로 해당 url에 접속
    chrome_options = Options()
    chrome_options.page_load_strategy = 'none'
    chrome_options.add_argument('headless')
    chrome_options.add_argument("disable-gpu")
    chrome_options.add_argument("--kiosk")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    # (크롬)드라이버가 요소를 찾는데에 최대 wait_time 초까지 기다림 (함수 사용 시 설정 가능하며 기본값은 5초)
    driver.implicitly_wait(wait_time)
    
    # 인자로 입력받은 url 주소를 가져와서 접속
    driver.get(url)

    # 더보기가 안뜰 때 까지 계속 클릭 (모든 댓글의 html을 얻기 위함)
    while True:
        
        # 예외처리 구문 - 더보기 광클하다가 없어서 에러 뜨면 while문을 나감(break)
        try:
            more = driver.find_element(By.CSS_SELECTOR, 'a.u_cbox_btn_more')
            more.click()
            time.sleep(delay_time)
            
        except:
            break

    # 본격적인 크롤링 타임
    
    # 1)작성자
    # selenium으로 작성자 포함된 태그 모두 수집
    nicknames = driver.find_elements(By.CSS_SELECTOR,'span.u_cbox_nick')
    # 리스트에 텍스트만 담기 (리스트 컴프리핸션 문법)
    list_nicknames = [nick.text for nick in nicknames]

    # 2)댓글 시간
    # selenium으로 댓글 시간 포함된 태그 모두 수집
    createds_at = driver.find_elements(By.CSS_SELECTOR,'span.u_cbox_date')
    # 리스트에 텍스트만 담기 (리스트 컴프리핸션 문법)
    list_datetimes = []
    for created_at in createds_at:
        created_at = created_at.text
        if int(created_at[12:14]) >= 12:
            created_at = created_at[:12] + 'PM ' + str(int(created_at[12:14])-12) + created_at[14:17]
        else:
            created_at = created_at[:12] + 'AM ' + created_at[12:17]
        created_at = datetime.strptime(created_at, '%Y.%m.%d. %p %H:%M')
        list_datetimes.append(created_at)

    # 3)댓글 내용
    # selenium으로 댓글내용 포함된 태그 모두 수집
    contents = driver.find_elements(By.CSS_SELECTOR,'span.u_cbox_contents')
    # 리스트에 텍스트만 담기 (리스트 컴프리핸션 문법)
    list_contents = [content.text for content in contents]

    # 4)댓글 좋아요 수
    likes = driver.find_elements(By.CSS_SELECTOR,'div > a.u_cbox_btn_recomm > em')
    # 리스트에 텍스트만 담기 (리스트 컴프리핸션 문법)
    list_likes = [like.text for like in likes]

    # 5)댓글 싫어요 수
    dislikes = driver.find_elements(By.CSS_SELECTOR,'div > a.u_cbox_btn_unrecomm > em')
    # 리스트에 텍스트만 담기 (리스트 컴프리핸션 문법)
    list_dislikes = [dislike.text for dislike in dislikes]
    
    print(list_nicknames)
    print(list_contents)
    print(list_likes)
    print(list_dislikes)
    print(list_datetimes)

    # step3. 그대로 dbeaver로
    import pymysql

    connection = pymysql.connect(host='localhost', user='root', port = 3306, password = "clftjd4dlek!", db = 'third_project', charset = 'utf8mb4', use_unicode=True, cursorclass=pymysql.cursors.DictCursor)
    cur = connection.cursor()

    for nick, content, like, dislike, created_at in zip(list_nicknames, list_contents, list_likes, list_dislikes, list_datetimes):
        
        sql = """INSERT INTO main_page_newscomment (username, comment_content, comment_like, comment_dislike, created_at) VALUES(%s, %s, %s, %s, %s)"""
        cur.execute(sql, ('%s'%(nick), '%s'%(content), '%s'%(like), '%s'%(dislike), '%s'%(created_at)))
        connection.commit()

    connection.close()

    # 드라이버 종료
    driver.quit()
    
# step4. 실제 함수 실행
if __name__ == '__main__': # 설명하자면 매우 길어져서 그냥 이렇게 사용하는 것을 권장
    
    # 원하는 기사 url 입력
    url = 'https://n.news.naver.com/mnews/article/comment/008/0004841493?sid=101'
    
    # 함수 실행
    comments = get_naver_news_comments(url)