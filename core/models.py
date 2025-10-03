# File: Rita_All_Django/core/models.py
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# --- User Profile ---
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255, blank=True, default='')
    date_of_birth = models.DateField(null=True, blank=True)
    bio = models.TextField(blank=True, default='')
    avatar = models.ImageField(upload_to='avatars/', default='avatars/default.jpg')

    def __str__(self):
        return self.user.username

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()

# --- Chat History ---
class ChatHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ROLE_CHOICES = [('user', 'User'), ('model', 'Model')]
    role = models.CharField(max_length=5, choices=ROLE_CHOICES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']
        verbose_name = "Chat History"
        verbose_name_plural = "Chat Histories"

    def __str__(self):
        return f'{self.user.username} ({self.role}): {self.content[:50]}'

# --- TikTok Video Analysis ---
class TikTokVideo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tiktok_videos')
    video_id = models.CharField(max_length=255, unique=True)
    video_url = models.URLField(max_length=1024)
    author = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    cover_url = models.URLField(max_length=1024, blank=True, null=True)
    download_url = models.URLField(max_length=1024, blank=True, null=True)
    
    # Video Stats
    play_count = models.PositiveIntegerField(default=0)
    likes = models.PositiveIntegerField(default=0)
    comments = models.PositiveIntegerField(default=0)
    shares = models.PositiveIntegerField(default=0)
    duration = models.PositiveIntegerField(default=0)
    
    transcript = models.TextField(blank=True, null=True)
    analysis = models.JSONField(blank=True, null=True)
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETE', 'Complete'),
        ('FAILED', 'Failed'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "TikTok Video"
        verbose_name_plural = "TikTok Videos"

    def __str__(self):
        return f"@{self.author}: {self.description[:50]}..."

# --- Location Tracker ---
class TrackingLink(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    original_url = models.URLField(max_length=2048)
    tracking_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    require_consent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Tracking Link"
        verbose_name_plural = "Tracking Links"

    def __str__(self):
        return f"{self.original_url} -> /t/{self.tracking_id}/"

class LocationLog(models.Model):
    tracking_link = models.ForeignKey(TrackingLink, on_delete=models.CASCADE, related_name='logs')
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Location Log"
        verbose_name_plural = "Location Logs"
        
    def __str__(self):
        return f"Log for {self.tracking_link.tracking_id} at {self.timestamp}"

# --- Web Scraper ---
class ScrapeResult(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETE', 'Complete'),
        ('FAILED', 'Failed'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    url = models.URLField(max_length=2048)
    fields = models.CharField(max_length=1024)
    model = models.CharField(max_length=100)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    json_result = models.FileField(upload_to='scrape_results/json/', null=True, blank=True)
    csv_result = models.FileField(upload_to='scrape_results/csv/', null=True, blank=True)

    input_tokens = models.IntegerField(null=True, blank=True)
    output_tokens = models.IntegerField(null=True, blank=True)
    total_cost = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    
    error_message = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Scrape task for {self.url} ({self.status})"

    class Meta:
        ordering = ['-created_at']