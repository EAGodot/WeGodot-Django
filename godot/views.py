from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from .models import MarkdownDocument



import os
from django.conf import settings



# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
import os
import time
from django.conf import settings


class MarkdownImage(APIView):
    """
    获取故事配图
    从 media 文件夹下获取固定的一张图片
    """
    permission_classes = [AllowAny]
    
    # 图片文件名（根据您 media 文件夹下的实际文件名修改）
    IMAGE_FILENAME = 'signal_table.png'  # 请修改为您的实际图片文件名
    
    def get(self, request):
        """
         获取固定故事配图
         返回格式：
         {
             'success': True,
             'data': {
                 'image_url': 'http://xxx/media/story_image.jpg',
                 'filename': 'story_image.jpg',
                 'alt': '图片描述'
             }
         }
        """
        print("=== 获取故事配图 ===")
        print("请求用户:", request.user.username if request.user.is_authenticated else "匿名用户")
        
        try:
            # 构建图片的完整路径
            image_path = os.path.join(settings.MEDIA_ROOT, self.IMAGE_FILENAME)
            
            # 检查图片文件是否存在
            if not os.path.exists(image_path):
                print(f"图片文件不存在: {image_path}")
                return Response({
                    'success': False,
                    'error': '图片文件不存在'
                }, status=status.HTTP_404_NOT_FOUND)
            
            
            
            # 获取文件修改时间（用于破坏缓存）
            file_mtime = os.path.getmtime(image_path)            
            
            # 构建带时间戳的图片URL
            image_url = self.get_image_url(request, file_mtime)            

                        
            print(f"返回图片: {self.IMAGE_FILENAME}")
            print(f"图片URL: {image_url}")
           
           
            # 添加缓存控制头
            response = Response({
                'success': True,
                'data': {
                    'image_url': image_url,
                    'filename': self.IMAGE_FILENAME,
                }
            })
            
            # 设置响应头，禁用缓存
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            
            return response           
            


        except Exception as e:
            print(f"获取图片失败: {str(e)}")
            return Response({
                'success': False,
                'error': f'获取图片失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    




    def get_image_url(self, request, timestamp):
        """
        构建带时间戳的图片访问URL，破坏浏览器缓存
        """
        media_relative_path = f'{self.IMAGE_FILENAME}'
        base_url = request.build_absolute_uri(settings.MEDIA_URL + media_relative_path)
        
        # 添加时间戳参数，强制刷新缓存
        image_url = f"{base_url}?v={int(timestamp)}"
        
        return image_url        



class RunManageLog(APIView):
    """
    获取运行日志
    从 media 文件夹下读取 run_manage.log 文件内容
    """
    permission_classes = [AllowAny]
    
    LOG_FILENAME = 'run_manage.log'
    
    def get(self, request):
        """
        获取日志文件内容
        返回格式：
        {
            'success': True,
            'data': {
                'content': '日志内容...',
                'filename': 'run_manage.log',
                'size': 1234,
                'last_modified': '2024-01-01 12:00:00'
            }
        }
        """
        print("=== 获取运行日志 ===")
        
        try:
            log_path = os.path.join(settings.MEDIA_ROOT, self.LOG_FILENAME)
            
            if not os.path.exists(log_path):
                return Response({
                    'success': False,
                    'error': '日志文件不存在',
                    'data': {
                        'content': '日志文件尚未生成，请等待策略运行。',
                        'filename': self.LOG_FILENAME,
                    }
                }, status=status.HTTP_404_NOT_FOUND)
            
            # 读取日志文件内容，限制最大读取行数防止过大
            max_lines = 1000
            lines = []
            try:
                with open(log_path, 'r', encoding='utf-8') as f:
                    for i, line in enumerate(f):
                        if i >= max_lines:
                            lines.append(f'\n... 已截断，仅显示最后 {max_lines} 行 ...')
                            break
                        lines.append(line)
            except UnicodeDecodeError:
                with open(log_path, 'r', encoding='gbk') as f:
                    for i, line in enumerate(f):
                        if i >= max_lines:
                            lines.append(f'\n... 已截断，仅显示最后 {max_lines} 行 ...')
                            break
                        lines.append(line)
            
            content = ''.join(lines)
            file_size = os.path.getsize(log_path)
            file_mtime = os.path.getmtime(log_path)
            last_modified = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(file_mtime))
            
            response = Response({
                'success': True,
                'data': {
                    'content': content,
                    'filename': self.LOG_FILENAME,
                    'size': file_size,
                    'last_modified': last_modified,
                }
            })
            
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            
            return response
            
        except Exception as e:
            print(f"获取日志失败: {str(e)}")
            return Response({
                'success': False,
                'error': f'获取日志失败: {str(e)}',
                'data': {
                    'content': f'读取日志失败: {str(e)}',
                    'filename': self.LOG_FILENAME,
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

    

    def get_image_url(self, request, timestamp):
        """
        构建带时间戳的图片访问URL，破坏浏览器缓存
        """
        media_relative_path = f'{self.IMAGE_FILENAME}'
        base_url = request.build_absolute_uri(settings.MEDIA_URL + media_relative_path)
        
        # 添加时间戳参数，强制刷新缓存
        image_url = f"{base_url}?v={int(timestamp)}"
        
        return image_url        

    
 









class MarkdownListView(APIView):
    """
    获取Markdown文档列表
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """
        获取Markdown文档列表
        GET参数：preview_only - 是否只返回可预览的文档
        """
        print("=== 获取Markdown文档列表 ===")
        print("请求用户:", request.user.username if request.user.is_authenticated else "匿名用户")
        print("GET参数:", request.GET)
        
        try:
            preview_only = request.GET.get('preview_only', 'true').lower() == 'true'
            
            if preview_only:
                documents = MarkdownDocument.objects.filter(is_previewable=True)
            else:
                documents = MarkdownDocument.objects.all()
            
            data = []
            for doc in documents:
                data.append({
                    'id': doc.id,
                    'title': doc.title,
                    'description': doc.description,
                    'is_previewable': doc.is_previewable,
                    'created_at': doc.created_at.isoformat(),
                    'updated_at': doc.updated_at.isoformat(),
                    'file_size': doc.file_size,
                    'file_url': request.build_absolute_uri(doc.file.url) if doc.file else None
                })
            
            print(f"返回 {len(data)} 个文档")
            return Response({
                'success': True,
                'data': data,
                'count': len(data)
            })
        
        except Exception as e:
            print(f"获取文档列表失败: {str(e)}")
            return Response({
                'success': False,
                'error': f'获取文档列表失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class MarkdownDetailView(APIView):
    """
    获取Markdown文档详情
    """
    permission_classes = [AllowAny]
    
    def get(self, request, doc_id):
        """
        获取Markdown文档详情
        """
        print("=== 获取Markdown文档详情 ===")
        print("文档ID:", doc_id)
        print("请求用户:", request.user.username if request.user.is_authenticated else "匿名用户")
        
        try:
            document = get_object_or_404(MarkdownDocument, id=doc_id)
            
            # 检查预览权限
            if not document.is_previewable:
                print(f"文档 {doc_id} 不允许预览")
                return Response({
                    'success': False,
                    'error': '此文档不允许预览',
                    'document_id': document.id,
                    'title': document.title
                }, status=status.HTTP_403_FORBIDDEN)
            
            content = document.get_file_content()
            
            data = {
                'id': document.id,
                'title': document.title,
                'description': document.description,
                'content': content,
                'is_previewable': document.is_previewable,
                'created_at': document.created_at.isoformat(),
                'updated_at': document.updated_at.isoformat(),
                'file_size': document.file_size,
                'file_url': request.build_absolute_uri(document.file.url) if document.file else None,
                'file_extension': document.get_file_extension()
            }
            
            print(f"成功返回文档详情: {document.title}")
            return Response({
                'success': True,
                'data': data
            })
        
        except MarkdownDocument.DoesNotExist:
            print(f"文档不存在: {doc_id}")
            return Response({
                'success': False,
                'error': '文档不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"获取文档详情失败: {str(e)}")
            return Response({
                'success': False,
                'error': f'获取文档详情失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class MarkdownContentView(APIView):
    """
    仅获取Markdown文档内容
    """
    permission_classes = [AllowAny]
    
    def get(self, request, doc_id):
        """
        仅获取Markdown文档内容
        """
        print("=== 获取Markdown文档内容 ===")
        print("文档ID:", doc_id)
        print("请求用户:", request.user.username if request.user.is_authenticated else "匿名用户")
        
        try:
            document = get_object_or_404(MarkdownDocument, id=doc_id)
            
            # 检查预览权限
            if not document.is_previewable:
                print(f"文档 {doc_id} 不允许预览")
                return Response({
                    'success': False,
                    'error': '此文档不允许预览'
                }, status=status.HTTP_403_FORBIDDEN)
            
            content = document.get_file_content()
            
            print(f"成功返回文档内容: {document.title}")
            return Response({
                'success': True,
                'data': {
                    'id': document.id,
                    'title': document.title,
                    'content': content
                }
            })
        
        except MarkdownDocument.DoesNotExist:
            print(f"文档不存在: {doc_id}")
            return Response({
                'success': False,
                'error': '文档不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"获取文档内容失败: {str(e)}")
            return Response({
                'success': False,
                'error': f'获取文档内容失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class MarkdownCreateView(APIView):
    """
    创建新的Markdown文档
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        创建新的Markdown文档
        """
        print("=== 创建Markdown文档 ===")
        print("请求用户:", request.user.username)
        print("请求数据:", request.data)
        print("请求文件:", request.FILES)
        
        try:
            # 处理文件上传
            if 'file' not in request.FILES:
                print("未找到文件")
                return Response({
                    'success': False,
                    'error': '请选择要上传的Markdown文件'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            file = request.FILES['file']
            title = request.data.get('title', file.name)
            description = request.data.get('description', '')
            is_previewable = request.data.get('is_previewable', 'true').lower() == 'true'
            
            # 创建文档
            document = MarkdownDocument(
                title=title,
                description=description,
                file=file,
                is_previewable=is_previewable
            )
            document.save()
            
            print(f"文档创建成功: {document.title} (ID: {document.id})")
            return Response({
                'success': True,
                'message': '文档创建成功',
                'data': {
                    'id': document.id,
                    'title': document.title,
                    'file_url': request.build_absolute_uri(document.file.url),
                    'created_at': document.created_at.isoformat()
                }
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            print(f"创建文档失败: {str(e)}")
            return Response({
                'success': False,
                'error': f'创建文档失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class MarkdownUpdateView(APIView):
    """
    更新Markdown文档
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, doc_id):
        """
        更新Markdown文档
        """
        print("=== 更新Markdown文档 ===")
        print("文档ID:", doc_id)
        print("请求用户:", request.user.username)
        print("请求数据:", request.data)
        print("请求文件:", request.FILES)
        
        try:
            document = get_object_or_404(MarkdownDocument, id=doc_id)
            
            # 更新字段
            if 'title' in request.data:
                document.title = request.data['title']
            if 'description' in request.data:
                document.description = request.data['description']
            if 'is_previewable' in request.data:
                document.is_previewable = request.data['is_previewable'].lower() == 'true'
            
            # 处理文件更新
            if 'file' in request.FILES:
                document.file = request.FILES['file']
            
            document.save()
            
            print(f"文档更新成功: {document.title} (ID: {document.id})")
            return Response({
                'success': True,
                'message': '文档更新成功',
                'data': {
                    'id': document.id,
                    'title': document.title,
                    'is_previewable': document.is_previewable,
                    'updated_at': document.updated_at.isoformat()
                }
            })
        
        except MarkdownDocument.DoesNotExist:
            print(f"文档不存在: {doc_id}")
            return Response({
                'success': False,
                'error': '文档不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"更新文档失败: {str(e)}")
            return Response({
                'success': False,
                'error': f'更新文档失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class MarkdownDeleteView(APIView):
    """
    删除Markdown文档
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, doc_id):
        """
        删除Markdown文档
        """
        print("=== 删除Markdown文档 ===")
        print("文档ID:", doc_id)
        print("请求用户:", request.user.username)
        
        try:
            document = get_object_or_404(MarkdownDocument, id=doc_id)
            
            # 保存文档信息用于响应
            doc_info = {
                'id': document.id,
                'title': document.title
            }
            
            document.delete()
            
            print(f"文档删除成功: {doc_info['title']} (ID: {doc_info['id']})")
            return Response({
                'success': True,
                'message': '文档删除成功',
                'data': doc_info
            })
        
        except MarkdownDocument.DoesNotExist:
            print(f"文档不存在: {doc_id}")
            return Response({
                'success': False,
                'error': '文档不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"删除文档失败: {str(e)}")
            return Response({
                'success': False,
                'error': f'删除文档失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class MarkdownPreviewableView(APIView):
    """
    获取所有可预览的文档列表
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """
        获取所有可预览的文档列表
        """
        print("=== 获取可预览文档列表 ===")
        print("请求用户:", request.user.username if request.user.is_authenticated else "匿名用户")
        
        try:
            documents = MarkdownDocument.objects.filter(is_previewable=True)
            
            data = []
            for doc in documents:
                data.append({
                    'id': doc.id,
                    'title': doc.title,
                    'description': doc.description,
                    'created_at': doc.created_at.isoformat(),
                    'file_size': doc.file_size,
                    'file_url': request.build_absolute_uri(doc.file.url) if doc.file else None
                })
            
            print(f"返回 {len(data)} 个可预览文档")
            return Response({
                'success': True,
                'data': data,
                'count': len(data)
            })
        
        except Exception as e:
            print(f"获取可预览文档列表失败: {str(e)}")
            return Response({
                'success': False,
                'error': f'获取可预览文档列表失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)