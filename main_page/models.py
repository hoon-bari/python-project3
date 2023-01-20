from django.db import models
from django.utils import timezone


class Article(models.Model):
    news_number = models.CharField(max_length=100, blank=True, null=True)
    news_title = models.CharField(max_length=512, blank=True, null=True)
    news_url = models.CharField(max_length=512, blank=True, null=True)
    news_content = models.TextField(blank=True, null=True)
    news_date = models.DateTimeField(default=timezone.now)
    news_type = models.CharField(max_length=50, blank=True, null=True)
    news_img = models.TextField(blank=True, null=True)
    news_like = models.CharField(max_length=50, blank=True, null=True)
    search_time = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    @classmethod
    def get_active_article(cls):
        return cls.objects.filter(deleted_at__isnull=True)
    def delete(self):
        self.deleted_at = timezone.now()
        return self.save()
    def is_active(self):
        print(bool(self.deleted_at))
        return not bool(self.deleted_at)
    @classmethod
    def active_list(cls):
        return cls.objects.filter(deleted_at__isnull=True)

    class Meta:
        managed = False
        db_table = 'main_page_newsarticle'


class Comment(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, blank=True, null=True)
    news_number = models.CharField(max_length=100, blank=True, null=True)
    username = models.CharField(max_length=100, blank=True, null=True)
    comment_content = models.TextField(blank=True, null=True)
    comment_like = models.IntegerField(default=0)
    comment_dislike = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = 'main_page_newscomment'