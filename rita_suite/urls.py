"""
URL configuration for rita_suite project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # SỬA LỖI: Sử dụng include để trỏ đến tệp urls.py của ứng dụng 'core'
    # Tất cả các URL sẽ được xử lý bởi ứng dụng 'core'
    path('', include('core.urls')),
]

# Cấu hình để phục vụ các file media trong môi trường development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

