from django.http import HttpResponse, Http404, HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.views import View
from .forms import ArticleForm, CommentForm
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework import viewsets
from rest_framework import status
from .serializers import ArticleSerializer, CommentSerializer
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
from krwordrank.word import summarize_with_keywords
from .models import Article, Comment
from krwordrank.hangle import normalize
from bs4 import BeautifulSoup
import requests
import re
from datetime import datetime
import json



def index(request):
    news_articles = Article.get_active_article().order_by('-news_like')
    search = request.GET.get('search', '')
    search_type = request.GET.get('search_type', '')
    search_category = request.GET.get('search_category', '')
    keyword = request.GET.get('keyword', '')

    if not search_type:
        search_type = ''

    if '정치' in search_category:
        news_articles = news_articles.filter(Q(news_type__icontains='정치'))
    elif '경제' in search_category:
        news_articles = news_articles.filter(Q(news_type__icontains='경제'))
    elif 'IT/과학' in search_category:
        news_articles = news_articles.filter(Q(news_type__icontains='IT/과학'))
    elif '연예' in search_category:
        news_articles = news_articles.filter(Q(news_type__icontains='연예'))
    elif '스포츠' in search_category:
        news_articles = news_articles.filter(Q(news_type__icontains='스포츠'))
    elif '기타' in search_category:
        news_articles = news_articles.filter(Q(news_type__icontains='사회')|Q(news_type__icontains='생활'))

    if search:
        if len(search) > 1:
            if 'all' in search_type:
                news_articles = news_articles.filter(
                    Q(news_title__contains= search)|
                    Q(news_content__contains=search)
                ).distinct()
            elif 'title' in search_type:
                news_articles = news_articles.filter(Q(news_title__contains=search)).distinct()
            elif 'content' in search_type:
                news_articles = news_articles.filter(Q(news_content__contains=search)).distinct()
        else:
            search = None
            messages.error(request, '검색어는 2글자 이상 입력해주세요.')


    paginator = Paginator(news_articles, 9)
    page = request.GET.get('page', '1')
    posts = paginator.get_page(page)
    
    keyword = request.POST.get('keyword', '')

    return render(request, "main_page/index.html", {'posts': posts, 'search': search, 'search_type': search_type, 'search_category': search_category, 'keyword': keyword,})


def detail_page(request, article_id):
    article = get_object_or_404(Article, pk=article_id)
    comments = Comment.objects.filter(article=article_id).order_by('-comment_like')
    form = CommentForm(initial={'article': article})
    paginator = Paginator(comments, 5)
    page = request.GET.get('page', '1')
    posts = paginator.get_page(page)
    return render(request, "main_page/detail.html", {'article':article, 'form': form, 'posts': posts, 'comments': comments,})


def news_comment(request, article_id):
    article = get_object_or_404(Article, pk=article_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.article = article
            comment.save()

    return redirect(reverse('main_page:detail', args=[article_id]))


def news_create(request):
    form = ArticleForm()
    if request.method == "POST":
        form = ArticleForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(reverse("main_page:index"))
    return render(request, "main_page/create.html", {"form": form})


def news_edit(request, article_id):
    article = get_object_or_404(Article, pk=article_id)
    if request.method == "GET":
        form = ArticleForm(instance=article)
        return render(request, "main_page/edit.html", {"form": form})
    elif request.method == "POST":
        form = ArticleForm(request.POST, instance=article)
        if form.is_valid():
            form.save()
            return redirect(reverse('main_page:detail', args=[article_id]))
        return render(request, "main_page/edit.html", {"form": form})


def news_delete(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    if not article.is_active():
        print(article.is_active())
        raise Http404("게시물이 없습니다.")

    article.delete()
    return redirect(reverse("main_page:index"))

class ArticleListAPI(APIView):
    def get(self, request):
        queryset = Article.objects.prefetch_related('comment_set').all()
        serializer = ArticleSerializer(queryset, many=True)
        return Response(serializer.data)
    def post(self, request):
        serializer = ArticleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ArticleDetailAPI(APIView):
    def get_object(self, article_id):
        queryset = Article.objects.filter(id=article_id)
        return queryset

    def get(self, request, article_id):
        qs = self.get_object(article_id)
        serializer = ArticleSerializer(qs, many=True)
        return Response(serializer.data)

    def put(self, request, article_id):
        qs = self.get_object(article_id)
        serializer = ArticleSerializer(qs, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, article_id):
        qs = self.get_object(article_id)
        qs.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class CommentListAPI(APIView):
    def get(self, request):
        queryset = Comment.objects.all()
        serializer = CommentSerializer(queryset, many=True)
        return Response(serializer.data)
    def post(self, request):
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CommentDetailAPI(APIView):
    def get_object(self, article_id):
        queryset = Comment.objects.filter(id=article_id)
        return queryset

    def get(self, request, article_id):
        qs = self.get_object(article_id)
        serializer = CommentSerializer(qs, many=True)
        return Response(serializer.data)

    def put(self, request, article_id):
        qs = self.get_object(article_id)
        serializer = CommentSerializer(qs, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, article_id):
        qs = self.get_object(article_id)
        qs.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
def article_wordcloud(request):
    articles = Article.get_active_article()
    texts = [normalize(article.news_title, english=True, number=False) for article in articles]
    s_file_name = open('.\StopWordKorean.txt','r')
    stopwords = []
    for line in s_file_name.readlines():
        stopwords.append(line.strip())
    stopwords.extend(['포토','영상','다시','엔하이픈','글로','나는','환승연','제이'])
    keywords = summarize_with_keywords(texts, min_count=3, max_length=10,
                                       beta=0.85, max_iter=10, verbose=True, stopwords=stopwords)
    wordlist = []
    count = 0
    for key, val in keywords.items():
        temp = {'text': key, 'weight': int(val*100)}
        wordlist.append(temp)
        count += 1
        if count >= 150:
            break
    
    wordlist = list({data['text']:data for data in wordlist}.values())

    return Response(wordlist)


# 프론트도 안돼 api에서도 안돼 나는 어쩌란 말이냐
@api_view(['GET','POST'])
def news_crawling(request):
    keyword  = request.GET.get('q', '')
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"}
    url = "https://search.naver.com/search.naver?where=news&sm=tab_pge&query=" + keyword + "&start=11"

    original_html = requests.get(url,headers=headers)
    html = BeautifulSoup(original_html.text, "html.parser")

    url_naver = html.select("div.news_info > div.info_group > a.info")

    content =[]

    for i in url_naver:
        content.append(i['href'])

    news_url = []

    for i in range(len(content)):
        if "news.naver.com" in content[i]:
            news_url.append(content[i])
        else:
            pass
    
    article_list = []        

    for i in news_url:
        news = requests.get(i,headers=headers)
        news_html = BeautifulSoup(news.text,"html.parser")


        if "sports" in i:
            news_number = i[43:46] + "/" + i[52:]
        else:
            news_number = i[39:]


        news_title = news_html.select_one("#ct > div.media_end_head.go_trans > div.media_end_head_title > h2")
        if news_title == None:
            news_title = news_html.select_one("#content > div.end_ct > div > h2")
            if news_html.select_one("#content > div.end_ct > div > h2") == None:
                news_title = news_html.select_one("#content > div > div.content > div > div.news_headline > h4")
        

        news_content = news_html.select("div#dic_area")
        if news_content == []:
            news_content = news_html.select("#articeBody")
            if news_html.select("#articeBody") == []:
                news_content = news_html.select("#newsEndContents")


        news_content = ''.join(str(news_content))

        pattern1 = '<[^>]*>'
        news_title = re.sub(pattern=pattern1, repl='', string=str(news_title)).replace("[","").replace("]","").strip()
        news_content = re.sub(pattern=pattern1, repl='', string=news_content)
        news_content = news_content.replace("[","").replace("]","").replace("/n","").replace("/t","").strip()
        pattern2 = """[\n\n\n\n\n// flash 오류를 우회하기 위한 함수 추가\nfunction _flash_removeCallback() {}"""
        news_content = news_content.replace(pattern2, '').replace("/n","").replace("/t","").strip()

        news_type = str(news_html.select("div#_LNB.Nlnb_menu_inner > ul.Nlnb_menu_list > li.Nlist_item._LNB_ITEM.is_active > a.Nitem_link > span.Nitem_link_menu")).replace("[","").replace("]","").replace('<span class="Nitem_link_menu">',"").replace("</span>","")
        if news_type == "":
            news_type = str(news_html.select("div#lnb.lnb_wrap > ul.lnb_lst > li.on > a.lnb_home > em")).replace("[","").replace("]","").replace("<em>","").replace("</em>","").replace("홈", "")
            if news_html.select("div#lnb.lnb_wrap > ul.lnb_lst > li.on > a.lnb_home > em") == []:
                news_type = "스포츠"

        if news_type == "스포츠":
            news_date = news_html.select_one("#content > div > div.content > div > div.news_headline > div > span:nth-child(2)")
            if news_date == None:
                news_date = datetime.now()
                news_date = news_date.strftime("%Y.%m.%d. %p %I:%M")
            else:
                news_date = news_html.select_one("#content > div > div.content > div > div.news_headline > div > span:nth-child(2)").text.replace("최종수정 ", "")
        else:
            try:
                html_date = news_html.select_one("div#ct> div.media_end_head.go_trans > div.media_end_head_info.nv_notrans > div.media_end_head_info_datestamp > div > span")
                news_date = html_date.attrs['data-date-time']
            except AttributeError:
                html_date = news_html.select_one("#content > div.end_ct > div > div.article_info > span > em")
                news_date = re.sub(pattern=pattern1,repl='',string=str(html_date))

        if "-" in str(news_date):
            news_date = news_date.replace("-", ".")
        if "오전" in news_date:
            news_date = news_date.replace("오전", "AM")
        if "오후" in news_date:
            news_date = news_date.replace("오후", "PM")

        if news_type == "TV연예" or news_type == "스포츠":
            news_date = datetime.strptime(news_date,'%Y.%m.%d. %p %I:%M')
        else:
            if int(float(news_date[11:13])) >= 12:
                if int(float(news_date[11:13])) == 12:
                    news_date = news_date[:10] + "." + " PM " + str(int(news_date[11:13])) + news_date[13:16]
                    news_date = datetime.strptime(news_date,'%Y.%m.%d. %p %I:%M')
                else:
                    news_date = news_date[:10] + "." + " PM " + str(int(news_date[11:13])-12) + news_date[13:16]
                    news_date = datetime.strptime(news_date,'%Y.%m.%d. %p %I:%M')
            else:
                if int(float(news_date[11:13])) == 0:
                    news_date = news_date[:10] + "." + " AM " + str(12) + news_date[13:16]
                    news_date = datetime.strptime(news_date,'%Y.%m.%d. %p %I:%M')

                else:
                    news_date = news_date[:10] + "." + " AM " + str(int(news_date[11:13])) + news_date[13:16]
                    news_date = datetime.strptime(news_date,'%Y.%m.%d. %p %I:%M')

        if news_type == "스포츠":
            try:
                news_img = news_html.select_one("span > img")['src']
            except:
                news_img = news_html.select_one("script")['src']

        elif news_type == "TV연예":
            try:
                news_img = news_html.select_one("#img1")['src']
            except:
                news_img = news_html.select_one("body > script")['src']
        else:
            if news_html.select_one("#img1"):
                try:
                    news_img = news_html.select_one("#img1")['data-src']
                except:
                    news_img = news_html.select_one("#img1")['src']
            else:
                try:
                    news_img = news_html.select_one('div._VOD_PLAYER_WRAP')['data-cover-image-url']
                except:
                    news_img = ""
        

        temp = {'news_number':news_number,
            'news_title':news_title,
            'news_url':i,
            'news_content':news_content,
            'news_date':news_date,
            'news_type':news_type,
            'news_img':news_img,
            'news_like':0}

        Article(news_number=news_number,
        news_title=news_title,
        news_url=i,
        news_content=news_content,
        news_date=news_date,
        news_type=news_type,
        news_img=news_img,
        news_like=10).save()

        article_list.append(temp)
    
    return Response(article_list)

