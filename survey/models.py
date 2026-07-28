from django.db import models
from django.contrib.auth.models import User
from django.core.serializers.json import DjangoJSONEncoder
import json
from django.urls import reverse

class Survey(models.Model):
    SURVEY_STATUS = (
        ('draft', '草稿'),
        ('active', '进行中'),
        ('closed', '已结束'),
    )
    
    title = models.CharField(max_length=200, verbose_name="问卷标题")
    description = models.TextField(verbose_name="问卷描述", blank=True)
    questions = models.JSONField(verbose_name="问题配置", encoder=DjangoJSONEncoder)
    status = models.CharField(max_length=10, choices=SURVEY_STATUS, default='draft', verbose_name="状态")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="创建者")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    start_date = models.DateTimeField(null=True, blank=True, verbose_name="开始时间")
    end_date = models.DateTimeField(null=True, blank=True, verbose_name="结束时间")
    
    # 新增字段
    has_answer_file = models.BooleanField(default=False, verbose_name="是否有答案文件")
    answer_data = models.JSONField(verbose_name="答案数据", null=True, blank=True, encoder=DjangoJSONEncoder)
    
    class Meta:
        verbose_name = "调查问卷"
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    @property
    def is_active(self):
        from django.utils import timezone
        if self.status != 'active':
            return False
        if self.start_date and timezone.now() < self.start_date:
            return False
        if self.end_date and timezone.now() > self.end_date:
            return False
        return True

    def display_survey_id(self):
        """在admin中显示为问卷ID"""
        if self.id is None:
            return "新问卷"
        return f"问卷-{self.id:04d}"
    display_survey_id.short_description = '问卷ID'

    def get_absolute_url(self):
        if self.id:
            return reverse('admin:survey_survey_change', args=[str(self.id)])
        return reverse('admin:survey_survey_changelist')








import uuid
from django.db import models

class SurveyResponse(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, verbose_name="问卷", related_name='responses')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户", null=True, blank=True)
    user_ip = models.GenericIPAddressField(verbose_name="用户IP", null=True, blank=True)
    user_agent = models.TextField(verbose_name="用户代理", blank=True)
    answers = models.JSONField(verbose_name="回答数据", encoder=DjangoJSONEncoder)
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name="提交时间")
    is_anonymous = models.BooleanField(default=False, verbose_name="匿名提交")
    
    # 新增评分字段
    ai_score = models.FloatField(null=True, blank=True, verbose_name="AI评分")
    ai_comment = models.TextField(blank=True, verbose_name="AI评语")
    ai_evaluated_at = models.DateTimeField(null=True, blank=True, verbose_name="AI评估时间")
    
    # 新增序列号字段
    registration_code = models.CharField(
        max_length=50, 
        unique=True, 
        null=True, 
        blank=True, 
        verbose_name="注册序列号"
    )
    code_generated_at = models.DateTimeField(null=True, blank=True, verbose_name="序列号生成时间")
    code_used = models.BooleanField(default=False, verbose_name="序列号是否已使用")
    used_by_user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='used_registration_codes',
        verbose_name="使用用户"
    )
    used_at = models.DateTimeField(null=True, blank=True, verbose_name="使用时间")
    
    class Meta:
        verbose_name = "问卷回答"
        verbose_name_plural = verbose_name
        ordering = ['-submitted_at']
        unique_together = ['survey', 'user']  # 同一用户只能提交一次
    
    def __str__(self):
        return f"{self.survey.title} - {self.user.username if self.user else '匿名用户'}"
    
    def display_response_id(self):
        """在admin中显示为回答ID"""
        if self.id is None:
            return "新回答"
        return f"回答-{self.id:04d}"
    display_response_id.short_description = '回答ID'
    
    def generate_registration_code(self):
        """生成唯一的注册序列号"""
        # 使用UUID + 时间戳 + 随机数创建唯一序列号
        import time
        import random
        
        timestamp = int(time.time() * 1000)
        random_suffix = random.randint(1000, 9999)
        base_uuid = uuid.uuid4().hex[:12].upper()
        
        # 格式: SURVEY-时间戳-随机数-UUID部分
        code = f"SURVEY-{timestamp}-{random_suffix}-{base_uuid}"
        
        # 确保唯一性
        while SurveyResponse.objects.filter(registration_code=code).exists():
            timestamp = int(time.time() * 1000)
            random_suffix = random.randint(1000, 9999)
            base_uuid = uuid.uuid4().hex[:12].upper()
            code = f"SURVEY-{timestamp}-{random_suffix}-{base_uuid}"
        
        return code

















class SurveyAnswerAnalysis(models.Model):
    survey = models.OneToOneField(Survey, on_delete=models.CASCADE, verbose_name="问卷", related_name='analysis')
    total_responses = models.IntegerField(default=0, verbose_name="总回答数")
    answer_statistics = models.JSONField(verbose_name="回答统计", default=dict, encoder=DjangoJSONEncoder)
    last_updated = models.DateTimeField(auto_now=True, verbose_name="最后更新")
    
    class Meta:
        verbose_name = "问卷分析"
        verbose_name_plural = verbose_name
    
    def __str__(self):
        return f"{self.survey.title} - 分析数据"
    
    def display_analysis_id(self):
        """在admin中显示为分析ID"""
        if self.id is None:
            return "新分析"
        return f"分析-{self.id:04d}"
    display_analysis_id.short_description = '分析ID'