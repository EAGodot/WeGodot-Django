# models/image.py
from django.db import models
from django.conf import settings
import os
import uuid

def user_image_upload_path(instance, filename):
    """生成用戶圖片上傳路徑"""
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'
    return f'user_images/{instance.user.id}/{filename}'

class UserImage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    image = models.ImageField(upload_to=user_image_upload_path)
    original_filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()
    mime_type = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_images'
    
    def __str__(self):
        return f"{self.user.username} - {self.original_filename}"




        