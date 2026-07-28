from rest_framework import serializers
from .models import MarkdownDocument

class MarkdownDocumentSerializer(serializers.ModelSerializer):
    content = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = MarkdownDocument
        fields = [
            'id',
            'title',
            'description', 
            'file_url',
            'content',
            'is_previewable',
            'created_at',
            'updated_at',
            'file_size'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'file_size']
    
    def get_content(self, obj):
        """
        只有可预览的文档才返回内容
        """
        if obj.is_previewable:
            return obj.get_file_content()
        return None
    
    def get_file_url(self, obj):
        """
        返回文件下载URL
        """
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
        return None

class MarkdownDocumentListSerializer(serializers.ModelSerializer):
    """
    用于列表页的简化序列化器
    """
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = MarkdownDocument
        fields = [
            'id',
            'title',
            'description',
            'file_url',
            'is_previewable',
            'created_at',
            'file_size'
        ]
    
    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
        return None