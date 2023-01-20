from django.urls import path
from main_page import views


urlpatterns = [
    path('article', views.ArticleListAPI.as_view()),
    path('article/<int:article_id>', views.ArticleDetailAPI.as_view()),
    path('comment', views.CommentListAPI.as_view()),
    path('comment/<int:article_id>', views.CommentDetailAPI.as_view()),
    path("wordcloud", views.article_wordcloud),
    path("crawling", views.news_crawling)
]