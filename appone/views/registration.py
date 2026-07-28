from datetime import timedelta, datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
from appone.models.client import Client
from appone.models.code import Code
from appone.models.resource import Resource


#報錯
#NameError at /api/appone/registration/
#name 'timezone' is not defined
from django.utils import timezone
from django.contrib.auth.models import User

class RegisterView_backup(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        data = request.data
        username = data['username']
        password = data['password']
        email = data['email']
        code = data['code']


        p = data["province"]


        if not (username and password):
            return Response({'error': 'Please provide both username and password.'}, status=400)
        user_exists = User.objects.filter(username=username).exists()
        email_exists = Client.objects.filter(email=email).exists()
        if user_exists or email_exists:
            return Response({'error': '用户名或者邮箱已存在'}, status=400)
        if not email or not code:
            return Response({
                'result': "邮箱或验证码不能为空"
            })
        code_log = Code.objects.filter(email=email).order_by('-create_time')
        if code_log:
            newly_log = code_log[0]
            time = datetime.now() - timedelta(hours=0, minutes=5, seconds=0)
            if newly_log.create_time.replace(tzinfo=None) >= time:
                if newly_log.code == code:

                    #根據deepseek提示内容修改，錯誤提醒為下：
                        #IntegrityError at /api/appone/registration/
                        #(1048, "Column 'last_login' cannot be null")

                    #將下面代碼
                    #user = User.objects.create_user(username=username, password=password)
                    # 改为，並導入timezone模塊
                    user = User.objects.create_user(
                        username=username, 
                        password=password,
                        last_login=timezone.now()  # 或者根据你的需求处理
                    )

                    Client.objects.create(user=user, username=username, email=email, province=p)
                    token, created = Token.objects.get_or_create(user=user)
                    user = User.objects.filter(username=username).first()
                    client = Client.objects.get(user_id=user.id)
                    data = []
                    dataall = []
                    avatar_a = ''
                    r = Resource.objects.filter(path=client.avatar)
                    if r.exists():
                        if r[0].status:
                            avatar_a = client.avatar
                    else:
                        avatar_a = client.avatar
                    data.append({
                        'accessToken': token.key,
                        'id': client.user_id,
                        'username': client.username,
                        'phoneNumber': client.phone_number,
                        'email': client.email,
                        'admire': client.admire,
                        'userStatus': client.user_status,
                        'avatar': avatar_a,
                        'gender': client.gender,
                        'introduction': client.introduction,
                        'userType': client.user_type,
                        'createTime': client.create_time,
                        'qiniuDomain': client.qiniu_domain,
                        'qiniuBucketName': client.qiniu_bucket_name,
                        'qiniuSecretKey': client.qiniu_secret_key,
                        'qiniuAccessKey': client.qiniu_access_key,
                    })
                    dataall.append({
                        'code': 200,
                        'message': "null",
                        'data': data,
                        'currentTimeMillis': time.time(),
                    })
                    return Response({
                        'result': dataall
                    })
                else:
                    return Response({
                        'result': "验证码错误"
                    })
            else:
                return Response({
                    'result': "验证码已过期"
                })
        else:
            return Response({
                'result': "error"
            })





import time  # 添加这行导入
from survey.models import SurveyResponse  # 导入问卷回答模型
class RegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        data = request.data
        username = data.get('username', '')
        password = data.get('password', '')
        email = data.get('email', '')
        code = data.get('code', '')
        registration_code = data.get('registration_code', '')  # 新增：注册序列号
        province = data.get('province', '')

        # 验证必填字段
        if not (username and password and registration_code):
            return Response({'error': '请提供用户名、密码和注册序列号。'}, status=400)
        
        # 验证注册序列号
        if not self.validate_registration_code(registration_code):
            return Response({'error': '注册序列号无效或已被使用。'}, status=400)
        
        # 检查用户名和邮箱是否已存在
        user_exists = User.objects.filter(username=username).exists()
        email_exists = Client.objects.filter(email=email).exists()
        if user_exists or email_exists:
            return Response({'error': '用户名或者邮箱已存在'}, status=400)
        
        # 验证邮箱和验证码
        if not email or not code:
            return Response({
                'result': "邮箱或验证码不能为空"
            })
        
        code_log = Code.objects.filter(email=email).order_by('-create_time')
        if code_log:
            newly_log = code_log[0]
            time_threshold = datetime.now() - timedelta(hours=0, minutes=5, seconds=0)
            if newly_log.create_time.replace(tzinfo=None) >= time_threshold:
                if newly_log.code == code:
                    # 创建用户
                    user = User.objects.create_user(
                        username=username, 
                        password=password,
                        last_login=timezone.now()
                    )
                    
                    # 创建客户端信息，保存注册序列号
                    client = Client.objects.create(
                        user=user, 
                        username=username, 
                        email=email, 
                        province=province,
                        registration_code=registration_code,  # 保存序列号
                        code_used_at=timezone.now()  # 记录使用时间
                    )
                    
                    # 更新问卷回答中的序列号状态
                    self.update_survey_response_code(registration_code, user)
                    
                    # 生成token和返回数据
                    token, created = Token.objects.get_or_create(user=user)
                    user = User.objects.filter(username=username).first()
                    client = Client.objects.get(user_id=user.id)
                    data = []
                    dataall = []
                    avatar_a = ''
                    r = Resource.objects.filter(path=client.avatar)
                    if r.exists():
                        if r[0].status:
                            avatar_a = client.avatar
                    else:
                        avatar_a = client.avatar
                    data.append({
                        'accessToken': token.key,
                        'id': client.user_id,
                        'username': client.username,
                        'phoneNumber': client.phone_number,
                        'email': client.email,
                        'admire': client.admire,
                        'userStatus': client.user_status,
                        'avatar': avatar_a,
                        'gender': client.gender,
                        'introduction': client.introduction,
                        'userType': client.user_type,
                        'createTime': client.create_time,
                        'qiniuDomain': client.qiniu_domain,
                        'qiniuBucketName': client.qiniu_bucket_name,
                        'qiniuSecretKey': client.qiniu_secret_key,
                        'qiniuAccessKey': client.qiniu_access_key,
                        'registrationCode': client.registration_code,  # 返回序列号信息
                    })
                    dataall.append({
                        'code': 200,
                        'message': "null",
                        'data': data,
                        'currentTimeMillis': time.time(),
                    })
                    return Response({
                        'result': dataall
                    })
                else:
                    return Response({
                        'result': "验证码错误"
                    })
            else:
                return Response({
                    'result': "验证码已过期"
                })
        else:
            return Response({
                'result': "error"
            })
    
    def validate_registration_code(self, registration_code):
        """
        验证注册序列号是否有效
        """
        try:
            # 检查序列号是否存在且未被使用
            survey_response = SurveyResponse.objects.filter(
                registration_code=registration_code,
                code_used=False  # 确保序列号未被使用
            ).first()
            
            if survey_response:
                # 检查序列号是否已过期（可选，根据需求设置过期时间）
                # 这里可以添加过期时间检查逻辑
                return True
            return False
        except Exception:
            return False
    
    def update_survey_response_code(self, registration_code, user):
        """
        更新问卷回答中的序列号状态
        """
        try:
            survey_response = SurveyResponse.objects.filter(
                registration_code=registration_code
            ).first()
            
            if survey_response:
                survey_response.code_used = True
                survey_response.used_by_user = user
                survey_response.used_at = timezone.now()
                survey_response.save()
                return True
            return False
        except Exception as e:
            print(f"更新序列号状态失败: {str(e)}")
            return False


