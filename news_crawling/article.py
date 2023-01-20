# 크롤링시 필요한 라이브러리 불러오기
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time
import requests
import re
from datetime import datetime
from tqdm import tqdm

# 페이지 url 형식에 맞게 바꾸어 주는 함수 만들기
  #입력된 수를 1, 11, 21, 31 ...만들어 주는 함수
def makePgNum(num):
    if num == 1:
        return num
    elif num == 0:
        return num+1
    else:
        return num+9*(num-1)

# 크롤링할 url 생성하는 함수 만들기(검색어, 크롤링 시작 페이지, 크롤링 종료 페이지)

def makeUrl(search, start_pg, end_pg):
    if start_pg == end_pg:
        start_page = makePgNum(start_pg)
        url = "https://search.naver.com/search.naver?where=news&sm=tab_pge&query=" + search + "&start=" + str(start_page)
        print("생성url: ", url)
        return [url]
    else:
        urls = []
        for i in range(start_pg, end_pg + 1):
            page = makePgNum(i)
            url = "https://search.naver.com/search.naver?where=news&sm=tab_pge&query=" + search + "&start=" + str(page)
            urls.append(url)
        print("생성url: ", urls)
        return urls    

# html에서 원하는 속성 추출하는 함수 만들기 (기사, 추출하려는 속성값)
def news_attrs_crawler(articles,attrs):
    attrs_content=[]
    for i in articles:
        attrs_content.append(i.attrs[attrs])
    return attrs_content

# ConnectionError방지
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"}

#html생성해서 기사크롤링하는 함수 만들기(url): 링크를 반환
def articles_crawler(url):
    #html 불러오기
    original_html = requests.get(i,headers=headers)
    html = BeautifulSoup(original_html.text, "html.parser")

    url_naver = html.select("div.group_news > ul.list_news > li div.news_area > div.news_info > div.info_group > a.info")
    url = news_attrs_crawler(url_naver,'href')
    return url

# 자바스크립트 받아오기위해 어쩔수 없이 셀레늄 가져온다 ㅡㅡ
chrome_options = Options()
chrome_options.page_load_strategy = 'none'
chrome_options.add_argument('headless')
chrome_options.add_argument("disable-gpu")
chrome_options.add_argument("--kiosk")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

#####뉴스크롤링 시작#####

# 검색어 입력
search = input("검색할 키워드를 입력해주세요:")
# 검색 시작할 페이지 입력
page = int(input("\n크롤링할 시작 페이지를 입력해주세요. ex)1(숫자만입력):")) # ex)1 =1페이지,2=2페이지...
print("\n크롤링할 시작 페이지: ",page,"페이지")   
# 검색 종료할 페이지 입력
page2 = int(input("\n크롤링할 종료 페이지를 입력해주세요. ex)1(숫자만입력):")) # ex)1 =1페이지,2=2페이지...
print("\n크롤링할 종료 페이지: ",page2,"페이지")   

# naver url 생성
url = makeUrl(search,page,page2)

#뉴스 크롤러 실행
news_id = []
news_titles = []
news_url =[]
news_contents =[]
news_dates = []
news_types = []
news_img = []
news_like = []

for i in url:
    url = articles_crawler(url)
    news_url.append(url)


#제목, 링크, 내용 1차원 리스트로 꺼내는 함수 생성
def makeList(newlist, content):
    for i in content:
        for j in i:
            newlist.append(j)
    return newlist

    
#제목, 링크, 내용 담을 리스트 생성
news_url_1 = []

#1차원 리스트로 만들기(내용 제외)
makeList(news_url_1,news_url)

#NAVER 뉴스만 남기기
final_urls = []
for i in tqdm(range(len(news_url_1))):
    if "news.naver.com" in news_url_1[i]:
        final_urls.append(news_url_1[i])
    else:
        pass

# 뉴스 중복 제거
final_urls = list(set(final_urls))

# 뉴스 내용 크롤링

for i in tqdm(final_urls):
    # 각 기사 html get하기(beautifulSoup)
    news = requests.get(i,headers=headers)
    news_html = BeautifulSoup(news.text,"html.parser")
    
    # 각 기사 html get하기(Selenium)
    driver.get(i)
    time.sleep(2)
    news2 = driver.page_source
    news2_html = BeautifulSoup(news2, 'html.parser')
    time.sleep(2)
    
    # 뉴스 ID
    if "sports" in i:
        article_id = i[43:46] + "/" + i[52:]
    else:
        article_id = i[39:]
    news_id.append(article_id)


    # 뉴스 제목 가져오기
    title = news_html.select_one("#ct > div.media_end_head.go_trans > div.media_end_head_title > h2")
    if title == None:
        title = news_html.select_one("#content > div.end_ct > div > h2")
        if news_html.select_one("#content > div.end_ct > div > h2") == None:
            title = news_html.select_one("#content > div > div.content > div > div.news_headline > h4")
    
    # 뉴스 본문 가져오기
    content = news_html.select("div#dic_area")
    if content == []:
        content = news_html.select("#articeBody")
        if news_html.select("#articeBody") == []:
            content = news_html.select("#newsEndContents")

    # 기사 텍스트만 가져오기

    # list합치기
    content = ''.join(str(content))

    # html태그제거 및 텍스트 다듬기
    pattern1 = '<[^>]*>'
    title = re.sub(pattern=pattern1, repl='', string=str(title))
    content = re.sub(pattern=pattern1, repl='', string=content)
    pattern2 = """[\n\n\n\n\n// flash 오류를 우회하기 위한 함수 추가\nfunction _flash_removeCallback() {}"""
    content = content.replace(pattern2, '')

    news_titles.append(title)
    news_contents.append(content)
    
    # 뉴스 분야 넣기

    # 일반 기사
    parts = str(news_html.select("div#_LNB.Nlnb_menu_inner > ul.Nlnb_menu_list > li.Nlist_item._LNB_ITEM.is_active > a.Nitem_link > span.Nitem_link_menu")).replace("[","").replace("]","").replace('<span class="Nitem_link_menu">',"").replace("</span>","")
    if parts == "":
        # 연예 기사
        parts = str(news_html.select("div#lnb.lnb_wrap > ul.lnb_lst > li.on > a.lnb_home > em")).replace("[","").replace("]","").replace("<em>","").replace("</em>","").replace("홈", "")
         # 스포츠 기사
        if news_html.select("div#lnb.lnb_wrap > ul.lnb_lst > li.on > a.lnb_home > em") == []:
            parts = "스포츠"
    news_types.append(parts)

    # 날짜 가져오기
    if parts == "스포츠":
        news_date = news2_html.select_one("#content > div > div.content > div > div.news_headline > div > span:nth-child(2)")
        if news_date == None:
            news_date = datetime.now()
            news_date = news_date.strftime("%Y.%m.%d. %p %I:%M")
        else:
            news_date = news2_html.select_one("#content > div > div.content > div > div.news_headline > div > span:nth-child(2)").text.replace("최종수정 ", "")
    else:
        try:
            html_date = news_html.select_one("div#ct> div.media_end_head.go_trans > div.media_end_head_info.nv_notrans > div.media_end_head_info_datestamp > div > span")
            news_date = html_date.attrs['data-date-time']
        except AttributeError:
            html_date = news_html.select_one("#content > div.end_ct > div > div.article_info > span > em")
            news_date = re.sub(pattern=pattern1,repl='',string=str(html_date))


    # 날짜 전처리
    if "-" in str(news_date):
        news_date = news_date.replace("-", ".")
    if "오전" in news_date:
        news_date = news_date.replace("오전", "AM")
    if "오후" in news_date:
        news_date = news_date.replace("오후", "PM")

    if parts == "TV연예" or parts == "스포츠":
        news_date = datetime.strptime(news_date,'%Y.%m.%d. %p %I:%M')
        news_dates.append(news_date)
    else:
        if int(float(news_date[11:13])) >= 12:
            if int(float(news_date[11:13])) == 12:
                news_date = news_date[:10] + "." + " PM " + str(int(news_date[11:13])) + news_date[13:16]
                news_date = datetime.strptime(news_date,'%Y.%m.%d. %p %I:%M')
                news_dates.append(news_date)
            else:
                news_date = news_date[:10] + "." + " PM " + str(int(news_date[11:13])-12) + news_date[13:16]
                news_date = datetime.strptime(news_date,'%Y.%m.%d. %p %I:%M')
                news_dates.append(news_date)
        else:
            if int(float(news_date[11:13])) == 0:
                news_date = news_date[:10] + "." + " AM " + str(12) + news_date[13:16]
                news_date = datetime.strptime(news_date,'%Y.%m.%d. %p %I:%M')
                news_dates.append(news_date)
            else:
                news_date = news_date[:10] + "." + " AM " + str(int(news_date[11:13])) + news_date[13:16]
                news_date = datetime.strptime(news_date,'%Y.%m.%d. %p %I:%M')
                news_dates.append(news_date)


    # 뉴스 공감 수 가져오기(셀레늄)
    if parts == "TV연예":
        likes = str(news2_html.select("#content > div.end_ct > div > div.end_top_util > div:nth-child(1) > div._reactionModule.u_likeit > a > span.u_likeit_text._count.num")).replace('<span class="u_likeit_text _count num">',"").replace("</span>", "").replace("[", "").replace("]", "").replace("'","").replace(",","")
    elif parts == "스포츠":
        likes = str(news2_html.select("#content > div > div.content > div > div.news_work > div.count > div._reactionModule.u_likeit > a > span.u_likeit_text._count.num")).replace('<span class="u_likeit_text _count num">',"").replace("</span>", "").replace("[", "").replace("]", "").replace("'","").replace(",","")
    else:
        likes = str(news2_html.select("#commentFontGroup > div.media_end_head_info_variety_likeit._LIKE_HIDE.as_likeit_improve > div > a > span.u_likeit_text._count.num")).replace('<span class="u_likeit_text _count num">',"").replace("</span>", "").replace("[", "").replace("]", "").replace("'","").replace(",","")
    
    if likes == "":
        news_like.append(int(0))
    else:
        news_like.append(int(likes))

    # 뉴스 이미지 가져오기
    if parts == "스포츠":
        try:
            img = news_html.select_one("span > img")['src']
        except:
            img = news_html.select_one("script")['src']

    elif parts == "TV연예":
        try:
            img = news_html.select_one("#img1")['src']
        except:
            img = news_html.select_one("body > script")['src']
    else:
        if news_html.select_one("#img1"):
            try:
                img = news_html.select_one("#img1")['data-src']
            except:
                img = news_html.select_one("#img1")['src']
        else:
            try:
                img = news_html.select_one('div._VOD_PLAYER_WRAP')['data-cover-image-url']
            except:
                img = ""
    news_img.append(img)

    # 검색시간 더하기
    now = datetime.now()
    search_time = now.strftime("%Y.%m.%d. %p %I:%M")
    search_time = datetime.strptime(search_time, "%Y.%m.%d. %p %I:%M")
    

print("검색된 기사 갯수: 총 ",(page2+1-page)*10,'개')
print("\n[뉴스 제목]")
print(news_titles)
print("\n[뉴스 링크]")
print(final_urls)
print("\n[뉴스 내용]")
print(news_contents)

print('news_id: ', news_id)
print('news_title: ',len(news_titles))
print('news_urls: ',len(final_urls))
print('news_contents: ',len(news_contents))
print('news_dates: ',news_dates)
print('news_types: ', news_types)
print('news_img: ', news_img)
print('news_like: ', news_like)
print('search_time ', search_time)


import pymysql

connection = pymysql.connect(host='localhost', user='root', port = 3306, password = "clftjd4dlek!", db = 'third_project', charset = 'utf8mb4', use_unicode=True, cursorclass=pymysql.cursors.DictCursor)
cur = connection.cursor()

for news_id, news_title, news_url, news_content, news_date, news_type, news_img, news_like in zip(news_id, news_titles, final_urls, news_contents, news_dates, news_types, news_img, news_like):
    
    sql = """INSERT INTO main_page_newsarticle (news_number, news_title, news_url, news_content, news_date, news_type, news_img, news_like, search_time) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
    cur.execute(sql, ('%s'%(news_id), '%s'%(news_title), '%s'%(news_url), '%s'%(news_content), '%s'%(news_date), '%s'%(news_type), '%s'%(news_img), '%s'%(news_like), '%s'%(search_time)))
    connection.commit()

connection.close()


driver.quit()