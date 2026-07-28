from django.contrib import admin
from .models import Blog, BlogLike, BlogComment, CommentLike, BlogCollection, Tag

@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'status', 'visibility', 'view_count', 'like_count', 'created_at']
    list_filter = ['category', 'status', 'visibility', 'created_at', 'author']
    search_fields = ['title', 'content', 'summary']
    readonly_fields = ['view_count', 'like_count', 'comment_count', 'created_at', 'updated_at']
    fieldsets = (
        ('基本信息', {
            'fields': ('title', 'author', 'summary', 'content')
        }),
        ('分类信息', {
            'fields': ('category', 'tags', 'cover_image')
        }),
        ('状态设置', {
            'fields': ('status', 'visibility', 'is_featured')
        }),
        ('统计信息', {
            'fields': ('view_count', 'like_count', 'comment_count'),
            'classes': ('collapse',)
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at', 'published_at'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.author_id:
            obj.author = request.user
        super().save_model(request, obj, form, change)

@admin.register(BlogLike)
class BlogLikeAdmin(admin.ModelAdmin):
    list_display = ['blog', 'user', 'created_at']
    list_filter = ['created_at']
    search_fields = ['blog__title', 'user__username']

@admin.register(BlogComment)
class BlogCommentAdmin(admin.ModelAdmin):
    list_display = ['blog', 'user', 'content_preview', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'created_at']
    search_fields = ['blog__title', 'user__username', 'content']
    readonly_fields = ['created_at', 'updated_at']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = '评论内容'

@admin.register(CommentLike)
class CommentLikeAdmin(admin.ModelAdmin):
    list_display = ['comment', 'user', 'created_at']
    list_filter = ['created_at']

@admin.register(BlogCollection)
class BlogCollectionAdmin(admin.ModelAdmin):
    list_display = ['blog', 'user', 'created_at']
    list_filter = ['created_at']

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'blog_count', 'created_at']
    search_fields = ['name']
    
    def blog_count(self, obj):
        return obj.blog_count
    blog_count.short_description = '博客数量'