from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication


from appone.models.code import Code
from luntan.tools.code.code import send_code


#class CodeView(APIView):
#    permission_classes = [AllowAny]
#    authentication_classes = [TokenAuthentication]
#    # 验证码发送
#    def post(self, request):
#        data = request.data
#        email = data.get("email").strip()
#        try:
#            code = send_code(email)
#            code_upper = code.upper()
#            Code.objects.create(email=email, code=code_upper)
#            return Response({'result': "success"})
#        except Exception as error:
#            return Response({'result': "failure {0}".format(error)})


class CodeView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [TokenAuthentication]
    
    def post(self, request):
        data = request.data
        email = data.get("email", "").strip()
        
        print(f"🔍 调试信息 - 收到请求，邮箱: {email}")
        
        try:
            # 测试 send_code 函数
            print("🔄 准备调用 send_code 函数...")
            code = send_code(email)
            print(f"✅ send_code 返回的验证码: {code}")
            
            if code:
                code_upper = code.upper()
                print(f"📝 准备保存验证码到数据库: {code_upper}")
                
                # 保存到数据库
                Code.objects.create(email=email, code=code_upper)
                print("💾 验证码保存到数据库成功")
                
                return Response({'result': "success"})
            else:
                print("❌ send_code 返回了空值")
                return Response({'result': "failure send_code returned empty"})
                
        except Exception as error:
            print(f"💥 发生异常: {str(error)}")
            return Response({'result': f"failure {error}"})