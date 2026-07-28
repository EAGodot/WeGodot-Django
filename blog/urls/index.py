from django.urls import path
from .. import views


"""
urlpatterns = [
    path('api/blogs/create/', views.BlogCreateView.as_view(), name='blog-create'),
    path('api/blogs/update/<int:blog_id>/', views.BlogUpdateView.as_view(), name='blog-update'),
    path('api/blogs/drafts/', views.BlogDraftView.as_view(), name='blog-drafts'),
    path('api/blogs/drafts/<int:draft_id>/', views.BlogDraftView.as_view(), name='blog-draft-delete'),
    # 使用简化版本先测试（不分页）
    #path('api/blogs/', views.BlogListSimpleView.as_view(), name='blog-list'),
    # 或者使用分页版本（确保导入正确后）
    path('api/blogs/', views.BlogListView.as_view(), name='blog-list'),
    # 博客详情视图
    path('api/blogs/<int:blog_id>/', views.BlogDetailView.as_view(), name='blog-detail'),
    path('api/blogs/search/', views.BlogSearchView.as_view(), name='blog-search')
]
"""
urlpatterns = [
    # 博客列表和详情
    path('api/blogs/', views.BlogListView.as_view(), name='blog-list'),
    path('api/blogs/<int:blog_id>/', views.BlogDetailView.as_view(), name='blog-detail'),
    path('api/blogs/search/', views.BlogSearchView.as_view(), name='blog-search'),
    
    # 🔥 新增：个人文章管理
    path('api/blogs/personal/', views.PersonalBlogsView.as_view(), name='personal-blogs'),
    path('api/blogs/<int:blog_id>/publish/', views.BlogStatusView.as_view(), name='blog-publish'),
    path('api/blogs/<int:blog_id>/unpublish/', views.BlogStatusView.as_view(), name='blog-unpublish'),
    path('api/blogs/<int:blog_id>/delete/', views.BlogStatusView.as_view(), name='blog-delete'),
    
    # 博客创建和编辑
    path('api/blogs/create/', views.BlogCreateView.as_view(), name='blog-create'),
    path('api/blogs/update/<int:blog_id>/', views.BlogUpdateView.as_view(), name='blog-update'),
    
    # 草稿管理
    path('api/blogs/drafts/', views.BlogDraftView.as_view(), name='blog-drafts'),
    path('api/blogs/drafts/<int:draft_id>/', views.BlogDraftView.as_view(), name='blog-draft-delete'),
    
    # 点赞功能
    path('api/blogs/<int:blog_id>/like/', views.BlogLikeView.as_view(), name='blog-like'),
    
    # 评论功能
    path('api/blogs/<int:blog_id>/comments/', views.BlogCommentView.as_view(), name='blog-comments'),
    path('api/comments/reply/', views.CommentReplyView.as_view(), name='comment-reply'),
    
    # 评论点赞功能
    path('api/comments/<int:comment_id>/like/', views.CommentLikeView.as_view(), name='comment-like'),
    
    # 收藏功能
    path('api/blogs/<int:blog_id>/collect/', views.BlogCollectionView.as_view(), name='blog-collect'),
]