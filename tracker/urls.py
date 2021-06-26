from django.contrib import admin
from django.conf import settings
from django.urls import include, path
from django.conf.urls.static import static

from main.views import ChangeLanguageView, Index

urlpatterns = [
    path('main/', include('main.urls')),
    path('accounts/', include('accounts.urls')),
    path('admin/', admin.site.urls),
    path('language/', ChangeLanguageView.as_view(), name='change_language'),
    path('', Index.as_view(), name='index'),
    path('tinymce/', include('tinymce.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
