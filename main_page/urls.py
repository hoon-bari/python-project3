from django.urls import path
from . import views


app_name = "main_page"


urlpatterns = [
    path("", views.index, name='index'),
    path("create", views.news_create, name='create'),
    path("<int:article_id>", views.detail_page, name='detail'),
    path("<int:article_id>/comments", views.news_comment, name="comment"),
    path("<int:article_id>/edit", views.news_edit, name='edit'),
    path("<int:article_id>/delete", views.news_delete, name='delete'),
]