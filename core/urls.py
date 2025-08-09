from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # --- Các URL xác thực và trang chung ---
    path('', views.homepage, name='homepage'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login_view'),
    path('logout/', views.logout_view, name='logout_view'),
    path('profile/', views.profile_view, name='profile_view'),
    path('about/', views.about_view, name='about_view'),
    
    # --- URL cho trang Chat ---
    path('chat/', views.chat_view, name='chat_view'),
    path('api/chat/', views.api_chat, name='api_chat'),
    path('api/chat/delete/', views.delete_chat_history, name='delete_chat_history'),
    
    # --- URL cho trang TikTok Analyzer ---
    path('tiktok-analyzer/', views.tiktok_analyzer_view, name='tiktok_analyzer_view'),
    
    # --- API cho quy trình phân tích bất đồng bộ ---
    path('api/tiktok-analyzer/submit/', views.api_tiktok_submit_url, name='api_tiktok_submit_url'),
    path('api/tiktok-analyzer/status/', views.api_tiktok_check_status, name='api_tiktok_check_status'),
    
    # --- API để xóa lịch sử TikTok ---
    path('api/tiktok-history/delete/', views.api_delete_tiktok_history, name='api_delete_tiktok_history'),

    # --- URL cho chức năng Location Tracker ---
    path('location-tracker/', views.location_tracker_dashboard, name='location_tracker_dashboard'),
    path('t/<str:tracking_id>/', views.track_and_redirect, name='track_and_redirect'),
    path('api/log-location/', views.save_location, name='save_location'),
    path('api/location-tracker/data/', views.api_get_tracker_data, name='api_get_tracker_data'),
    path('api/location-tracker/delete/<int:pk>/', views.api_delete_tracking_link, name='api_delete_tracking_link'),
]
