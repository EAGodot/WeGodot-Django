from django.contrib import admin
from django.utils.html import format_html
from .models import MarkdownDocument

@admin.register(MarkdownDocument)
class MarkdownDocumentAdmin(admin.ModelAdmin):
    list_display = [
        'title', 
        'is_previewable', 
        'file_encoding',
        'file_size_display', 
        'created_at', 
        'file_link',
        'content_preview_status'
    ]
    
    list_filter = [
        'is_previewable', 
        'file_encoding',
        'created_at'
    ]
    
    search_fields = [
        'title', 
        'description'
    ]
    
    readonly_fields = [
        'file_size', 
        'file_encoding',
        'created_at', 
        'updated_at',
        'preview_content',
        'encoding_info',
        'force_reload_button'
    ]
    
    fieldsets = (
        ('基本信息', {
            'fields': (
                'title', 
                'description', 
                'file',
                'is_previewable'
            )
        }),
        ('文件信息', {
            'fields': (
                'file_size', 
                'file_encoding',
                'encoding_info',
                'force_reload_button',
                'created_at', 
                'updated_at'
            )
        }),
        ('内容预览', {
            'fields': ('preview_content',),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """
        重写保存方法，在保存后检测文件编码
        """
        super().save_model(request, obj, form, change)
        # 保存后检测文件编码
        if obj.file:
            detected_encoding = obj.detect_file_encoding()
            if detected_encoding != obj.file_encoding:
                obj.file_encoding = detected_encoding
                MarkdownDocument.objects.filter(id=obj.id).update(file_encoding=detected_encoding)
    
    def content_preview_status(self, obj):
        """
        显示内容预览状态
        """
        content = obj.get_file_content_safe()
        if content.startswith("无法读取文件内容") or content.startswith("读取文件内容时发生错误"):
            return format_html('<span style="color: red;">❌ 读取失败</span>')
        else:
            preview = content[:50] + "..." if len(content) > 50 else content
            return format_html('<span style="color: green;">✅ 可预览</span>')
    content_preview_status.short_description = '预览状态'
    
    def file_size_display(self, obj):
        """
        在列表页显示友好的文件大小
        """
        if obj.file_size < 1024:
            return f"{obj.file_size} B"
        elif obj.file_size < 1024 * 1024:
            return f"{obj.file_size / 1024:.1f} KB"
        else:
            return f"{obj.file_size / (1024 * 1024):.1f} MB"
    file_size_display.short_description = '文件大小'
    
    def file_link(self, obj):
        """
        在列表页显示文件链接
        """
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank">📥 下载</a>', 
                obj.file.url
            )
        return "-"
    file_link.short_description = '文件操作'
    
    def force_reload_button(self, obj):
        """
        强制重新加载内容的按钮
        """
        if obj.id:
            return format_html(
                '<button type="button" onclick="location.reload()" style="padding: 5px 10px; background: #4CAF50; color: white; border: none; border-radius: 3px; cursor: pointer;">🔄 重新检测编码</button>'
            )
        return ""
    force_reload_button.short_description = '操作'
    
    def preview_content(self, obj):
        """
        在编辑页预览文件内容
        """
        content = obj.get_file_content_safe()
        
        # 显示调试信息
        debug_info = f"""
        <div style="background: #e7f3ff; padding: 8px; margin-bottom: 10px; border-radius: 4px; font-size: 12px;">
            <strong>调试信息:</strong><br>
            文件编码: {obj.file_encoding}<br>
            文件大小: {obj.file_size} 字节<br>
            内容长度: {len(content) if content else 0} 字符
        </div>
        """
        
        if content.startswith("无法读取文件内容") or content.startswith("读取文件内容时发生错误"):
            # 显示错误信息和原始字节
            try:
                with obj.file.open('rb') as f:
                    raw_data = f.read()
                hex_preview = ' '.join(f'{b:02x}' for b in raw_data[:100])
                debug_info += f"""
                <div style="background: #ffe7e7; padding: 8px; margin-bottom: 10px; border-radius: 4px; font-size: 12px;">
                    <strong>原始数据 (前100字节):</strong><br>
                    {hex_preview}...
                </div>
                """
            except:
                pass
            
            return format_html(debug_info + '<div style="color: red; padding: 10px;">{}</div>', content)
        else:
            preview = content[:2000] + "..." if len(content) > 2000 else content
            return format_html(
                debug_info + '<div style="background: #f5f5f5; padding: 15px; border-radius: 5px; max-height: 500px; overflow-y: auto; white-space: pre-wrap; font-family: "Courier New", monospace; font-size: 14px; line-height: 1.4;">{}</div>', 
                preview
            )
    preview_content.short_description = '文件内容预览'
    
    def encoding_info(self, obj):
        """
        显示编码信息
        """
        return format_html(
            '<div style="color: #666; font-size: 12px; background: #f9f9f9; padding: 8px; border-radius: 4px;">'
            '检测到的文件编码: <strong>{}</strong><br>'
            '如果预览显示乱码，可以尝试重新检测编码'
            '</div>',
            obj.file_encoding
        )
    encoding_info.short_description = '编码信息'

    def get_queryset(self, request):
        """
        优化查询性能
        """
        return super().get_queryset(request).select_related()