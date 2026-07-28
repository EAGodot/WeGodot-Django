# blog/views.py
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from django.contrib.auth.models import User
from .models import Blog, BlogLike, BlogComment, BlogCollection, CommentLike
from .serializers import BlogListSerializer, BlogDetailSerializer, BlogCommentSerializer, BlogLikeSerializer, BlogCollectionSerializer
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q

class BlogListView(APIView):
    #permission_classes = [AllowAny]
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get(self, request):
        """
        获取博客列表 - 支持个人模式和全部模式
        """
        print("=== 获取博客列表 ===")
        print("请求参数:", dict(request.GET))
        print("当前用户:", request.user.username)
        
        try:
            # 🔥 新增：检查是否为个人模式
            my_blogs = request.GET.get('my_blogs', '').lower() == 'true'
            author_filter = request.GET.get('author', '')
            status_filter = request.GET.get('status', '')
            exclude_drafts = request.GET.get('exclude_drafts', '').lower() == 'true'
            
            print(f"模式参数 - 个人模式: {my_blogs}, 作者: {author_filter}, 状态: {status_filter}, 排除草稿: {exclude_drafts}")
            
            if my_blogs:
                # 🔥 个人模式：显示当前用户的所有文章（包括草稿）
                blogs = Blog.objects.filter(author=request.user)
                print(f"个人模式：找到 {blogs.count()} 篇用户文章")
            elif author_filter:
                # 按指定作者筛选
                blogs = Blog.objects.filter(author__username=author_filter, status='published')
                print(f"作者筛选模式：找到 {blogs.count()} 篇作者文章")
            else:
                # 🔥 默认模式：显示所有已发布的博客
                blogs = Blog.objects.filter(status='published')
                print(f"全部模式：找到 {blogs.count()} 篇已发布博客")
            
            # 状态筛选
            if status_filter:
                blogs = blogs.filter(status=status_filter)
                print(f"状态筛选后: {blogs.count()} 个结果")
            
            # 排除草稿（仅在个人模式下有效）
            if exclude_drafts and my_blogs:
                blogs = blogs.exclude(status='draft')
                print(f"排除草稿后: {blogs.count()} 个结果")
            
            # 🔥 修复：支持多种搜索参数名称
            search_query = request.GET.get('q') or request.GET.get('search') or request.GET.get('query')
            category = request.GET.get('category', '')
            tag = request.GET.get('tag', '')
            featured = request.GET.get('featured', '')
            
            print(f"搜索参数 - 关键词: {search_query}, 分类: {category}, 标签: {tag}")
            
            # 关键词搜索（支持标题、内容、摘要）
            if search_query:
                blogs = blogs.filter(
                    Q(title__icontains=search_query) | 
                    Q(content__icontains=search_query) |
                    Q(summary__icontains=search_query)
                )
                print(f"关键词搜索后: {blogs.count()} 个结果")
            
            # 分类筛选
            if category:
                blogs = blogs.filter(category=category)
                print(f"分类筛选后: {blogs.count()} 个结果")
            
            # 标签筛选
            if tag:
                blogs = blogs.filter(tags__contains=[tag])
                print(f"标签筛选后: {blogs.count()} 个结果")
            
            if featured.lower() == 'true':
                blogs = blogs.filter(is_featured=True)
                print(f"推荐筛选后: {blogs.count()} 个结果")
            
            # 排序：已发布的按发布时间，草稿按更新时间
            if my_blogs:
                blogs = blogs.order_by('-updated_at')
            else:
                blogs = blogs.order_by('-published_at')
            
            # 分页处理
            page = request.GET.get('page', 1)
            page_size = request.GET.get('page_size', 10)
            
            try:
                page_size = int(page_size)
            except (ValueError, TypeError):
                page_size = 10
            
            paginator = Paginator(blogs, page_size)
            
            try:
                blogs_page = paginator.page(page)
            except PageNotAnInteger:
                blogs_page = paginator.page(1)
            except EmptyPage:
                blogs_page = paginator.page(paginator.num_pages)
            
            # 使用新的 BlogListSerializer
            serializer = BlogListSerializer(
                blogs_page, 
                many=True,
                context={'request': request}
            )
            
            response_data = {
                'success': True,
                'data': serializer.data,
                'pagination': {
                    'current_page': blogs_page.number,
                    'total_pages': paginator.num_pages,
                    'total_count': paginator.count,
                    'has_next': blogs_page.has_next(),
                    'has_previous': blogs_page.has_previous(),
                },
                'search_info': {
                    'query': search_query,
                    'category': category,
                    'results_count': paginator.count
                },
                'mode_info': {
                    'is_personal_mode': my_blogs,
                    'current_user': request.user.username if my_blogs else None
                }
            }
            
            print(f"✅ 搜索完成 - 模式: {'个人' if my_blogs else '全部'}, 关键词: {search_query}, 结果数: {paginator.count}")
            return Response(response_data)
            
        except Exception as e:
            print("获取博客列表异常:", str(e))
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'message': f'获取博客列表失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class BlogDetailView(APIView):
    #permission_classes = [AllowAny]
    permission_classes = [IsAuthenticated]    
    authentication_classes = [TokenAuthentication]

    def get(self, request, blog_id):
        """
        获取博客详情 - 支持查看草稿（仅作者本人）
        """
        print("=== 获取博客详情 ===")
        print("博客ID:", blog_id)
        print("当前用户:", request.user.username)
        
        try:
            # 首先尝试获取博客
            blog = Blog.objects.get(id=blog_id)
            print("找到博客:", blog.title)
            print("博客状态:", blog.status)
            print("博客作者:", blog.author.username)
            
            # 🔥 新增：权限检查
            # 如果是草稿，只有作者本人可以查看
            if blog.status == 'draft' and blog.author != request.user:
                print("❌ 无权限查看草稿")
                return Response({
                    'success': False,
                    'message': '无权限查看此草稿'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # 如果是已发布博客，增加浏览数
            if blog.status == 'published':
                blog.increment_view_count()
                print(f"浏览数更新: {blog.view_count}")
            
            # 使用 BlogDetailSerializer
            serializer = BlogDetailSerializer(
                blog,
                context={'request': request}
            )
            
            return Response({
                'success': True,
                'data': serializer.data
            })
            
        except Blog.DoesNotExist:
            print("博客不存在，ID:", blog_id)
            return Response({
                'success': False,
                'message': '博客不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print("获取博客详情异常:", str(e))
            return Response({
                'success': False,
                'message': f'获取博客详情失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 🔥 新增：个人文章管理API
class PersonalBlogsView(APIView):
    """
    个人文章管理专用API
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get(self, request):
        """
        获取个人文章统计和列表
        """
        print("=== 获取个人文章 ===")
        print("当前用户:", request.user.username)
        
        try:
            # 获取当前用户的所有文章
            user_blogs = Blog.objects.filter(author=request.user)
            
            # 统计信息
            total_count = user_blogs.count()
            published_count = user_blogs.filter(status='published').count()
            draft_count = user_blogs.filter(status='draft').count()
            
            print(f"统计信息 - 总数: {total_count}, 已发布: {published_count}, 草稿: {draft_count}")
            
            # 筛选参数
            status_filter = request.GET.get('status', '')
            search_query = request.GET.get('search', '')
            category = request.GET.get('category', '')
            
            # 状态筛选
            if status_filter:
                user_blogs = user_blogs.filter(status=status_filter)
                print(f"状态筛选后: {user_blogs.count()} 个结果")
            
            # 搜索
            if search_query:
                user_blogs = user_blogs.filter(
                    Q(title__icontains=search_query) | 
                    Q(content__icontains=search_query) |
                    Q(summary__icontains=search_query)
                )
                print(f"搜索后: {user_blogs.count()} 个结果")
            
            # 分类筛选
            if category:
                user_blogs = user_blogs.filter(category=category)
                print(f"分类筛选后: {user_blogs.count()} 个结果")
            
            # 按更新时间排序（最新的在前面）
            user_blogs = user_blogs.order_by('-updated_at')
            
            # 分页
            page = request.GET.get('page', 1)
            page_size = request.GET.get('page_size', 12)
            
            try:
                page_size = int(page_size)
            except (ValueError, TypeError):
                page_size = 12
            
            paginator = Paginator(user_blogs, page_size)
            
            try:
                blogs_page = paginator.page(page)
            except PageNotAnInteger:
                blogs_page = paginator.page(1)
            except EmptyPage:
                blogs_page = paginator.page(paginator.num_pages)
            
            # 序列化
            serializer = BlogListSerializer(
                blogs_page, 
                many=True,
                context={'request': request}
            )
            
            response_data = {
                'success': True,
                'data': serializer.data,
                'stats': {
                    'total': total_count,
                    'published': published_count,
                    'drafts': draft_count
                },
                'pagination': {
                    'current_page': blogs_page.number,
                    'total_pages': paginator.num_pages,
                    'total_count': paginator.count,
                    'has_next': blogs_page.has_next(),
                    'has_previous': blogs_page.has_previous(),
                }
            }
            
            return Response(response_data)
            
        except Exception as e:
            print("获取个人文章异常:", str(e))
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'message': f'获取个人文章失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 🔥 新增：博客状态管理API
# 🔥 修改：BlogStatusView 適配新的URL結構
class BlogStatusView(APIView):
    """
    博客狀態管理（發布/取消發布/刪除）
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def post(self, request, blog_id):
        """
        管理博客狀態
        通過URL路徑判斷操作類型
        """
        print(f"=== 博客狀態管理 ===")
        print(f"博客ID: {blog_id}")
        print(f"當前用戶: {request.user.username}")
        print(f"請求路徑: {request.path}")
        
        try:
            # 從URL路徑判斷操作類型
            if 'publish' in request.path:
                action = 'publish'
            elif 'unpublish' in request.path:
                action = 'unpublish'
            elif 'delete' in request.path:
                action = 'delete'
            else:
                return Response({
                    'success': False,
                    'message': '不支持的操作'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            print(f"檢測到操作: {action}")
            
            # 獲取博客
            blog = Blog.objects.get(id=blog_id, author=request.user)
            print(f"找到博客: {blog.title} (狀態: {blog.status})")
            
            if action == 'publish':
                # 發布博客
                if blog.status == 'draft':
                    blog.status = 'published'
                    if not blog.published_at:
                        from django.utils import timezone
                        blog.published_at = timezone.now()
                    blog.save()
                    message = '博客發布成功'
                    print("✅ 博客已發布")
                else:
                    message = '博客已經是發布狀態'
            
            elif action == 'unpublish':
                # 設為草稿
                if blog.status == 'published':
                    blog.status = 'draft'
                    blog.save()
                    message = '博客已設為草稿'
                    print("✅ 博客已設為草稿")
                else:
                    message = '博客已經是草稿狀態'
            
            elif action == 'delete':
                # 刪除博客
                blog_title = blog.title
                blog.delete()
                message = f'博客 "{blog_title}" 刪除成功'
                print("✅ 博客已刪除")
            
            return Response({
                'success': True,
                'message': message
            })
            
        except Blog.DoesNotExist:
            print("博客不存在或無權限，ID:", blog_id)
            return Response({
                'success': False,
                'message': '博客不存在或無權限'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print("博客狀態管理異常:", str(e))
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'message': f'操作失敗: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
# ... 其他视图保持不变（BlogCreateView, BlogUpdateView, BlogLikeView等）...

class BlogCreateView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        """
        创建新博客或保存草稿 - 使用新的序列化器
        """
        print("=== 创建博客请求 ===")
        print("请求数据:", request.data)
        
        try:
            data = request.data.copy()
            print("复制后的数据:", data)
            
            # 🔥 修复：优先使用前端传来的 status 字段，而不是 action
            if data.get('status') == 'published':
                data['status'] = 'published'
                print("✅ 设置为发布模式")
            else:
                # 如果没有明确设置发布状态，才设置为草稿
                data['status'] = 'draft'
                print("设置为草稿模式")
            
            print("处理后的数据:", data)
            
            # 设置作者为当前用户
            data['author'] = request.user.id
            print("设置作者:", request.user.id)
            
            # 使用 BlogDetailSerializer
            serializer = BlogDetailSerializer(
                data=data,
                context={'request': request}
            )
            print("序列化器是否有效:", serializer.is_valid())
            
            if not serializer.is_valid():
                print("=== 序列化错误 ===")
                print("错误详情:", serializer.errors)
                return Response({
                    'success': False,
                    'message': '数据验证失败',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            # 🔥 新增：检查同名博客
            try:
                title = data.get('title', '').strip()
                status_val = data.get('status', 'draft')
                
                print(f"=== 同名博客检查开始 ===")
                print(f"当前用户: {request.user} (ID: {request.user.id})")
                print(f"标题: '{title}'")
                print(f"状态: {status_val}")

                if title:
                    # 检查当前用户是否已经存在同名的博客
                    existing_blog = Blog.objects.filter(
                        title__iexact=title,
                        author=request.user
                    )
                    
                    existing_count = existing_blog.count()
                    existing_ids = list(existing_blog.values_list('id', flat=True))
                    
                    print(f"找到 {existing_count} 篇同名博客")
                    print(f"同名博客ID列表: {existing_ids}")
                    
                    if existing_blog.exists():
                        print("⚠️ 检测到同名博客，阻止保存")
                        return Response({
                            'success': False,
                            'message': '您已经发布过同名的博客，请修改标题',
                            'error_code': 'DUPLICATE_TITLE',
                            'debug_info': {
                                'existing_count': existing_count,
                                'existing_ids': existing_ids,
                                'current_title': title,
                                'current_user': request.user.id
                            }
                        }, status=status.HTTP_400_BAD_REQUEST)
                    else:
                        print("✅ 没有检测到同名博客，允许保存")                        
                else:
                    print("❓ 标题为空，跳过同名检查")
                    
                print("=== 同名博客检查结束 ===")
                
            except Exception as e:
                print("❌ 检查同名博客时出错:", str(e))
                import traceback
                traceback.print_exc()
                print("⚠️ 同名检查出错，但继续执行保存操作")

            # 保存数据
            blog = serializer.save()
            print("博客保存成功，ID:", blog.id)
            
            # 返回成功响应
            if blog.status == 'published':
                message = '博客发布成功'
            else:
                message = '草稿保存成功'
            
            return Response({
                'success': True,
                'message': message,
                'data': BlogDetailSerializer(blog, context={'request': request}).data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            print("保存异常:", str(e))
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'message': f'服务器错误: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class BlogUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def put(self, request, blog_id):
        """
        更新博客 - 使用新的序列化器
        """
        print("=== 更新博客请求 ===")
        print("博客ID:", blog_id)
        print("请求数据:", request.data)
        
        try:
            # 查找博客
            blog = Blog.objects.get(id=blog_id, author=request.user)
            print("找到博客:", blog.title)
            
        except Blog.DoesNotExist:
            print("博客不存在或无权限，ID:", blog_id)
            return Response({
                'success': False,
                'message': '博客不存在或无权限修改'
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            data = request.data.copy()
            print("复制后的更新数据:", data)
            
            # 处理发布操作
            if data.get('action') == 'publish':
                data['status'] = 'published'
                print("更新为发布状态")
            
            print("处理后的更新数据:", data)
            
            # 使用 BlogDetailSerializer 更新数据
            serializer = BlogDetailSerializer(
                blog, 
                data=data, 
                partial=True,
                context={'request': request}
            )
            print("更新序列化器是否有效:", serializer.is_valid())
            
            if not serializer.is_valid():
                print("=== 更新序列化错误 ===")
                print("错误详情:", serializer.errors)
                return Response({
                    'success': False,
                    'message': '数据验证失败',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 保存更新
            updated_blog = serializer.save()
            print("博客更新成功")
            
            # 返回响应
            message = '博客更新成功' if updated_blog.status == 'published' else '草稿更新成功'
            
            return Response({
                'success': True,
                'message': message,
                'data': BlogDetailSerializer(updated_blog, context={'request': request}).data
            })
            
        except Exception as e:
            print("更新异常:", str(e))
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'message': f'更新失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





class BlogDraftView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get(self, request):
        """
        获取草稿列表 - 使用新的序列化器
        """
        print("=== 获取草稿列表 ===")
        
        try:
            # 获取当前用户的所有草稿
            drafts = Blog.objects.filter(author=request.user, status='draft').order_by('-updated_at')
            print(f"找到 {drafts.count()} 个草稿")
            
            # 使用 BlogListSerializer
            serializer = BlogListSerializer(
                drafts, 
                many=True,
                context={'request': request}
            )
            
            return Response({
                'success': True,
                'data': serializer.data,
                'count': drafts.count()
            })
            
        except Exception as e:
            print("获取草稿列表异常:", str(e))
            return Response({
                'success': False,
                'message': f'获取草稿失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, draft_id=None):
        """
        删除草稿
        """
        print("=== 删除草稿请求 ===")
        print("草稿ID:", draft_id)
        
        try:
            if draft_id:
                # 删除单个草稿
                try:
                    draft = Blog.objects.get(id=draft_id, author=request.user, status='draft')
                    draft_title = draft.title
                    draft.delete()
                    print(f"删除草稿: {draft_title}")
                    
                    return Response({
                        'success': True,
                        'message': '草稿删除成功'
                    })
                    
                except Blog.DoesNotExist:
                    print("草稿不存在或无权限，ID:", draft_id)
                    return Response({
                        'success': False,
                        'message': '草稿不存在或无权限删除'
                    }, status=status.HTTP_404_NOT_FOUND)
            else:
                # 删除所有草稿
                drafts = Blog.objects.filter(author=request.user, status='draft')
                count = drafts.count()
                drafts.delete()
                print(f"删除所有草稿，共 {count} 个")
                
                return Response({
                    'success': True,
                    'message': f'成功删除 {count} 个草稿'
                })
                
        except Exception as e:
            print("删除草稿异常:", str(e))
            return Response({
                'success': False,
                'message': f'删除失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class BlogSearchView(APIView):
    #permission_classes = [AllowAny]  # 允许任何人搜索
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get(self, request):
        """
        搜索博客 - 增强版搜索功能
        """
        print("=== 搜索博客 ===")
        print("请求参数:", dict(request.GET))
        
        try:
            blogs = Blog.objects.filter(status='published')
            
            # 🔥 修复：支持多种搜索参数名称
            query = request.GET.get('q') or request.GET.get('search') or request.GET.get('query')
            category = request.GET.get('category', '')
            tag = request.GET.get('tag', '')
            
            print(f"搜索参数 - 关键词: {query}, 分类: {category}, 标签: {tag}")
            
            # 关键词搜索（标题、内容、摘要）
            if query:
                blogs = blogs.filter(
                    Q(title__icontains=query) | 
                    Q(content__icontains=query) |
                    Q(summary__icontains=query)
                )
                print(f"关键词搜索后: {blogs.count()} 个结果")
            
            # 分类筛选
            if category:
                blogs = blogs.filter(category=category)
                print(f"分类筛选后: {blogs.count()} 个结果")
            
            # 标签筛选
            if tag:
                blogs = blogs.filter(tags__contains=[tag])
                print(f"标签筛选后: {blogs.count()} 个结果")
            
            blogs = blogs.order_by('-published_at')
            print(f"最终搜索到 {blogs.count()} 个结果")
            
            # 分页处理
            page = request.GET.get('page', 1)
            page_size = request.GET.get('page_size', 12)
            
            try:
                page_size = int(page_size)
            except (ValueError, TypeError):
                page_size = 12
            
            paginator = Paginator(blogs, page_size)
            
            try:
                blogs_page = paginator.page(page)
            except PageNotAnInteger:
                blogs_page = paginator.page(1)
            except EmptyPage:
                blogs_page = paginator.page(paginator.num_pages)
            
            # 使用 BlogListSerializer
            serializer = BlogListSerializer(
                blogs_page, 
                many=True,
                context={'request': request}
            )
            
            response_data = {
                'success': True,
                'data': serializer.data,
                'pagination': {
                    'current_page': blogs_page.number,
                    'total_pages': paginator.num_pages,
                    'total_count': paginator.count,
                    'has_next': blogs_page.has_next(),
                    'has_previous': blogs_page.has_previous(),
                },
                'search_info': {
                    'query': query,
                    'category': category,
                    'tag': tag,
                    'results_count': paginator.count
                }
            }
            
            print(f"✅ 搜索完成 - 关键词: {query}, 结果数: {paginator.count}")
            return Response(response_data)
            
        except Exception as e:
            print("搜索博客异常:", str(e))
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'message': f'搜索失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





class BlogLikeView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def post(self, request, blog_id):
        """
        点赞/取消点赞博客
        """
        print("=== 点赞博客 ===")
        print("博客ID:", blog_id)
        
        try:
            blog = Blog.objects.get(id=blog_id, status='published')
            
            # 检查是否已经点赞
            like_exists = BlogLike.objects.filter(blog=blog, user=request.user).exists()
            
            if like_exists:
                # 取消点赞
                BlogLike.objects.filter(blog=blog, user=request.user).delete()
                message = '取消点赞成功'
                print("取消点赞")
            else:
                # 点赞
                BlogLike.objects.create(blog=blog, user=request.user)
                message = '点赞成功'
                print("点赞成功")
            
            # 获取更新后的点赞数
            blog.refresh_from_db()
            
            return Response({
                'success': True,
                'message': message,
                'like_count': blog.like_count,
                'is_liked': not like_exists  # 返回新的点赞状态
            })
            
        except Blog.DoesNotExist:
            print("博客不存在或未发布，ID:", blog_id)
            return Response({
                'success': False,
                'message': '博客不存在或未发布'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print("点赞操作异常:", str(e))
            return Response({
                'success': False,
                'message': f'操作失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class CommentLikeView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def post(self, request, comment_id):
        """
        点赞/取消点赞评论
        """
        print("=== 点赞评论 ===")
        print("评论ID:", comment_id)
        print("用户:", request.user.username if request.user else 'Anonymous')
        
        try:
            # 获取评论对象
            comment = BlogComment.objects.get(id=comment_id, is_approved=True)
            print(f"找到评论: {comment.id}, 内容: {comment.content[:20]}...")
            
            # 检查是否已经点赞
            like_exists = CommentLike.objects.filter(comment=comment, user=request.user).exists()
            print(f"点赞状态: {'已点赞' if like_exists else '未点赞'}")
            
            if like_exists:
                # 取消点赞
                like_instance = CommentLike.objects.filter(comment=comment, user=request.user).first()
                if like_instance:
                    like_instance.delete()
                    print("✅ 取消点赞成功")
                message = '取消点赞成功'
                new_like_status = False
            else:
                # 点赞
                CommentLike.objects.create(comment=comment, user=request.user)
                print("✅ 点赞成功")
                message = '点赞成功'
                new_like_status = True
            
            # 重新从数据库获取评论以更新点赞数
            comment.refresh_from_db()
            current_like_count = comment.like_count
            print(f"更新后点赞数: {current_like_count}")
            
            return Response({
                'success': True,
                'message': message,
                'like_count': current_like_count,
                'is_liked': new_like_status
            })
            
        except BlogComment.DoesNotExist:
            print(f"❌ 评论不存在或未审核通过，ID: {comment_id}")
            return Response({
                'success': False,
                'message': '评论不存在或未审核通过'
            }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            print(f"❌ 评论点赞操作异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'message': f'操作失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)






class BlogCollectionView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def post(self, request, blog_id):
        """
        收藏/取消收藏博客
        """
        print("=== 收藏博客 ===")
        print("博客ID:", blog_id)
        
        try:
            blog = Blog.objects.get(id=blog_id, status='published')
            
            # 检查是否已经收藏
            collection_exists = BlogCollection.objects.filter(blog=blog, user=request.user).exists()
            
            if collection_exists:
                # 取消收藏
                BlogCollection.objects.filter(blog=blog, user=request.user).delete()
                message = '取消收藏成功'
                print("取消收藏")
            else:
                # 收藏
                BlogCollection.objects.create(blog=blog, user=request.user)
                message = '收藏成功'
                print("收藏成功")
            
            return Response({
                'success': True,
                'message': message,
                'is_collected': not collection_exists
            })
            
        except Blog.DoesNotExist:
            print("博客不存在或未发布，ID:", blog_id)
            return Response({
                'success': False,
                'message': '博客不存在或未发布'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print("收藏操作异常:", str(e))
            return Response({
                'success': False,
                'message': f'操作失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





class CommentReplyView(APIView):
    """回复评论视图"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        """
        回复评论 - 修復用戶設置版本
        """
        print("=== 回复评论 ===")
        print("请求数据:", request.data)
        print("用户:", request.user)
        print("用户ID:", request.user.id)
        
        try:
            data = request.data.copy()
            
            # 验证必要字段
            blog_id = data.get('blog')
            parent_id = data.get('parent')
            content = data.get('content', '').strip()
            
            if not all([blog_id, parent_id, content]):
                return Response({
                    'success': False,
                    'message': '缺少必要字段: blog, parent, content'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 验证博客存在
            try:
                blog = Blog.objects.get(id=blog_id, status='published')
            except Blog.DoesNotExist:
                return Response({
                    'success': False,
                    'message': '博客不存在或未发布'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # 验证父评论存在
            try:
                parent_comment = BlogComment.objects.get(id=parent_id, blog=blog, is_approved=True)
            except BlogComment.DoesNotExist:
                return Response({
                    'success': False,
                    'message': '父评论不存在'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # 🔥 修復：手動創建評論，確保用戶正確設置
            try:
                # 直接創建評論對象，避免序列化器問題
                new_comment = BlogComment.objects.create(
                    blog=blog,
                    user=request.user,  # 🔥 明確設置用戶
                    parent=parent_comment,
                    content=content,
                    is_approved=True
                )
                
                print(f"✅ 回復創建成功，ID: {new_comment.id}")
                print(f"✅ 用戶信息: {request.user.username} (ID: {request.user.id})")
                
                # 重新獲取完整的評論數據
                new_comment_with_details = BlogComment.objects.filter(
                    id=new_comment.id
                ).select_related('user').first()
                
                if new_comment_with_details:
                    serializer = BlogCommentSerializer(
                        new_comment_with_details,
                        context={'request': request}
                    )
                    
                    return Response({
                        'success': True,
                        'message': '回复成功',
                        'data': serializer.data
                    }, status=status.HTTP_201_CREATED)
                else:
                    return Response({
                        'success': False,
                        'message': '回复创建成功但获取数据失败'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                    
            except Exception as create_error:
                print(f"❌ 創建回復時出錯: {str(create_error)}")
                import traceback
                traceback.print_exc()
                return Response({
                    'success': False,
                    'message': f'創建回復失敗: {str(create_error)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            print("回复评论异常:", str(e))
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'message': f'回复失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class BlogCommentView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get(self, request, blog_id):
        """
        获取博客评论列表 - 修复版本
        """

        print("=== 获取博客评论 - 修复版本 ===")
        print("博客ID:", blog_id)
        
        try:
            blog = Blog.objects.get(id=blog_id, status='published')
            
            # 获取顶级评论（parent为null的评论）
            top_level_comments = BlogComment.objects.filter(
                blog=blog,
                is_approved=True, 
                parent__isnull=True
            ).select_related('user').prefetch_related('replies').order_by('created_at')
            
            print(f"找到 {top_level_comments.count()} 条顶级评论")
            
            # 🔥 调试：检查评论结构
            for comment in top_level_comments:
                print(f"评论 {comment.id}:")
                direct_replies = BlogComment.objects.filter(parent=comment, is_approved=True)
                print(f"  - 直接回复数量: {direct_replies.count()}")
                
                for reply in direct_replies:
                    sub_replies = BlogComment.objects.filter(parent=reply, is_approved=True)
                    print(f"    - 回复 {reply.id} 的子回复数量: {sub_replies.count()}")
            
            # 使用修复后的序列化器
            serializer = BlogCommentSerializer(
                top_level_comments, 
                many=True,
                context={'request': request}
            )
            
            # 调试序列化后的数据
            serialized_data = serializer.data
            print("🎯 序列化后的数据结构检查:")
            
            for comment in serialized_data:
                print(f"评论 {comment['id']}:")
                print(f"  - 直接回复数量: {len(comment.get('replies', []))}")
                for reply in comment.get('replies', []):
                    print(f"    - 回复 {reply['id']} 的子回复数量: {len(reply.get('replies', []))}")
            
            return Response({
                'success': True,
                'data': serialized_data,
                'count': top_level_comments.count()
            })
            
        except Blog.DoesNotExist:
            return Response({
                'success': False,
                'message': '博客不存在或未发布'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print("获取评论异常:", str(e))
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'message': f'获取评论失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def post(self, request, blog_id):
        #发表评论
        print("=== 发表评论 ===")
        print("博客ID:", blog_id)
        print("请求数据:", request.data)
        print("用户:", request.user)
        
        try:
            blog = Blog.objects.get(id=blog_id, status='published')
            print("找到博客:", blog.title)
            
            data = request.data.copy()
            data['blog'] = blog_id
            
            print("序列化数据:", data)
            
            serializer = BlogCommentSerializer(
                data=data,
                context={'request': request}
            )
            
            if serializer.is_valid():
                print("评论数据验证通过")
                comment = serializer.save()
                print("评论保存成功，ID:", comment.id)
                
                return Response({
                    'success': True,
                    'message': '评论发表成功',
                    'data': BlogCommentSerializer(comment, context={'request': request}).data
                }, status=status.HTTP_201_CREATED)
            else:
                print("=== 评论数据验证失败 ===")
                print("错误详情:", serializer.errors)
                return Response({
                    'success': False,
                    'message': '评论数据验证失败',
                    'errors': serializer.errors,
                    'debug_info': {
                        'blog_id': blog_id,
                        'user': request.user.username,
                        'content_received': request.data.get('content')
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Blog.DoesNotExist:
            print("博客不存在或未发布，ID:", blog_id)
            return Response({
                'success': False,
                'message': '博客不存在或未发布'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print("发表评论异常:", str(e))
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'message': f'发表评论失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)