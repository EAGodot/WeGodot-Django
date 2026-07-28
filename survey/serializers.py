from rest_framework import serializers
from .models import Survey, SurveyResponse, SurveyAnswerAnalysis
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class SurveySerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    is_active = serializers.ReadOnlyField()
    response_count = serializers.SerializerMethodField()
    survey_id = serializers.SerializerMethodField()
    display_id = serializers.SerializerMethodField()
    
    class Meta:
        model = Survey
        fields = [
            'id', 'survey_id', 'display_id', 'title', 'description', 'questions', 'status',
            'created_by', 'created_at', 'updated_at', 'start_date',
            'end_date', 'is_active', 'response_count'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']
    
    def get_response_count(self, obj):
        return obj.responses.count()
    
    def get_survey_id(self, obj):
        return obj.id
    
    def get_display_id(self, obj):
        return f"SURV-{obj.id:04d}"
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)



class SurveyResponseSerializer(serializers.ModelSerializer):
    survey_title = serializers.CharField(source='survey.title', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    survey_id = serializers.IntegerField(source='survey.id', read_only=True)
    display_response_id = serializers.SerializerMethodField()
    
    class Meta:
        model = SurveyResponse
        fields = [
            'id', 'display_response_id', 'survey', 'survey_id', 'survey_title', 
            'user', 'username', 'user_ip', 'user_agent', 'answers', 
            'submitted_at', 'is_anonymous'
        ]
        read_only_fields = ['user_ip', 'user_agent', 'submitted_at']
    
    def get_display_response_id(self, obj):
        return f"RESP-{obj.id:04d}"
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            validated_data['user'] = request.user
        if request:
            validated_data['user_ip'] = self.get_client_ip(request)
            validated_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')
        
        return super().create(validated_data)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip




class SurveyAnswerAnalysisSerializer(serializers.ModelSerializer):
    survey_title = serializers.CharField(source='survey.title', read_only=True)
    display_analysis_id = serializers.SerializerMethodField()
    
    class Meta:
        model = SurveyAnswerAnalysis
        fields = [
            'id', 'display_analysis_id', 'survey', 'survey_title', 
            'total_responses', 'answer_statistics', 'last_updated'
        ]
    
    def get_display_analysis_id(self, obj):
        return f"ANAL-{obj.id:04d}"





#from ..luntan.services.deepseek_service import DeepSeekService
from luntan.services.deepseek_service import DeepSeekService
from django.utils import timezone

class SurveyResponseSubmitSerializer(serializers.ModelSerializer):
    """专门用于提交问卷的简化序列化器"""
    
    # 新增字段用于返回序列号
    registration_code = serializers.CharField(read_only=True)
    
    class Meta:
        model = SurveyResponse
        fields = ['survey', 'answers', 'is_anonymous', 'registration_code']
        read_only_fields = ['registration_code']
    
    def create(self, validated_data):
        request = self.context.get('request')
        
        print("创建回答记录，验证数据:", validated_data)
        
        # 处理用户认证
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            user = request.user
            print(f"已登录用户: {user.username}")
            
            # 检查是否已经提交过（仅对已登录用户）
            existing_response = SurveyResponse.objects.filter(
                survey=validated_data['survey'], 
                user=user
            ).first()
            if existing_response:
                # 简单直接的时间格式化，不处理时区
                submit_time = existing_response.submitted_at
                time_str = submit_time.strftime('%Y-%m-%d %H:%M:%S')
                raise serializers.ValidationError(f'您已经在 {time_str} 提交过该问卷，无法重复提交')
            
            validated_data['user'] = user
        else:
            # 匿名用户，设置为 None
            validated_data['user'] = None
            print("匿名用户提交")
        
        # 处理 IP 和 User-Agent
        if request:
            validated_data['user_ip'] = self.get_client_ip(request)
            validated_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')
            print(f"用户IP: {validated_data['user_ip']}")
        
        try:
            # 创建回答记录
            survey_response = super().create(validated_data)
            
            # 调用AI评估
            self._evaluate_with_ai(survey_response)
            
            return survey_response
            
        except Exception as e:
            print(f"创建回答记录时出错: {str(e)}")
            raise
    
    def _evaluate_with_ai(self, survey_response):
        """使用本地逻辑评估问卷回答"""
        try:
            survey = survey_response.survey
            
            # 检查是否有标准答案（可选）
            standard_answers = {}
            if hasattr(survey, 'answer_data') and survey.answer_data:
                standard_answers = survey.answer_data
            
            user_answers = survey_response.answers
            
            # 调用本地评估服务
            deepseek_service = DeepSeekService()
            evaluation_result = deepseek_service.evaluate_survey_response(
                survey_title=survey.title,
                standard_answers=standard_answers,
                user_answers=user_answers
            )
            
            # 更新回答记录
            survey_response.ai_score = evaluation_result['score']
            survey_response.ai_comment = evaluation_result['comment']
            survey_response.ai_evaluated_at = timezone.now()
            
            # 如果评分大于60分，生成注册序列号
            if evaluation_result['score'] > 60:
                registration_code = survey_response.generate_registration_code()
                survey_response.registration_code = registration_code
                survey_response.code_generated_at = timezone.now()
                print(f"生成注册序列号: {registration_code}")
            
            survey_response.save()
            
            print(f"评估完成 - 评分: {evaluation_result['score']}")
            
        except Exception as e:
            print(f"评估失败，使用默认评估: {str(e)}")
            # 即使评估失败，也提供一个默认评估
            self._provide_default_evaluation(survey_response)
    
    def _provide_default_evaluation(self, survey_response):
        """提供默认评估"""
        try:
            user_answers = survey_response.answers
            
            # 简单的基础评分
            base_score = 70
            
            # 根据回答数量微调
            answer_count = len(user_answers)
            if answer_count > 3:
                base_score += 10
            elif answer_count > 1:
                base_score += 5
            
            # 限制分数范围
            final_score = max(60, min(85, base_score))
            
            # 生成简单评语
            if final_score >= 80:
                comment = "感谢您的详细回答！您的反馈很有价值。"
            elif final_score >= 70:
                comment = "感谢您的参与！您的回答对我们很有帮助。"
            else:
                comment = "感谢您的反馈！期待您更详细的意见。"
            
            survey_response.ai_score = final_score
            survey_response.ai_comment = comment
            survey_response.ai_evaluated_at = timezone.now()
            
            # 如果评分大于60分，生成注册序列号
            if final_score > 60:
                registration_code = survey_response.generate_registration_code()
                survey_response.registration_code = registration_code
                survey_response.code_generated_at = timezone.now()
                print(f"生成注册序列号: {registration_code}")
            
            survey_response.save()
            
            print(f"默认评估完成 - 评分: {final_score}")
            
        except Exception as e:
            print(f"默认评估也失败了: {str(e)}")
            # 如果连默认评估都失败，至少记录评估时间
            survey_response.ai_comment = "评估系统暂时不可用"
            survey_response.ai_evaluated_at = timezone.now()
            survey_response.save()
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

