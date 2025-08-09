import uuid
from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', default='avatars/default.png', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'{self.user.username} Profile'

class ChatHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} - {self.role}: {self.content[:50]}'

class TikTokVideo(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Đang chờ'),
        ('PROCESSING', 'Đang xử lý'),
        ('COMPLETE', 'Hoàn thành'),
        ('FAILED', 'Thất bại'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    video_id = models.CharField(max_length=255, unique=True)
    video_url = models.URLField(max_length=1024)
    author = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    cover_url = models.URLField(max_length=1024, blank=True, null=True)
    download_url = models.URLField(max_length=1024, blank=True, null=True)
    play_count = models.PositiveIntegerField(default=0)
    likes = models.PositiveIntegerField(default=0)
    comments = models.PositiveIntegerField(default=0)
    shares = models.PositiveIntegerField(default=0)
    transcript = models.TextField(blank=True, null=True)
    analysis = models.JSONField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.author} - {self.description[:50]}'

# --- MODEL MỚI CHO CHỨC NĂNG THEO DÕI VỊ TRÍ ---

class TrackingLink(models.Model):
    """Lưu link gốc và link theo dõi, liên kết với người dùng đã tạo ra nó."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Người tạo")
    original_url = models.URLField(max_length=2000, verbose_name="URL Gốc")
    tracking_id = models.CharField(max_length=15, unique=True, blank=True, verbose_name="ID Theo dõi")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    
    # --- ĐÃ THÊM TRƯỜNG MỚI ---
    # Trường này sẽ lưu trạng thái `True` nếu người dùng bật tùy chọn "Bắt buộc"
    require_consent = models.BooleanField(default=False, verbose_name="Bắt buộc cấp quyền")

    def save(self, *args, **kwargs):
        if not self.tracking_id:
            self.tracking_id = str(uuid.uuid4())[:8]
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tracking_id} -> {self.original_url[:70]}..."

    class Meta:
        verbose_name = "Link Theo dõi"
        verbose_name_plural = "Các Link Theo dõi"

class LocationLog(models.Model):
    """Lưu các vị trí đã được ghi nhận cho mỗi link."""
    tracking_link = models.ForeignKey(TrackingLink, on_delete=models.CASCADE, related_name='logs', verbose_name="Link Theo dõi")
    latitude = models.FloatField(verbose_name="Vĩ độ")
    longitude = models.FloatField(verbose_name="Kinh độ")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Dấu thời gian")

    def __str__(self):
        return f"Log for {self.tracking_link.tracking_id} at ({self.latitude}, {self.longitude})"

    class Meta:
        verbose_name = "Nhật ký Vị trí"
        verbose_name_plural = "Các Nhật ký Vị trí"
