# File: Rita_All_Django/core/urls.py
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # --- Authentication and General Pages ---
    path('', views.homepage, name='homepage'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login_view'),
    path('logout/', views.logout_view, name='logout_view'),
    path('profile/', views.profile_view, name='profile_view'),
    path('about/', views.about_view, name='about_view'),
    
    # --- Chat Feature ---
    path('chat/', views.chat_view, name='chat_view'),
    path('api/chat/', views.api_chat, name='api_chat'),
    path('api/chat/refresh/', views.api_refresh_chat, name='api_refresh_chat'),
    
    # --- TikTok Analyzer ---
    path('tiktok-analyzer/', views.tiktok_analyzer_view, name='tiktok_analyzer_view'),
    path('api/tiktok-analyzer/submit/', views.api_tiktok_submit_url, name='api_tiktok_submit_url'),
    path('api/tiktok-analyzer/status/', views.api_tiktok_check_status, name='api_tiktok_check_status'),
    path('api/tiktok-history/delete/', views.api_delete_tiktok_history, name='api_delete_tiktok_history'),

    # --- Location Tracker ---
    path('location-tracker/', views.location_tracker_dashboard, name='location_tracker_dashboard'),
    path('t/<uuid:tracking_id>/', views.track_and_redirect, name='track_and_redirect'),
    path('api/log-location/', views.save_location, name='save_location'),
    path('api/location-tracker/data/', views.api_get_tracker_data, name='api_get_tracker_data'),
    path('api/location-tracker/delete/<int:pk>/', views.api_delete_tracking_link, name='api_delete_tracking_link'),

    # --- Web Scraper ---
    path('web-scraper/', views.web_scraper_view, name='web_scraper_view'),
    path('api/web-scraper/start/', views.api_start_scraping, name='api_start_scrape'),
    path('api/web-scraper/status/<int:task_id>/', views.api_check_scrape_status, name='api_check_scrape_status'),
    path('api/web-scraper/history/', views.api_get_scrape_history, name='api_get_scrape_history'),
    path('api/web-scraper/history/delete/', views.api_delete_scrape_history, name='api_delete_scrape_history'),
    path('download/scrape/<int:task_id>/<str:file_type>/', views.download_scrape_result, name='download_scrape_result'),
]