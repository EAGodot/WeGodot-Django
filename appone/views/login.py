import time
import re
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
from appone.models.client import Client
from appone.models.resource import Resource



class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        username = request.data.get("account", "").strip()
        password = request.data.get("password", "").strip()
        province = request.data.get("province", "").strip()

        # 驗證輸入
        if not username or not password:
            return Response({"error": "用戶名和密碼不能為空"}, status=400)

        user = None
        client = None

        try:
            # 判斷是郵箱還是用戶名登錄
            email_pattern = r'^[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+){0,4}@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+){0,4}$'
            if re.match(email_pattern, username):
                # 郵箱登錄
                try:
                    client = Client.objects.get(email=username)
                    user = User.objects.filter(username=client.username).first()
                except Client.DoesNotExist:
                    return Response({"error": "該郵箱未註冊"}, status=400)
            else:
                # 用戶名登錄
                user = User.objects.filter(username=username).first()
                if user:
                    try:
                        client = Client.objects.get(user_id=user.id)
                    except Client.DoesNotExist:
                        return Response({"error": "用戶資料不完整"}, status=400)
                else:
                    return Response({"error": "用戶名或密碼錯誤"}, status=400)

            # 檢查用戶和客戶端是否存在
            if not user or not client:
                return Response({"error": "用戶名或密碼錯誤"}, status=400)

            # 檢查賬戶狀態
            if client.user_status is False or client.deleted is True:
                return Response({"result": "該賬戶已被禁用或刪除"})

            # 驗證密碼
            if user.check_password(password):
                # 更新省份信息（如果需要）
                if province and not client.province:
                    client.province = province
                    client.save()

                # 獲取或創建 token
                token, created = Token.objects.get_or_create(user=user)

                # 處理頭像
                avatar_url = ""
                if client.avatar:
                    r = Resource.objects.filter(path=client.avatar)
                    if r.exists() and r[0].status:
                        avatar_url = client.avatar
                    else:
                        avatar_url = client.avatar

                # 構建響應數據
                user_data = {
                    "accessToken": token.key,
                    "id": client.user_id,
                    "username": client.username,
                    "phoneNumber": client.phone_number,
                    "email": client.email,
                    "admire": client.admire,
                    "userStatus": client.user_status,
                    "avatar": avatar_url,
                    "gender": client.gender,
                    "introduction": client.introduction,
                    "userType": client.user_type,
                    "createTime": client.create_time,
                    'qiniuDomain': client.qiniu_domain,
                    'qiniuBucketName': client.qiniu_bucket_name,
                    'qiniuSecretKey': client.qiniu_secret_key,
                    'qiniuAccessKey': client.qiniu_access_key,
                }

                response_data = {
                    "code": 200,
                    "message": "登錄成功",
                    "data": [user_data],
                    "currentTimeMillis": int(time.time() * 1000),  # 轉換為毫秒
                }

                return Response({"result": [response_data]})

            else:
                return Response({"error": "用戶名或密碼錯誤"}, status=400)

        except Exception as e:
            # 記錄錯誤日誌
            print(f"登錄錯誤: {str(e)}")
            return Response({"error": "服務器內部錯誤，請稍後重試"}, status=500)