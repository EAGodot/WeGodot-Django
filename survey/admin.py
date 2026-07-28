from django.contrib import admin
from django import forms
from django.utils.html import format_html
from django.urls import path, reverse
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import json
import os
from .models import Survey, SurveyResponse, SurveyAnswerAnalysis

# 移除配置方式选择，只保留JSON文本输入
from django.template.loader import render_to_string

class SurveyConfigForm(forms.ModelForm):
    # 新增：是否有问卷配置文件的选择
    has_question_file = forms.BooleanField(
        required=False,
        initial=False,
        label="是否有问卷配置文件",
        help_text="勾选此项表示您将上传问卷配置文件"
    )
    
    # 问卷配置文件上传字段
    question_json_file = forms.FileField(
        required=False,
        label="问卷JSON文件",
        help_text="上传问卷配置文件（JSON格式）",
        widget=forms.FileInput(attrs={'accept': '.json'})
    )
    
    # 新增：是否有答案文件的选择
    has_answer_file = forms.BooleanField(
        required=False,
        initial=False,
        label="是否有答案文件",
        help_text="勾选此项表示您将上传预定义的答案数据文件"
    )
    
    # 答案文件上传字段
    answer_json_file = forms.FileField(
        required=False,
        label="答案JSON文件",
        help_text="上传预定义的答案数据（JSON格式）",
        widget=forms.FileInput(attrs={'accept': '.json'})
    )
    
    # 隐藏原来的questions字段，改为文件上传方式
    questions = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )
    
    class Meta:
        model = Survey
        fields = [
            'title', 'description', 'status', 'created_by', 
            'start_date', 'end_date', 'questions',
            'has_question_file', 'question_json_file',  # 新增问卷文件字段
            'has_answer_file', 'answer_json_file'  # 新增答案文件字段
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 根据实例数据初始化表单字段
        if self.instance and self.instance.pk:
            # 初始化问卷文件相关字段
            if hasattr(self.instance, 'questions') and self.instance.questions:
                self.fields['has_question_file'].initial = True
            
            # 初始化答案文件相关字段
            if hasattr(self.instance, 'answer_data') and self.instance.answer_data:
                self.fields['has_answer_file'].initial = True
    
    def clean(self):
        cleaned_data = super().clean()
        has_question_file = cleaned_data.get('has_question_file')
        question_json_file = cleaned_data.get('question_json_file')
        has_answer_file = cleaned_data.get('has_answer_file')
        answer_json_file = cleaned_data.get('answer_json_file')
        
        # 验证问卷配置文件
        if has_question_file:
            if not question_json_file:
                raise forms.ValidationError({'question_json_file': '请选择要上传的问卷JSON文件'})
            
            # 验证文件类型
            if not question_json_file.name.endswith('.json'):
                raise forms.ValidationError({'question_json_file': '文件必须是JSON格式(.json)'})
            
            # 验证文件内容
            try:
                file_content = question_json_file.read().decode('utf-8')
                question_data = json.loads(file_content)
                # 验证问题结构
                self.validate_questions_structure(question_data)
                # 将验证后的数据存储在cleaned_data中
                cleaned_data['question_json_content'] = question_data
            except json.JSONDecodeError as e:
                raise forms.ValidationError({'question_json_file': f'JSON文件格式错误: {str(e)}'})
            except Exception as e:
                raise forms.ValidationError({'question_json_file': f'读取文件失败: {str(e)}'})
        else:
            # 没有问卷文件，设置为None
            cleaned_data['question_json_content'] = None
        
        # 验证答案文件
        if has_answer_file:
            if not answer_json_file:
                raise forms.ValidationError({'answer_json_file': '请选择要上传的答案JSON文件'})
            
            # 验证文件类型
            if not answer_json_file.name.endswith('.json'):
                raise forms.ValidationError({'answer_json_file': '文件必须是JSON格式(.json)'})
            
            # 验证文件内容
            try:
                file_content = answer_json_file.read().decode('utf-8')
                answer_data = json.loads(file_content)
                # 将验证后的数据存储在cleaned_data中
                cleaned_data['answer_json_content'] = answer_data
            except json.JSONDecodeError as e:
                raise forms.ValidationError({'answer_json_file': f'JSON文件格式错误: {str(e)}'})
            except Exception as e:
                raise forms.ValidationError({'answer_json_file': f'读取文件失败: {str(e)}'})
        else:
            # 没有答案文件，设置为None
            cleaned_data['answer_json_content'] = None
        
        return cleaned_data
    
    def validate_questions_structure(self, questions_data):
        """验证问题结构"""
        if not isinstance(questions_data, dict):
            raise forms.ValidationError('问题配置必须是JSON对象格式')
        
        required_sections = ['multipleChoiceQuestions', 'essayQuestions']
        for section in required_sections:
            if section not in questions_data:
                raise forms.ValidationError(f'缺少必要的问题部分: {section}')
            
            if not isinstance(questions_data[section], list):
                raise forms.ValidationError(f'{section} 必须是数组格式')
        
        # 验证选择题配置
        for i, question in enumerate(questions_data.get('multipleChoiceQuestions', [])):
            if not question.get('id'):
                raise forms.ValidationError(f"选择题 #{i+1} 缺少id字段")
            if not question.get('text'):
                raise forms.ValidationError(f"选择题 #{i+1} 缺少问题文本")
            if not question.get('type') in ['single', 'multiple']:
                raise forms.ValidationError(f"选择题 #{i+1} 类型必须是 'single' 或 'multiple'")
            if not question.get('options'):
                raise forms.ValidationError(f"选择题 #{i+1} 缺少选项配置")
            
            # 验证选项
            for j, option in enumerate(question.get('options', [])):
                if not option.get('value'):
                    raise forms.ValidationError(f"选择题 #{i+1} 选项 #{j+1} 缺少value字段")
                if not option.get('text'):
                    raise forms.ValidationError(f"选择题 #{i+1} 选项 #{j+1} 缺少显示文本")
        
        # 验证论述题配置
        for i, question in enumerate(questions_data.get('essayQuestions', [])):
            if not question.get('id'):
                raise forms.ValidationError(f"论述题 #{i+1} 缺少id字段")
            if not question.get('text'):
                raise forms.ValidationError(f"论述题 #{i+1} 缺少问题文本")
            if question.get('type') != 'essay':
                raise forms.ValidationError(f"论述题 #{i+1} 类型必须是 'essay'")

class SurveyResponseInline(admin.TabularInline):
    model = SurveyResponse
    extra = 0
    readonly_fields = ['user', 'submitted_at', 'user_ip', 'is_anonymous']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    form = SurveyConfigForm
    actions = ['make_active', 'make_closed', 'make_draft']

    list_display = [
        'id',
        'display_survey_id_admin',
        'title', 
        'status_badge', 
        'created_by', 
        'created_at', 
        'response_count', 
        'is_active_badge',
        #'has_question_file_badge',  # 新增：是否有问卷文件徽章
        'has_answer_file_badge',    # 新增：是否有答案文件徽章
        'action_links'
    ]
    
    list_display_links = ['id', 'display_survey_id_admin', 'title']
    
    list_filter = [
        'status', 
        'created_at',
        'created_by',
    ]
    
    search_fields = ['title', 'description', 'created_by__username']
    
    readonly_fields = [
        'id',
        'display_survey_id',
        'created_at', 
        'updated_at', 
        'response_count', 
        'questions_preview',
        'answer_file_preview',  # 答案文件预览
        'config_info'
    ]
    
    fieldsets = (
        ('ID信息', {
            'fields': (
                'id',
                'display_survey_id',
            ),
            'classes': ('collapse',)
        }),
        ('基本信息', {
            'fields': (
                'title', 
                'description', 
                'status',
                'created_by',
                ('created_at', 'updated_at')
            )
        }),
        ('时间设置', {
            'fields': (
                'start_date',
                'end_date',
            ),
            'classes': ('collapse',)
        }),
        ('问卷问题配置', {
            'fields': ('has_question_file', 'question_json_file', 'questions_preview'),
            'description': '上传问卷配置文件（JSON格式）'
        }),
        ('调查问卷答案', {
            'fields': ('has_answer_file', 'answer_json_file', 'answer_file_preview'),
            'description': '可选：上传预定义的答案数据（JSON格式）'
        }),
        ('统计信息', {
            'fields': ('response_count',),
            'classes': ('wide',)
        }),
    )
    
    inlines = [SurveyResponseInline]
    
    class Media:
        css = {
            'all': ['admin/css/survey_admin.css']
        }
    
    def make_active(self, request, queryset):
        updated_count = queryset.update(status='active')
        self.message_user(
            request, 
            f'成功发布了 {updated_count} 个问卷', 
            messages.SUCCESS
        )
    make_active.short_description = "发布选中的问卷"
    
    def make_closed(self, request, queryset):
        updated_count = queryset.update(status='closed')
        self.message_user(
            request, 
            f'成功关闭了 {updated_count} 个问卷', 
            messages.SUCCESS
        )
    make_closed.short_description = "关闭选中的问卷"
    
    def make_draft(self, request, queryset):
        updated_count = queryset.update(status='draft')
        self.message_user(
            request, 
            f'成功将 {updated_count} 个问卷设为草稿', 
            messages.SUCCESS
        )
    make_draft.short_description = "将选中的问卷设为草稿"
    
    def save_model(self, request, obj, form, change):
        # 处理问卷文件上传
        has_question_file = form.cleaned_data.get('has_question_file', False)
        question_json_content = form.cleaned_data.get('question_json_content')
        
        if has_question_file and question_json_content:
            # 有问卷文件，保存问卷数据
            obj.questions = question_json_content
            messages.success(request, f'成功上传问卷文件，包含 {len(question_json_content.get("multipleChoiceQuestions", []))} 个选择题和 {len(question_json_content.get("essayQuestions", []))} 个论述题')
        else:
            # 没有问卷文件，设置为None
            obj.questions = None
            if has_question_file:  # 用户勾选了但有错误
                messages.warning(request, '问卷文件上传失败，已保存其他数据')
            else:
                messages.info(request, '未上传问卷文件')
        
        # 处理答案文件上传
        has_answer_file = form.cleaned_data.get('has_answer_file', False)
        answer_json_content = form.cleaned_data.get('answer_json_content')
        
        if has_answer_file and answer_json_content:
            # 有答案文件，保存答案数据
            obj.answer_data = answer_json_content
            messages.success(request, f'成功上传答案文件，包含 {len(answer_json_content) if isinstance(answer_json_content, list) else "未知数量"} 条答案数据')
        else:
            # 没有答案文件，设置为None
            obj.answer_data = None
            if has_answer_file:  # 用户勾选了但有错误
                messages.warning(request, '答案文件上传失败，已保存其他数据')
            else:
                messages.info(request, '未上传答案文件')
        
        # 设置创建者
        if not obj.pk:
            obj.created_by = request.user
        
        super().save_model(request, obj, form, change)
    
    # 自定义显示字段
    def display_survey_id(self, obj):
        """显示格式化的问卷ID"""
        return obj.display_survey_id()
    display_survey_id.short_description = '问卷编号'
    
    def has_question_file_badge(self, obj):
        """显示是否有问卷文件的徽章"""
        if hasattr(obj, 'questions') and obj.questions:
            return format_html(
                '<span style="background: #28a745; color: white; padding: 3px 8px; border-radius: 12px; font-size: 12px; font-weight: bold;">✅ 有问卷文件</span>'
            )
        else:
            return format_html(
                '<span style="background: #6c757d; color: white; padding: 3px 8px; border-radius: 12px; font-size: 12px; font-weight: bold;">❌ 无问卷文件</span>'
            )
    has_question_file_badge.short_description = '问卷文件'
    
    def has_answer_file_badge(self, obj):
        """显示是否有答案文件的徽章"""
        if hasattr(obj, 'answer_data') and obj.answer_data:
            return format_html(
                '<span style="background: #28a745; color: white; padding: 3px 8px; border-radius: 12px; font-size: 12px; font-weight: bold;">✅ 有答案</span>'
            )
        else:
            return format_html(
                '<span style="background: #6c757d; color: white; padding: 3px 8px; border-radius: 12px; font-size: 12px; font-weight: bold;">❌ 无答案</span>'
            )
    has_answer_file_badge.short_description = '答案文件'
    
    def questions_preview(self, obj):
        """问卷文件预览 - 与答案文件相同的格式"""
        if not hasattr(obj, 'questions') or not obj.questions:
            return format_html(
                '<div style="color: gray; font-style: italic;">暂无问卷文件</div>'
            )
        
        try:
            questions_data = obj.questions
            
            # 使用format_html安全地构建所有内容
            preview_parts = []
            
            # 添加标题
            preview_parts.append(format_html("<h4>问卷配置预览</h4>"))
            
            if isinstance(questions_data, (list, dict)):
                # 尝试格式化JSON
                try:
                    formatted_json = json.dumps(questions_data, ensure_ascii=False, indent=2)
                    
                    # 使用mark_safe来允许显示格式化的JSON
                    from django.utils.safestring import mark_safe
                    # 将换行符和空格转换为HTML标签
                    formatted_display = formatted_json.replace('\n', '<br>').replace('  ', '&nbsp;&nbsp;')
                    json_display = mark_safe(formatted_display)
                    
                    preview_parts.append(format_html(
                        '<div style="background: #f5f5f5; padding: 15px; border-radius: 5px; font-family: monospace; white-space: pre-wrap; max-height: 600px; overflow-y: auto; border: 1px solid #ddd; font-size: 12px; line-height: 1.4;">{}</div>',
                        json_display
                    ))
                    
                    # 添加统计信息
                    if isinstance(questions_data, dict):
                        mc_count = len(questions_data.get('multipleChoiceQuestions', []))
                        essay_count = len(questions_data.get('essayQuestions', []))
                        preview_parts.append(format_html(
                            '<div style="margin-top: 10px; color: #666; font-size: 12px; padding: 5px; background: #e8f4fd; border-radius: 3px;">📊 问卷配置 - 选择题: {}个, 论述题: {}个</div>',
                            mc_count, essay_count
                        ))
                    else:
                        preview_parts.append(format_html(
                            '<div style="margin-top: 10px; color: #666; font-size: 12px; padding: 5px; background: #e8f4fd; border-radius: 3px;">📊 数据类型: 列表，包含 {} 个元素</div>',
                            len(questions_data)
                        ))
                        
                except Exception as json_error:
                    # JSON格式化失败，使用简单显示
                    data_str = str(questions_data)
                    
                    preview_parts.append(format_html(
                        '<div style="color: orange; margin-bottom: 10px; padding: 8px; background: #fff3cd; border-radius: 4px;">⚠️ 无法格式化显示JSON数据: {}</div>',
                        str(json_error)
                    ))
                    
                    # 使用mark_safe显示原始数据
                    from django.utils.safestring import mark_safe
                    data_display = mark_safe(data_str.replace('\n', '<br>'))
                    
                    preview_parts.append(format_html(
                        '<div style="background: #f5f5f5; padding: 15px; border-radius: 5px; border: 1px solid #ddd; font-family: monospace; font-size: 12px; white-space: pre-wrap; max-height: 600px; overflow-y: auto;">{}</div>',
                        data_display
                    ))
                    
            else:
                # 其他数据类型
                data_str = str(questions_data)
                
                from django.utils.safestring import mark_safe
                data_display = mark_safe(data_str.replace('\n', '<br>'))
                
                preview_parts.append(format_html(
                    '<div style="margin-bottom: 10px; color: #333;">数据类型: <strong>{}</strong></div>',
                    type(questions_data).__name__
                ))
                preview_parts.append(format_html(
                    '<div style="background: #f5f5f5; padding: 15px; border-radius: 5px; border: 1px solid #ddd; font-family: monospace; font-size: 12px; white-space: pre-wrap; max-height: 600px; overflow-y: auto;">{}</div>',
                    data_display
                ))
            
            # 返回组合的内容
            return format_html("{}" * len(preview_parts), *preview_parts)
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            return format_html(
                '<div style="color: red; padding: 10px; background: #ffeaea; border-radius: 5px; border: 1px solid #ffcccc;">'
                '<strong>预览失败:</strong> {}<br>'
                '<details style="margin-top: 10px;"><summary>错误详情</summary><pre style="font-size: 10px; white-space: pre-wrap; background: #f5f5f5; padding: 10px; border-radius: 3px;">{}</pre></details>'
                '</div>',
                str(e),
                error_details
            )
    questions_preview.short_description = "问卷配置预览"
    
    def answer_file_preview(self, obj):
        """答案文件预览 - 与问卷文件相同的格式"""
        if not hasattr(obj, 'answer_data') or not obj.answer_data:
            return format_html(
                '<div style="color: gray; font-style: italic;">暂无答案文件</div>'
            )
        
        try:
            answer_data = obj.answer_data
            
            # 使用format_html安全地构建所有内容
            preview_parts = []
            
            # 添加标题
            preview_parts.append(format_html("<h4>答案数据预览</h4>"))
            
            if isinstance(answer_data, (list, dict)):
                # 尝试格式化JSON
                try:
                    formatted_json = json.dumps(answer_data, ensure_ascii=False, indent=2)
                    
                    # 使用mark_safe来允许显示格式化的JSON
                    from django.utils.safestring import mark_safe
                    # 将换行符和空格转换为HTML标签
                    formatted_display = formatted_json.replace('\n', '<br>').replace('  ', '&nbsp;&nbsp;')
                    json_display = mark_safe(formatted_display)
                    
                    preview_parts.append(format_html(
                        '<div style="background: #f5f5f5; padding: 15px; border-radius: 5px; font-family: monospace; white-space: pre-wrap; max-height: 600px; overflow-y: auto; border: 1px solid #ddd; font-size: 12px; line-height: 1.4;">{}</div>',
                        json_display
                    ))
                    
                    # 添加统计信息
                    if isinstance(answer_data, list):
                        preview_parts.append(format_html(
                            '<div style="margin-top: 10px; color: #666; font-size: 12px; padding: 5px; background: #e8f4fd; border-radius: 3px;">📊 共 {} 条答案记录</div>',
                            len(answer_data)
                        ))
                    else:
                        preview_parts.append(format_html(
                            '<div style="margin-top: 10px; color: #666; font-size: 12px; padding: 5px; background: #e8f4fd; border-radius: 3px;">📊 字典类型，包含 {} 个键</div>',
                            len(answer_data)
                        ))
                        
                except Exception as json_error:
                    # JSON格式化失败，使用简单显示
                    data_str = str(answer_data)
                    
                    preview_parts.append(format_html(
                        '<div style="color: orange; margin-bottom: 10px; padding: 8px; background: #fff3cd; border-radius: 4px;">⚠️ 无法格式化显示JSON数据: {}</div>',
                        str(json_error)
                    ))
                    
                    # 使用mark_safe显示原始数据
                    from django.utils.safestring import mark_safe
                    data_display = mark_safe(data_str.replace('\n', '<br>'))
                    
                    preview_parts.append(format_html(
                        '<div style="background: #f5f5f5; padding: 15px; border-radius: 5px; border: 1px solid #ddd; font-family: monospace; font-size: 12px; white-space: pre-wrap; max-height: 600px; overflow-y: auto;">{}</div>',
                        data_display
                    ))
                    
            else:
                # 其他数据类型
                data_str = str(answer_data)
                
                from django.utils.safestring import mark_safe
                data_display = mark_safe(data_str.replace('\n', '<br>'))
                
                preview_parts.append(format_html(
                    '<div style="margin-bottom: 10px; color: #333;">数据类型: <strong>{}</strong></div>',
                    type(answer_data).__name__
                ))
                preview_parts.append(format_html(
                    '<div style="background: #f5f5f5; padding: 15px; border-radius: 5px; border: 1px solid #ddd; font-family: monospace; font-size: 12px; white-space: pre-wrap; max-height: 600px; overflow-y: auto;">{}</div>',
                    data_display
                ))
            
            # 返回组合的内容
            return format_html("{}" * len(preview_parts), *preview_parts)
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            return format_html(
                '<div style="color: red; padding: 10px; background: #ffeaea; border-radius: 5px; border: 1px solid #ffcccc;">'
                '<strong>预览失败:</strong> {}<br>'
                '<details style="margin-top: 10px;"><summary>错误详情</summary><pre style="font-size: 10px; white-space: pre-wrap; background: #f5f5f5; padding: 10px; border-radius: 3px;">{}</pre></details>'
                '</div>',
                str(e),
                error_details
            )
    answer_file_preview.short_description = '答案文件预览'

    def config_info(self, obj):
        """配置状态信息"""
        if obj.pk:
            if hasattr(obj, 'questions') and obj.questions and isinstance(obj.questions, dict):
                mc_count = len(obj.questions.get('multipleChoiceQuestions', []))
                essay_count = len(obj.questions.get('essayQuestions', []))
                return format_html(
                    '✅ 文件配置已加载<br>'
                    '<small>选择题: {}个, 论述题: {}个</small>',
                    mc_count, essay_count
                )
            else:
                return "❌ 无问卷配置或配置格式错误"
        return "请上传问卷配置文件"
    config_info.short_description = '配置状态'
        
    def status_badge(self, obj):
        """状态徽章"""
        color_map = {
            'draft': '#6c757d',
            'active': '#28a745', 
            'closed': '#dc3545'
        }
        color = color_map.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 12px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = '状态'
    
    def is_active_badge(self, obj):
        """激活状态徽章"""
        if obj.is_active:
            return format_html(
                '<span style="background: #28a745; color: white; padding: 3px 8px; border-radius: 12px; font-size: 12px;">活跃</span>'
            )
        else:
            return format_html(
                '<span style="background: #dc3545; color: white; padding: 3px 8px; border-radius: 12px; font-size: 12px;">未激活</span>'
            )
    is_active_badge.short_description = '激活状态'
    
    def response_count(self, obj):
        """回答数量"""
        count = obj.responses.count()
        try:
            url = reverse('admin:survey_surveyresponse_changelist') + f'?survey__id__exact={obj.id}'
            return format_html('<a href="{}">{}</a>', url, count)
        except Exception as e:
            return str(count)
    response_count.short_description = '回答数'
    
    def action_links(self, obj):
        """操作链接"""
        links = []
        try:
            change_url = reverse('admin:survey_survey_change', args=[obj.id])
            links.append(f'<a href="{change_url}">编辑</a>')
            
            preview_url = reverse('survey-preview', args=[obj.id])
            links.append(f'<a href="{preview_url}" target="_blank">预览</a>')
        except Exception as e:
            links.append('<span>操作不可用</span>')
        
        return format_html(' | '.join(links)) if links else '-'
    action_links.short_description = '操作'
    
    def display_survey_id_admin(self, obj):
        """在admin列表中安全显示问卷ID"""
        return obj.display_survey_id()
    display_survey_id_admin.short_description = '问卷编号'

# 其他Admin类保持不变...
@admin.register(SurveyResponse)
class SurveyResponseAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'display_response_id_admin',
        'survey', 
        'user_display', 
        'submitted_at', 
        'is_anonymous'
    ]
    list_display_links = ['id', 'display_response_id_admin']

    list_filter = ['survey', 'submitted_at', 'is_anonymous']
    search_fields = ['survey__title', 'user__username']
    readonly_fields = [
        'id',
        'display_response_id',
        'submitted_at', 
        'user_ip', 
        'user_agent'
    ]
    
    def user_display(self, obj):
        if obj.user:
            return obj.user.username
        return "匿名用户"
    user_display.short_description = "用户"
    
    def display_response_id(self, obj):
        return obj.display_response_id()
    display_response_id.short_description = '回答编号'

    def display_response_id_admin(self, obj):
        """安全显示回答ID"""
        return obj.display_response_id()
    display_response_id_admin.short_description = '回答编号'

@admin.register(SurveyAnswerAnalysis)
class SurveyAnswerAnalysisAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'display_analysis_id_admin',
        'survey', 
        'total_responses', 
        'last_updated'
    ]
    list_display_links = ['id', 'display_analysis_id_admin']
    readonly_fields = [
        'id',
        'display_analysis_id',
        'total_responses', 
        'answer_statistics', 
        'last_updated'
    ]
    list_filter = ['last_updated']
    
    def display_analysis_id(self, obj):
        return obj.display_analysis_id()
    display_analysis_id.short_description = '分析编号'

    def display_analysis_id_admin(self, obj):
        """安全显示分析ID"""
        return obj.display_analysis_id()
    display_analysis_id_admin.short_description = '分析编号'