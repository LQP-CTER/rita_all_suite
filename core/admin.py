# File: Rita_All_Django/core/admin.py
from django.contrib import admin
from .models import (
    Profile,
    ChatHistory,
    TikTokVideo,
    TrackingLink,
    LocationLog,
    ScrapeResult
)

# Register your models here to make them accessible in the Django admin site.

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name')
    search_fields = ('user__username', 'full_name')

@admin.register(ChatHistory)
class ChatHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'content_preview', 'timestamp')
    list_filter = ('user', 'role', 'timestamp')
    search_fields = ('content',)

    def content_preview(self, obj):
        return (obj.content[:75] + '...') if len(obj.content) > 75 else obj.content
    content_preview.short_description = 'Content'

@admin.register(TikTokVideo)
class TikTokVideoAdmin(admin.ModelAdmin):
    list_display = ('user', 'author', 'description_preview', 'status', 'created_at')
    list_filter = ('status', 'user', 'author')
    search_fields = ('video_url', 'description', 'author')

    def description_preview(self, obj):
        return (obj.description[:75] + '...') if obj.description and len(obj.description) > 75 else obj.description
    description_preview.short_description = 'Description'

@admin.register(TrackingLink)
class TrackingLinkAdmin(admin.ModelAdmin):
    list_display = ('user', 'original_url', 'tracking_id', 'created_at', 'require_consent')
    list_filter = ('user', 'require_consent')
    search_fields = ('original_url', 'tracking_id')

@admin.register(LocationLog)
class LocationLogAdmin(admin.ModelAdmin):
    list_display = ('tracking_link_info', 'latitude', 'longitude', 'timestamp')
    list_filter = ('timestamp',)
    
    def tracking_link_info(self, obj):
        return obj.tracking_link.tracking_id
    tracking_link_info.short_description = 'Tracking ID'

@admin.register(ScrapeResult)
class ScrapeResultAdmin(admin.ModelAdmin):
    list_display = ('user', 'url', 'status', 'created_at', 'completed_at')
    list_filter = ('status', 'user')
    search_fields = ('url',)