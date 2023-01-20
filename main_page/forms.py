from django import forms
from .models import Article, Comment

class ArticleForm(forms.ModelForm):

   def __init__(self, *args, **kwargs):
       super().__init__(*args, **kwargs)
       self._widget_update()

   def _widget_update(self):
       for visible in self.visible_fields():
           visible.field.widget.attrs['class'] = 'form-control'

   class Meta:
       model = Article
       fields = ["news_title", "news_type", "news_img", "news_content"]
       widgets = {
           'news_title': forms.Textarea(attrs={
               'class': 'form-control',
               'placeholder': '제목을 수정해주세요',
               'rows': 1
           }),
            'news_img': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'img 주소를 수정해주세요.',
                'rows': 3
             }),
           'news_content': forms.Textarea(attrs={
               'class': 'form-control',
               'placeholder': '내용을 수정해주세요.',
               'rows': 10
           }),
       }

class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ['username', 'comment_content', 'article']
