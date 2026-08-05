"""luntan URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('appone.urls.index')),
    path('', include('user.urls.index')),
    #20251027添加
    path('', include('blog.urls.index')),
    path('', include('survey.urls.index')),
    path('', include('godot.urls.index')),
    path('', include('task.urls.index'))
]

# deepseek增加的圖片本地服務
# 開發環境：提供媒體文件服務 

from django.conf import settings  # 添加這行！
from django.conf.urls.static import static  # 必須導入static！
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
