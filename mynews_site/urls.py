from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("main_page/", include('main_page.urls')),
    path("api-auth/", include('rest_framework.urls')),
    path("api/", include('main_page.api-urls'))
]
