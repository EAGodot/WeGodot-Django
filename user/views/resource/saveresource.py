# Create your views here.
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAdminUser
from appone.models.label import Label
from appone.models.resource import Resource

#deepseek支持
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication, SessionAuthentication  # 添加SessionAuthenticatio
# user/views/resource/saveresource_simple.py
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from appone.models.resource import Resource

class SaveResourceView(APIView):
    """
    完全無認證的資源保存視圖
    """
    # 明確設置為空列表，禁用所有認證
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        print("🎯 SaveResourceView 被調用 - 無認證版本!")
        
        try:
            data = request.data
            print("📦 接收到的數據:", data)
            
            user_id = data.get('id')
            if not user_id:
                return Response({
                    'result': "failure",
                    'message': "缺少用戶ID"
                }, status=status.HTTP_400_BAD_REQUEST)

            user = User.objects.filter(id=user_id).first()
            if not user:
                return Response({
                    'result': "failure", 
                    'message': f"用戶ID {user_id} 不存在"
                }, status=status.HTTP_404_NOT_FOUND)
            
            file_type = data.get('type', '')
            file_path = data.get('path', '')
            file_size = data.get('size', 0)
            mime_type = data.get('mimeType', '')
            
            # 驗證必需字段
            missing_fields = []
            if not file_type: missing_fields.append('type')
            if not file_path: missing_fields.append('path') 
            if not file_size: missing_fields.append('size')
            if not mime_type: missing_fields.append('mimeType')
            
            if missing_fields:
                return Response({
                    'result': "failure",
                    'message': f"缺少必填字段: {', '.join(missing_fields)}"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 檢查是否已存在相同路徑的記錄
            existing_resource = Resource.objects.filter(path=file_path).first()
            if existing_resource:
                print(f"⚠️ 資源已存在，使用現有記錄 ID: {existing_resource.id}")
                return Response({
                    'result': "success", 
                    'message': "資源已存在",
                    'resource_id': existing_resource.id,
                    'user_id': user.id,
                    'file_path': file_path
                }, status=status.HTTP_200_OK)
            
            # 創建資源記錄
            resource = Resource.objects.create(
                type=file_type,
                path=file_path,
                size=file_size,
                mime_type=mime_type,
                user_id=user
            )
            
            print(f"✅ 資源保存成功! ID: {resource.id}, 用戶: {user.username}, 路徑: {file_path}")
            
            return Response({
                'result': "success",
                'message': "資源保存成功",
                'resource_id': resource.id,
                'user_id': user.id,
                'file_path': file_path
            }, status=status.HTTP_201_CREATED)

        except Exception as error:
            print(f"❌ 保存資源錯誤: {error}")
            import traceback
            traceback.print_exc()
            return Response({
                'result': "failure",
                'message': f"服務器錯誤: {str(error)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)







#被deepseek替換掉
class SaveResourceViewBackup(APIView):
    #permission_classes = [IsAdminUser]
    #authentication_classes = [TokenAuthentication]

    def post(self, request):
        try:
            data = request.data
            id = data['id']
            type = data['type']
            path = data['path']
            size = data['size']
            mime_type = data['mimeType']
            user = User.objects.filter(id=id).first()
            if user and type and path and size and mime_type:
                Resource.objects.create(type=type, path=path,
                                        size=size, mime_type=mime_type, user_id_id=id)
                return Response({
                    'result': "success",
                })
            else:
                return Response({
                    'failure': "exists null",
                })

        except Exception as error:
            return Response({
                'result': "failure {0}".format(error)
            })
            