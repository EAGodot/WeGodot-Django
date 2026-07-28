import os
import uuid
import chardet
from django.db import models
from django.core.exceptions import ValidationError

def validate_markdown_file_extension(value):
    """
    验证文件扩展名是否为Markdown格式
    """
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.md', '.markdown']
    if not ext.lower() in valid_extensions:
        raise ValidationError('只支持Markdown文件 (.md, .markdown)')

def markdown_file_upload_path(instance, filename):
    """
    生成文件上传路径
    """
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return f'markdown_files/{filename}'

class MarkdownDocument(models.Model):
    title = models.CharField(
        max_length=200, 
        verbose_name='文档标题',
        help_text='输入文档的标题'
    )
    
    description = models.TextField(
        blank=True, 
        verbose_name='文档描述',
        help_text='对文档的简要描述'
    )
    
    # 文件字段 - 通过本地路径上传
    file = models.FileField(
        upload_to=markdown_file_upload_path,
        validators=[validate_markdown_file_extension],
        verbose_name='Markdown文件',
        help_text='选择本地的Markdown文件'
    )
    
    # 预览控制属性
    is_previewable = models.BooleanField(
        default=True,
        verbose_name='允许预览',
        help_text='控制Vue前端是否可以加载和预览此文档'
    )
    
    # 元数据
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name='创建时间'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True, 
        verbose_name='更新时间'
    )
    
    file_size = models.PositiveIntegerField(
        default=0,
        verbose_name='文件大小(字节)',
        help_text='自动计算的文件大小'
    )
    
    # 新增字段：文件编码
    file_encoding = models.CharField(
        max_length=20,
        default='utf-8',
        verbose_name='文件编码',
        help_text='自动检测的文件编码'
    )
    
    class Meta:
        verbose_name = 'Markdown文档'
        verbose_name_plural = 'Markdown文档'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({'可预览' if self.is_previewable else '不可预览'})"
    
    def save(self, *args, **kwargs):
        """
        保存时自动计算文件大小
        """
        if self.file:
            self.file_size = self.file.size
        super().save(*args, **kwargs)
    
    def detect_file_encoding(self):
        """
        改进的文件编码检测
        """
        if not self.file:
            return 'utf-8'
            
        try:
            with self.file.open('rb') as f:
                raw_data = f.read()
            
            # 方法1: 首先尝试UTF-8（因为大多数Markdown文件都是UTF-8）
            try:
                raw_data.decode('utf-8')
                return 'utf-8'
            except UnicodeDecodeError:
                pass
            
            # 方法2: 使用chardet检测，但设置置信度阈值
            encoding_result = chardet.detect(raw_data)
            detected_encoding = encoding_result.get('encoding', 'utf-8')
            confidence = encoding_result.get('confidence', 0)
            
            # 如果置信度低于0.8，优先使用中文编码
            if confidence < 0.8:
                # 尝试常见的中文编码
                chinese_encodings = ['gbk', 'gb2312', 'gb18030', 'big5']
                for encoding in chinese_encodings:
                    try:
                        raw_data.decode(encoding)
                        return encoding
                    except UnicodeDecodeError:
                        continue
            
            # 方法3: 使用检测到的编码，但如果是不常见的编码，回退到UTF-8
            common_encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'big5', 'latin-1', 'ascii']
            if detected_encoding.lower() in common_encodings:
                return detected_encoding
            else:
                return 'utf-8'
                
        except Exception as e:
            print(f"编码检测失败: {e}")
            return 'utf-8'
    
    def get_file_content(self):
        """
        改进的文件读取方法，优先使用UTF-8
        """
        try:
            if not self.file:
                return "文件为空或不存在"
            
            # 读取文件内容
            with self.file.open('rb') as f:
                raw_data = f.read()
            
            # 优先尝试UTF-8
            encodings_to_try = ['utf-8']
            
            # 如果模型中有存储的编码，也尝试
            if self.file_encoding and self.file_encoding != 'utf-8':
                encodings_to_try.append(self.file_encoding)
            
            # 添加常见的中文编码
            encodings_to_try.extend(['gbk', 'gb2312', 'gb18030', 'big5'])
            
            # 添加其他常见编码
            encodings_to_try.extend(['latin-1', 'ascii', 'windows-1252'])
            
            for encoding in encodings_to_try:
                try:
                    content = raw_data.decode(encoding)
                    # 如果成功解码，更新编码信息（如果是新检测到的）
                    if encoding != self.file_encoding:
                        self.file_encoding = encoding
                        MarkdownDocument.objects.filter(id=self.id).update(file_encoding=encoding)
                    return content
                except UnicodeDecodeError:
                    continue
            
            # 如果所有编码都失败，使用UTF-8并忽略错误
            content = raw_data.decode('utf-8', errors='ignore')
            return content
            
        except Exception as e:
            return f"读取文件时出错: {str(e)}"
    
    def get_file_content_safe(self):
        """
        安全的文件读取方法
        """
        try:
            content = self.get_file_content()
            if content.startswith("读取文件时出错:"):
                return f"无法读取文件内容: {content}"
            return content
        except Exception as e:
            return f"读取文件内容时发生错误: {str(e)}"
    
    def get_file_extension(self):
        """
        获取文件扩展名
        """
        if self.file:
            return os.path.splitext(self.file.name)[1]
        return ""