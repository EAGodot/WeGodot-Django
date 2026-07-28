from django.urls import path
from .. import views

urlpatterns = [

    # 预览相关URL
    path('survey/preview/<int:survey_id>/', views.survey_preview, name='survey-preview'),
    path('survey/preview/<int:survey_id>/submit/', views.submit_survey_preview, name='survey-preview-submit'),
  
  
    # 新增：获取最新活跃问卷
    path('api/surveys/latest-active/', views.LatestActiveSurveyView.as_view(), name='latest-active-survey'),  
  
    # 问卷配置路由
    path('api/surveys/<int:survey_id>/config/', views.SurveyConfigView.as_view(), name='survey-config'),
    

    # 问卷管理
    path('api/surveys/list/', views.SurveyListView.as_view(), name='survey-list'),
    path('api/surveys/detail/<int:survey_id>/', views.SurveyDetailView.as_view(), name='survey-detail'),
    path('api/surveys/create/', views.SurveyCreateView.as_view(), name='survey-create'),
    path('api/surveys/update/<int:survey_id>/', views.SurveyUpdateView.as_view(), name='survey-update'),
    path('api/surveys/delete/<int:survey_id>/', views.SurveyDeleteView.as_view(), name='survey-delete'),
    
    # 问卷回答
    path('api/surveys/<int:survey_id>/submit/', views.SurveyResponseSubmitView.as_view(), name='survey-submit'),
    path('api/surveys/<int:survey_id>/responses/', views.SurveyResponseListView.as_view(), name='survey-responses'),
    
    # 数据分析
    path('api/surveys/<int:survey_id>/analysis/', views.SurveyAnalysisView.as_view(), name='survey-analysis'),
    path('api/surveys/<int:survey_id>/export/', views.SurveyExportView.as_view(), name='survey-export'),
]















