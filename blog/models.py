from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinLengthValidator
from django.urls import reverse

class Blog(models.Model):
    VISIBILITY_CHOICES = [
        ('public', '公开'),
        ('private', '私密'),
    ]
    
    CATEGORY_CHOICES = [
        ('technology', '技术'),
        ('life', '生活'),
        ('design', '设计'),
        ('other', '其他'),
    ]
    
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('published', '已发布'),
        ('archived', '已归档'),
    ]
    
    title = models.CharField(max_length=100, verbose_name='标题', validators=[MinLengthValidator(1)])
    summary = models.TextField(max_length=200, blank=True, verbose_name='摘要')
    content = models.TextField(verbose_name='内容', validators=[MinLengthValidator(10)])
    tags = models.JSONField(default=list, verbose_name='标签')
    category = models.CharField(
        max_length=20, 
        choices=CATEGORY_CHOICES, 
        default='technology',
        verbose_name='分类'
    )
    visibility = models.CharField(
        max_length=10,
        choices=VISIBILITY_CHOICES,
        default='public',
        verbose_name='可见性'
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='状态'
    )
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='作者', related_name='blogs')
    cover_image = models.ImageField(upload_to='blog_covers/', null=True, blank=True, verbose_name='封面图片')
    view_count = models.PositiveIntegerField(default=0, verbose_name='浏览数')
    like_count = models.PositiveIntegerField(default=0, verbose_name='点赞数')
    comment_count = models.PositiveIntegerField(default=0, verbose_name='评论数')
    is_featured = models.BooleanField(default=False, verbose_name='是否推荐')
    is_draft = models.BooleanField(default=True, verbose_name='是否为草稿')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    published_at = models.DateTimeField(null=True, blank=True, verbose_name='发布时间')
    
    class Meta:
        verbose_name = '博客'
        verbose_name_plural = '博客'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'published_at']),
            models.Index(fields=['author', 'created_at']),
            models.Index(fields=['category']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):

        print(f"🔍 Blog模型保存 - ID: {self.id}, 状态: {self.status}, 发布时间: {self.published_at}")
       



        # 自动设置发布时间
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
            self.is_draft = False
        elif self.status == 'draft':
            self.is_draft = True
        
        # 确保已发布的博客必须是公开的
        if self.status == 'published' and self.visibility == 'private':
            self.visibility = 'public'
            
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('blog_detail', kwargs={'pk': self.pk})
    
    def increment_view_count(self):
        """增加浏览数"""
        self.view_count += 1
        self.save(update_fields=['view_count'])
    
    @property
    def reading_time(self):
        """估算阅读时间（按每分钟200字计算）"""
        word_count = len(self.content.strip())
        return max(1, round(word_count / 200))

class BlogLike(models.Model):
    """博客点赞模型"""
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, related_name='likes', verbose_name='博客')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='点赞时间')
    
    class Meta:
        verbose_name = '博客点赞'
        verbose_name_plural = '博客点赞'
        unique_together = ['blog', 'user']  # 防止重复点赞
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} 点赞了 {self.blog.title}"

class BlogComment(models.Model):
    """博客评论模型"""
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, related_name='comments', verbose_name='博客')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='replies',
        verbose_name='父评论'
    )
    content = models.TextField(max_length=1000, verbose_name='评论内容', validators=[MinLengthValidator(1)])
    like_count = models.PositiveIntegerField(default=0, verbose_name='点赞数')
    is_approved = models.BooleanField(default=True, verbose_name='是否审核通过')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '博客评论'
        verbose_name_plural = '博客评论'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['blog', 'created_at']),
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} 评论了 {self.blog.title}"
    
    @property
    def is_reply(self):
        """判断是否是回复评论"""
        return self.parent is not None

class CommentLike(models.Model):
    """评论点赞模型"""
    comment = models.ForeignKey(BlogComment, on_delete=models.CASCADE, related_name='likes', verbose_name='评论')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='点赞时间')
    
    class Meta:
        verbose_name = '评论点赞'
        verbose_name_plural = '评论点赞'
        unique_together = ['comment', 'user']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} 点赞了评论"

class BlogCollection(models.Model):
    """博客收藏模型"""
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, related_name='collections', verbose_name='博客')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='收藏时间')
    
    class Meta:
        verbose_name = '博客收藏'
        verbose_name_plural = '博客收藏'
        unique_together = ['blog', 'user']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} 收藏了 {self.blog.title}"

class Tag(models.Model):
    """标签模型"""
    name = models.CharField(max_length=20, unique=True, verbose_name='标签名')
    description = models.CharField(max_length=100, blank=True, verbose_name='描述')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        verbose_name = '标签'
        verbose_name_plural = '标签'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def blog_count(self):
        """该标签下的博客数量"""
        return Blog.objects.filter(tags__contains=[self.name]).count()

# 信号处理，用于更新计数
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver([post_save, post_delete], sender=BlogLike)
def update_blog_like_count(sender, instance, **kwargs):
    """更新博客点赞数"""
    blog = instance.blog
    blog.like_count = blog.likes.count()
    blog.save(update_fields=['like_count'])

@receiver([post_save, post_delete], sender=BlogComment)
def update_blog_comment_count(sender, instance, **kwargs):
    """更新博客评论数"""
    blog = instance.blog
    blog.comment_count = blog.comments.filter(is_approved=True).count()
    blog.save(update_fields=['comment_count'])

@receiver([post_save, post_delete], sender=CommentLike)
def update_comment_like_count(sender, instance, **kwargs):
    """更新评论点赞数"""
    comment = instance.comment
    comment.like_count = comment.likes.count()
    comment.save(update_fields=['like_count'])








        