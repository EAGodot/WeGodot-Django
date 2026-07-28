from django.urls import path
from .. import views

urlpatterns = [
    # Markdown文档管理
    path('api/markdown/image/', views.MarkdownImage.as_view(), name='markdown-image'),
    path('api/markdown/list/', views.MarkdownListView.as_view(), name='markdown-list'),
    path('api/markdown/detail/<int:doc_id>/', views.MarkdownDetailView.as_view(), name='markdown-detail'),
    path('api/markdown/content/<int:doc_id>/', views.MarkdownContentView.as_view(), name='markdown-content'),
    path('api/markdown/create/', views.MarkdownCreateView.as_view(), name='markdown-create'),
    path('api/markdown/update/<int:doc_id>/', views.MarkdownUpdateView.as_view(), name='markdown-update'),
    path('api/markdown/delete/<int:doc_id>/', views.MarkdownDeleteView.as_view(), name='markdown-delete'),
    path('api/markdown/previewable/', views.MarkdownPreviewableView.as_view(), name='markdown-previewable'),
]