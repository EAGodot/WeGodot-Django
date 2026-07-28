from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import TokenAuthentication
from django.utils import timezone
from django.db.models import Q
from django.shortcuts import get_object_or_404
import json
from .models import Survey, SurveyResponse, SurveyAnswerAnalysis
from .serializers import SurveySerializer, SurveyResponseSerializer,SurveyAnswerAnalysisSerializer,SurveyResponseSubmitSerializer

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required

from rest_framework import serializers
from rest_framework.exceptions import ValidationError


def survey_preview(request, survey_id):
    """
    问卷预览页面
    """
    survey = get_object_or_404(Survey, id=survey_id)
    
    # 检查权限：只有创建者或超级用户可以预览
    if not request.user.is_authenticated:
        return render(request, 'admin/surveys/access_denied.html', {
            'message': '请先登录'
        })
    
    if not (request.user == survey.created_by or request.user.is_superuser):
        return render(request, 'admin/surveys/access_denied.html', {
            'message': '您没有权限预览此问卷'
        })
    
    # 构建预览数据
    preview_data = {
        'survey': survey,
        'is_preview': True,
        'preview_message': '这是预览模式，提交的数据不会被保存'
    }
    
    return render(request, 'admin/surveys/preview.html', preview_data)

@require_http_methods(["POST"])
@csrf_exempt
def submit_survey_preview(request, survey_id):
    """
    预览模式的问卷提交（不保存到数据库）
    """
    survey = get_object_or_404(Survey, id=survey_id)
    
    try:
        data = json.loads(request.body)
        answers = data.get('answers', {})
        
        # 验证回答数据（但不保存）
        validation_result = validate_survey_answers(survey.questions, answers)
        
        if validation_result['success']:
            return JsonResponse({
                'success': True,
                'message': '预览提交成功（数据未保存）',
                'answers': answers,
                'is_preview': True
            })
        else:
            return JsonResponse({
                'success': False,
                'error': validation_result['error'],
                'is_preview': True
            })
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': '无效的JSON数据',
            'is_preview': True
        })

def validate_survey_answers(questions, answers):
    """
    验证问卷回答数据
    """
    try:
        mc_questions = questions.get('multipleChoiceQuestions', [])
        essay_questions = questions.get('essayQuestions', [])
        
        # 检查必填问题
        for question in mc_questions + essay_questions:
            if question.get('required', False):
                question_id = str(question['id'])
                if question_id not in answers or not answers[question_id]:
                    return {
                        'success': False,
                        'error': f'请完成必填问题: {question.get("text", "")}'
                    }
        
        return {'success': True}
        
    except Exception as e:
        return {
            'success': False,
            'error': f'数据验证失败: {str(e)}'
        }


# 辅助函数
def get_client_ip(request):
    """获取客户端IP地址"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def validate_answers(questions, answers):
    """验证回答数据格式"""
    try:
        mc_questions = questions.get('multipleChoiceQuestions', [])
        essay_questions = questions.get('essayQuestions', [])
        
        # 检查必填问题
        for question in mc_questions + essay_questions:
            if question.get('required', False):
                question_id = str(question['id'])
                if question_id not in answers or not answers[question_id]:
                    return False
        
        return True
    except (KeyError, TypeError):
        return False

def update_survey_analysis(survey):
    """更新问卷统计分析"""
    analysis, created = SurveyAnswerAnalysis.objects.get_or_create(survey=survey)
    analysis.total_responses = survey.responses.count()
    
    # 统计选择题答案
    statistics = {}
    mc_questions = survey.questions.get('multipleChoiceQuestions', [])
    
    for question in mc_questions:
        question_id = str(question['id'])
        question_stats = {
            'question_text': question['text'],
            'type': question['type'],
            'options': {},
            'total_answers': 0
        }
        
        # 统计每个选项的选择次数
        for option in question.get('options', []):
            option_value = option['value']
            count = SurveyResponse.objects.filter(
                answers__has_key=question_id
            ).filter(
                answers__contains={question_id: option_value}
            ).count()
            
            question_stats['options'][option_value] = {
                'text': option['text'],
                'count': count,
                'percentage': 0
            }
            question_stats['total_answers'] += count
        
        # 计算百分比
        if question_stats['total_answers'] > 0:
            for option_data in question_stats['options'].values():
                option_data['percentage'] = round(
                    (option_data['count'] / question_stats['total_answers']) * 100, 2
                )
        
        statistics[question_id] = question_stats
    
    analysis.answer_statistics = statistics
    analysis.save()



class LatestActiveSurveyView(APIView):
    """
    获取最新的活跃问卷
    """
    permission_classes = [AllowAny]
    def get(self, request):
        """
        获取最新的活跃问卷配置
        GET /api/surveys/latest-active/
        """
        print("=== 获取最新活跃问卷 ===")
        print(f"当前用户: {request.user.username if request.user.is_authenticated else '匿名用户'}")
        
        try:
            # 获取最新的活跃问卷，按创建时间倒序排列
            latest_active_survey = Survey.objects.filter(
                status='active'
            ).filter(
                Q(start_date__isnull=True) | Q(start_date__lte=timezone.now())
            ).filter(
                Q(end_date__isnull=True) | Q(end_date__gte=timezone.now())
            ).order_by('-created_at').first()
            
            if not latest_active_survey:
                return Response({
                    'success': False,
                    'error': '当前没有活跃的问卷',
                    'error_code': 'NO_ACTIVE_SURVEY'
                }, status=status.HTTP_404_NOT_FOUND)
            
            print(f"找到最新活跃问卷: {latest_active_survey.title} (ID: {latest_active_survey.id})")
            
            # 构建配置响应
            config_data = {
                'id': latest_active_survey.id,
                'title': latest_active_survey.title,
                'description': latest_active_survey.description,
                'questions': latest_active_survey.questions,
                'settings': {
                    'allow_anonymous': True,
                    'max_responses': None,
                    'start_date': latest_active_survey.start_date,
                    'end_date': latest_active_survey.end_date,
                    'require_login': False,
                },
                'meta': {
                    'created_by': latest_active_survey.created_by.username if latest_active_survey.created_by else '系统',
                    'created_at': latest_active_survey.created_at,
                    'response_count': latest_active_survey.responses.count(),
                    'is_active': latest_active_survey.is_active
                }
            }
            
            return Response({
                'success': True,
                'data': config_data,
                'message': '获取最新问卷配置成功'
            })
            
        except Exception as e:
            print(f"获取最新活跃问卷错误: {str(e)}")
            import traceback
            print(f"错误堆栈: {traceback.format_exc()}")
            
            return Response({
                'success': False,
                'error': '获取最新问卷配置失败',
                'error_code': 'CONFIG_LOAD_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class SurveyConfigView(APIView):
    """
    获取问卷配置信息
    允许匿名访问，但只返回活跃状态的问卷
    """
    permission_classes = [AllowAny]
    
    def get(self, request, survey_id):
        """
        获取问卷配置
        GET /api/surveys/1/config/
        """
        print("=== 获取问卷配置 ===")
        print(f"问卷ID: {survey_id}")
        print(f"当前用户: {request.user.username if request.user.is_authenticated else '匿名用户'}")
        
        try:
            # 获取问卷，只返回活跃状态的问卷
            survey = get_object_or_404(Survey, id=survey_id)
            
            # 检查问卷状态
            if not survey.is_active:
                return Response({
                    'success': False,
                    'error': '该问卷未发布或已结束',
                    'error_code': 'SURVEY_NOT_ACTIVE'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # 构建配置响应
            config_data = {
                'id': survey.id,
                'title': survey.title,
                'description': survey.description,
                'questions': survey.questions,
                'settings': {
                    'allow_anonymous': True,
                    'max_responses': None,
                    'start_date': survey.start_date,
                    'end_date': survey.end_date,
                    'require_login': False,
                },
                'meta': {
                    'created_by': survey.created_by.username if survey.created_by else '系统',
                    'created_at': survey.created_at,
                    'response_count': survey.responses.count(),
                    'is_active': survey.is_active
                }
            }
            
            print(f"返回问卷配置: {survey.title}")
            
            return Response({
                'success': True,
                'data': config_data,
                'message': '获取问卷配置成功'
            })
            
        except Exception as e:
            print(f"获取问卷配置错误: {str(e)}")
            return Response({
                'success': False,
                'error': '获取问卷配置失败',
                'error_code': 'CONFIG_LOAD_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




# 问卷列表视图
class SurveyListView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        """
        获取问卷列表 - 支持个人模式和全部模式
        """
        print("=== 获取问卷列表 ===")
        print("请求参数:", dict(request.GET))
        print("当前用户:", request.user.username if request.user.is_authenticated else "匿名用户")
        
        # 获取查询参数
        mode = request.GET.get('mode', 'active')  # active, my, all
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        
        # 计算分页
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        
        if mode == 'my' and request.user.is_authenticated:
            # 获取用户创建的问卷
            surveys = Survey.objects.filter(created_by=request.user)
        elif mode == 'all' and (request.user.is_authenticated and request.user.is_superuser):
            # 获取所有问卷（仅超级用户）
            surveys = Survey.objects.all()
        else:
            # 获取活跃问卷 - 优化查询，直接使用数据库过滤
            now = timezone.now()
            surveys = Survey.objects.filter(
                status='active'
            ).filter(
                Q(start_date__isnull=True) | Q(start_date__lte=now)
            ).filter(
                Q(end_date__isnull=True) | Q(end_date__gte=now)
            ).order_by('-created_at')
        
        # 总数
        total_count = surveys.count()
        
        # 分页
        paginated_surveys = surveys[start_index:end_index]
        
        serializer = SurveySerializer(paginated_surveys, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_count': total_count,
                'total_pages': (total_count + page_size - 1) // page_size
            }
        })






# 问卷详情视图
class SurveyDetailView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, survey_id):
        """
        获取问卷详情
        """
        print("=== 获取问卷详情 ===")
        print("问卷ID:", survey_id)
        print("当前用户:", request.user.username if request.user.is_authenticated else "匿名用户")
        
        survey = get_object_or_404(Survey, id=survey_id)
        
        # 检查权限
        if not survey.is_active and not (request.user.is_authenticated and survey.created_by == request.user):
            return Response({
                'success': False,
                'error': '无权访问此问卷'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = SurveySerializer(survey)
        return Response({
            'success': True,
            'data': serializer.data
        })





# 创建问卷视图
class SurveyCreateView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    
    def post(self, request):
        """
        创建新问卷
        """
        print("=== 创建问卷 ===")
        print("请求数据:", request.data)
        print("当前用户:", request.user.username)
        
        survey_data = {
            'title': request.data.get('title'),
            'description': request.data.get('description', ''),
            'questions': request.data.get('questions', {}),
            'status': request.data.get('status', 'draft'),
            'start_date': request.data.get('start_date'),
            'end_date': request.data.get('end_date'),
            'created_by': request.user.id
        }
        
        serializer = SurveySerializer(data=survey_data, context={'request': request})
        
        if serializer.is_valid():
            survey = serializer.save()
            return Response({
                'success': True,
                'data': serializer.data,
                'message': '问卷创建成功'
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'success': False,
                'error': '数据验证失败',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)


# 更新问卷视图
class SurveyUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    
    def put(self, request, survey_id):
        """
        更新问卷
        """
        print("=== 更新问卷 ===")
        print("问卷ID:", survey_id)
        print("请求数据:", request.data)
        print("当前用户:", request.user.username)
        
        survey = get_object_or_404(Survey, id=survey_id, created_by=request.user)
        
        serializer = SurveySerializer(survey, data=request.data, partial=True, context={'request': request})
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'data': serializer.data,
                'message': '问卷更新成功'
            })
        else:
            return Response({
                'success': False,
                'error': '数据验证失败',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)





# 删除问卷视图
class SurveyDeleteView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    
    def delete(self, request, survey_id):
        """
        删除问卷
        """
        print("=== 删除问卷 ===")
        print("问卷ID:", survey_id)
        print("当前用户:", request.user.username)
        
        survey = get_object_or_404(Survey, id=survey_id, created_by=request.user)
        survey_title = survey.title
        survey.delete()
        
        return Response({
            'success': True,
            'message': f'问卷 "{survey_title}" 已删除'
        })




class SurveyResponseSubmitView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request, survey_id):
        """
        提交问卷回答
        """
        print("=== 提交问卷回答 ===")
        print("问卷ID:", survey_id)
        print("请求数据:", request.data)
        print("当前用户:", request.user.username if request.user.is_authenticated else "匿名用户")
        
        try:
            # 获取问卷
            survey = get_object_or_404(Survey, id=survey_id)
            
            # 检查问卷状态
            if not survey.is_active:
                return Response({
                    'success': False,
                    'error': '该问卷已结束或尚未开始'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            answers = request.data.get('answers', {})
            is_anonymous = request.data.get('is_anonymous', False)
            
            print("接收到的答案:", answers)
            
            # 验证回答数据
            if not validate_answers(survey.questions, answers):
                return Response({
                    'success': False,
                    'error': '回答数据格式不正确或未完成必填问题'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 准备数据
            response_data = {
                'survey': survey.id,
                'answers': answers,
                'is_anonymous': is_anonymous
            }
            
            print("序列化器数据:", response_data)
            
            # 使用新的简化序列化器
            serializer = SurveyResponseSubmitSerializer(
                data=response_data,
                context={'request': request}
            )
            
            if serializer.is_valid():
                print("序列化器验证通过")
                
                try:
                    # 保存回答（包含AI评估）
                    survey_response = serializer.save()
                    
                    # 更新统计分析
                    update_survey_analysis(survey)
                    
                    # 构建响应数据
                    response_payload = {
                        'success': True,
                        'data': {
                            'id': survey_response.id,
                            'survey_id': survey_response.survey.id,
                            'submitted_at': survey_response.submitted_at,
                            'is_anonymous': survey_response.is_anonymous
                        },
                        'message': '问卷提交成功！感谢您的参与。'
                    }
                    
                    # 如果AI评估已经完成，包含评分信息
                    if survey_response.ai_score is not None:
                        response_payload['data']['ai_evaluation'] = {
                            'score': survey_response.ai_score,
                            'comment': survey_response.ai_comment,
                            'evaluated_at': survey_response.ai_evaluated_at
                        }
                        
                        # 如果评分大于60分且有注册序列号，包含序列号信息
                        if survey_response.ai_score > 70 and survey_response.registration_code:
                            response_payload['data']['registration_code'] = survey_response.registration_code
                            response_payload['message'] = f'问卷提交成功！您的评分为 {survey_response.ai_score} 分，已获得注册资格。'
                        else:
                            response_payload['message'] = '问卷提交成功！AI评估已完成。'
                    else:
                        response_payload['message'] = '问卷提交成功！评估结果稍后生成。'
                    
                    return Response(response_payload, status=status.HTTP_201_CREATED)
                    
                except serializers.ValidationError as e:
                    # 处理重复提交等验证错误
                    print("重复提交错误:", str(e))
                    error_message = str(e.detail[0]) if hasattr(e, 'detail') and e.detail else str(e)
                    return Response({
                        'success': False,
                        'error': error_message
                    }, status=status.HTTP_400_BAD_REQUEST)
                
            else:
                print("序列化器验证失败:", serializer.errors)
                return Response({
                    'success': False,
                    'error': '数据验证失败',
                    'details': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            print(f"提交问卷时发生未知错误: {str(e)}")
            import traceback
            print(f"错误堆栈: {traceback.format_exc()}")
            
            return Response({
                'success': False,
                'error': '服务器内部错误，请稍后重试'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# 问卷回答列表视图
class SurveyResponseListView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    
    def get(self, request, survey_id):
        """
        获取问卷的所有回答
        """
        print("=== 获取问卷回答列表 ===")
        print("问卷ID:", survey_id)
        print("当前用户:", request.user.username)
        
        survey = get_object_or_404(Survey, id=survey_id)
        
        # 检查权限：只有创建者或超级用户可以查看
        if not (request.user == survey.created_by or request.user.is_superuser):
            return Response({
                'success': False,
                'error': '无权查看此问卷的回答'
            }, status=status.HTTP_403_FORBIDDEN)
        
        responses = SurveyResponse.objects.filter(survey=survey)
        serializer = SurveyResponseSerializer(responses, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'count': len(serializer.data)
        })

# 问卷分析视图
class SurveyAnalysisView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    
    def get(self, request, survey_id):
        """
        获取问卷分析数据
        """
        print("=== 获取问卷分析数据 ===")
        print("问卷ID:", survey_id)
        print("当前用户:", request.user.username)
        
        survey = get_object_or_404(Survey, id=survey_id)
        
        # 检查权限
        if not (request.user == survey.created_by or request.user.is_superuser):
            return Response({
                'success': False,
                'error': '无权查看此问卷的分析数据'
            }, status=status.HTTP_403_FORBIDDEN)
        
        analysis, created = SurveyAnswerAnalysis.objects.get_or_create(survey=survey)
        serializer = SurveyAnswerAnalysisSerializer(analysis)
        
        return Response({
            'success': True,
            'data': serializer.data
        })

# 导出问卷数据视图
class SurveyExportView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    
    def get(self, request, survey_id):
        """
        导出问卷回答数据为CSV
        """
        print("=== 导出问卷数据 ===")
        print("问卷ID:", survey_id)
        print("当前用户:", request.user.username)
        
        survey = get_object_or_404(Survey, id=survey_id)
        
        # 检查权限
        if not (request.user == survey.created_by or request.user.is_superuser):
            return Response({
                'success': False,
                'error': '无权导出此问卷的数据'
            }, status=status.HTTP_403_FORBIDDEN)
        
        responses = survey.responses.all()
        
        # 生成CSV格式数据
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = f'attachment; filename="{survey.title}_responses.csv"'
        
        # 使用utf-8-sig编码以支持Excel中文显示
        response.write('\ufeff')  # BOM头，确保Excel正确显示中文
        
        writer = csv.writer(response)
        
        # 写入表头
        headers = ['提交时间', '用户', 'IP地址', '匿名']
        questions = survey.questions
        
        # 添加问题标题
        for question in questions.get('multipleChoiceQuestions', []):
            headers.append(question['text'])
        for question in questions.get('essayQuestions', []):
            headers.append(question['text'])
        
        writer.writerow(headers)
        
        # 写入数据
        for survey_response in responses:
            row = [
                survey_response.submitted_at.strftime('%Y-%m-%d %H:%M:%S'),
                survey_response.user.username if survey_response.user else '匿名用户',
                survey_response.user_ip or '',
                '是' if survey_response.is_anonymous else '否'
            ]
        
            answers = survey_response.answers
        
            # 添加选择题答案
            for question in questions.get('multipleChoiceQuestions', []):
                question_id = str(question['id'])
                answer = answers.get(question_id, '')
                if isinstance(answer, list):
                    # 将选项值转换为可读文本
                    option_texts = []
                    for option_value in answer:
                        for option in question.get('options', []):
                            if option['value'] == option_value:
                                option_texts.append(option['text'])
                                break
                    row.append(', '.join(option_texts))
                else:
                    # 查找单选答案的文本
                    option_text = ''
                    for option in question.get('options', []):
                        if option['value'] == answer:
                            option_text = option['text']
                            break
                    row.append(option_text)
        
            # 添加论述题答案
            for question in questions.get('essayQuestions', []):
                question_id = str(question['id'])
                answer = answers.get(question_id, '')
                # 限制长度，避免CSV单元格过长
                if len(answer) > 100:
                    answer = answer[:100] + '...'
                row.append(answer)
        
            writer.writerow(row)
        
        return response