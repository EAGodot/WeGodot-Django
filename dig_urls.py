# detailed_diagnose.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'My-Blog-ServeOpen.settings')
django.setup()

from django.urls import get_resolver, Resolver404
from django.core.handlers.wsgi import WSGIHandler
from django.conf import settings

def detailed_diagnosis():
    print("=== 详细路由诊断 ===")
    
    # 获取完整的URL解析器
    resolver = get_resolver()
    
    test_paths = [
        '/admin/',
        '/admin/login/',
        '/api/user/login/',
        '/',
        '/any-other-path/'
    ]
    
    for path in test_paths:
        print(f"\n--- 测试路径: {path} ---")
        try:
            match = resolver.resolve(path)
            print(f"✅ 匹配成功!")
            print(f"   视图: {match.func}")
            print(f"   参数: {match.kwargs}")
            print(f"   应用: {match.app_name}")
            print(f"   命名空间: {match.namespace}")
            
            # 检查视图函数详情
            if hasattr(match.func, 'view_class'):
                print(f"   视图类: {match.func.view_class}")
            if hasattr(match.func, '__name__'):
                print(f"   函数名: {match.func.__name__}")
                
        except Resolver404:
            print(f"❌ 无匹配路由")
    
    print(f"\n=== URL配置详情 ===")
    # 遍历所有URL模式
    for pattern in resolver.url_patterns:
        print(f"模式: {pattern.pattern}")
        if hasattr(pattern, 'url_patterns'):  # 包含其他URL配置
            print(f"  包含 {len(pattern.url_patterns)} 个子模式")
            for sub_pattern in pattern.url_patterns[:3]:  # 只显示前3个
                print(f"    └─ {sub_pattern.pattern}")

if __name__ == '__main__':
    detailed_diagnosis()