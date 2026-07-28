from django.contrib import admin


# Register your models here.
from appone.models.article import Article
from appone.models.article_like import Article_like
from appone.models.client import Client
from appone.models.code import Code
from appone.models.comment import Comment
from appone.models.family import Family
from appone.models.ip import Ip
from appone.models.label import Label
from appone.models.resource import Resource
from appone.models.resource_path import ResourcePath
from appone.models.sort import Sort
from appone.models.tree_hole import TreeHole
from appone.models.web_info import WebInfo
from appone.models.wei_yan import WeiYan
from appone.models.words import Words

#admin.site.register(Client)
admin.site.register(WebInfo)
admin.site.register(Sort)
admin.site.register(Label)
admin.site.register(Article)
admin.site.register(Comment)
admin.site.register(Resource)
admin.site.register(TreeHole)
admin.site.register(Words)
admin.site.register(Family)
admin.site.register(WeiYan)
admin.site.register(ResourcePath)
admin.site.register(Ip)
admin.site.register(Code)
admin.site.register(Article_like)






class ClientAdmin(admin.ModelAdmin):
    # 列表頁面顯示的字段
    list_display = [
        'user_id', 
        'username', 
        'email', 
        'phone_number',
        'user_type_display',  # 自定義方法顯示選擇字段
        'user_status',
        'gender_display',     # 自定義方法顯示性別
        'province',
        'create_time',
        'deleted'
    ]
    
    # 可以點擊的字段（鏈接到編輯頁面）
    list_display_links = ['username', 'email']
    
    # 右側篩選器
    list_filter = [
        'user_type',
        'user_status',
        'gender',
        'deleted',
        'create_time',
        'province'
    ]
    
    # 搜索字段
    search_fields = [
        'username', 
        'email', 
        'phone_number',
        'province',
        'registration_code'
    ]
    
    # 每頁顯示的記錄數
    list_per_page = 20
    
    # 可以直接在列表頁編輯的字段
    list_editable = ['user_status', 'deleted']
    
    # 詳細頁面的字段分組
    fieldsets = (
        ('基礎信息', {
            'fields': (
                'user', 
                'username', 
                'phone_number', 
                'email',
                'registration_code',
                'code_used_at'
            )
        }),
        ('個人信息', {
            'fields': (
                'province',
                'gender',
                'avatar',
                'introduction',
                'admire'
            )
        }),
        ('賬戶狀態', {
            'fields': (
                'user_status',
                'user_type',
                'deleted'
            )
        }),
        ('第三方集成', {
            'fields': (
                'open_id',
                'qiniu_domain',
                'qiniu_bucket_name',
                'qiniu_access_key',
                'qiniu_secret_key'
            ),
            'classes': ('collapse',)  # 可折疊
        }),
        ('時間信息', {
            'fields': (
                'create_time',
                'update_time',
                'update_by'
            ),
            'classes': ('collapse',)  # 可折疊
        })
    )
    
    # 只讀字段（在編輯頁面）
    readonly_fields = [
        'create_time', 
        'update_time',
        'user_id'
    ]
    
    # 自定義方法：顯示用戶類型的中文
    def user_type_display(self, obj):
        return obj.get_user_type_display()
    user_type_display.short_description = '用戶類型'
    
    # 自定義方法：顯示性別的中文
    def gender_display(self, obj):
        return obj.get_gender_display()
    gender_display.short_description = '性別'
    
    # 根據用戶類型添加顏色標記
    def user_type_display_colored(self, obj):
        colors = {
            0: 'red',      # Boss - 紅色
            1: 'orange',   # 管理員 - 橙色
            2: 'green',    # 普通用戶 - 綠色
            3: 'gray',     # 訪客 - 灰色
        }
        color = colors.get(obj.user_type, 'black')
        return f'<span style="color: {color}; font-weight: bold;">{obj.get_user_type_display()}</span>'
    user_type_display_colored.short_description = '用戶類型'
    user_type_display_colored.allow_tags = True
    
    # 添加自定義動作
    actions = ['enable_users', 'disable_users', 'mark_as_deleted']
    
    def enable_users(self, request, queryset):
        updated = queryset.update(user_status=True)
        self.message_user(request, f'已啟用 {updated} 個用戶')
    enable_users.short_description = "啟用選中的用戶"
    
    def disable_users(self, request, queryset):
        updated = queryset.update(user_status=False)
        self.message_user(request, f'已禁用 {updated} 個用戶')
    disable_users.short_description = "禁用選中的用戶"
    
    def mark_as_deleted(self, request, queryset):
        updated = queryset.update(deleted=True)
        self.message_user(request, f'已標記 {updated} 個用戶為刪除狀態')
    mark_as_deleted.short_description = "標記選中用戶為已刪除"

# 註冊 ModelAdmin
admin.site.register(Client, ClientAdmin)


