from django.db import models
from django.contrib.auth.models import User

class Client(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    username = models.CharField(max_length=32, unique=True, verbose_name='用户名')
    phone_number = models.CharField(max_length=16, null=True, blank=True, verbose_name='手机号')
    email = models.CharField(max_length=32, null=True, blank=True, verbose_name='用户邮箱')
    
    # 新增注册序列号字段
    registration_code = models.CharField(
        max_length=50, 
        unique=True, 
        null=True, 
        blank=True, 
        verbose_name='注册序列号'
    )
    code_used_at = models.DateTimeField(null=True, blank=True, verbose_name='序列号使用时间')
    
    province = models.CharField(max_length=100, blank=True, null=True)
    user_status = models.BooleanField(default=True, verbose_name='是否启用')
    gender_choice = (
        (0, '保密'),
        (1, '男'),
        (2, '女'),
    )
    gender = models.SmallIntegerField(null=True, blank=True, choices=gender_choice, default=0, verbose_name='性别')
    open_id = models.CharField(max_length=128, null=True, blank=True, verbose_name='openId')
    avatar = models.URLField(max_length=256, null=True, blank=True, verbose_name='头像')
    admire = models.CharField(max_length=32, null=True, blank=True, verbose_name='赞赏')
    introduction = models.CharField(max_length=4096, null=True, blank=True, verbose_name='简介')
    user_type_choice = (
        (0, 'Boss'),
        (1, '管理员'),
        (2, '普通用户'),
        (3, '访客'),
    )
    user_type = models.SmallIntegerField(choices=user_type_choice, default=2, verbose_name='用户类型')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='最终修改时间')
    update_by = models.CharField(max_length=32, null=True, blank=True, verbose_name='最终修改人')
    deleted = models.BooleanField(default=False, verbose_name='是否删除')
    qiniu_domain = models.CharField(max_length=128, null=True, blank=True, verbose_name='七牛云域名')
    qiniu_bucket_name = models.CharField(max_length=128, null=True, blank=True, verbose_name='七牛云bucket')
    qiniu_secret_key = models.CharField(max_length=128, null=True, blank=True, verbose_name='七牛云secret_key')
    qiniu_access_key = models.CharField(max_length=128, null=True, blank=True, verbose_name='七牛云access_key')
    
    class Meta:
        db_table = 'user'
        verbose_name = '用户信息表'
        verbose_name_plural = verbose_name

    def __str__(self):
        return str(self.user_id) + '-' + str(self.username)


    @property
    def user_id(self):
        return self.user.id if self.user else None
    
    def get_user_type_display_with_color(self):
        colors = {
            0: '#ff4444',  # Boss - 紅色
            1: '#ff8800',  # 管理員 - 橙色  
            2: '#00C851',  # 普通用戶 - 綠色
            3: '#aaaaaa',  # 訪客 - 灰色
        }
        color = colors.get(self.user_type, '#000000')
        return f'<span style="color: {color}; font-weight: bold;">{self.get_user_type_display()}</span>'
    
    def is_active_user(self):
        return self.user_status and not self.deleted









