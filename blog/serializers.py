# serializers.py
from rest_framework import serializers
from .models import Blog, BlogLike, BlogComment, CommentLike, BlogCollection, Tag
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class TagSerializer(serializers.ModelSerializer):
    blog_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Tag
        fields = ['id', 'name', 'description', 'blog_count', 'created_at']

class BlogListSerializer(serializers.ModelSerializer):
    """用于博客列表的序列化器（简化版）"""
    author_name = serializers.CharField(source='author.username', read_only=True)
    reading_time = serializers.ReadOnlyField()
    comment_count = serializers.ReadOnlyField()
    like_count = serializers.ReadOnlyField()
    is_draft = serializers.SerializerMethodField()
    
    class Meta:
        model = Blog
        fields = [
            'id', 'title', 'summary', 'cover_image', 'category', 'tags',
            'author', 'author_name', 'status', 'visibility', 'is_featured',
            'view_count', 'like_count', 'comment_count', 'reading_time',
            'is_draft', 'created_at', 'updated_at', 'published_at'
        ]
        read_only_fields = [
            'created_at', 'updated_at', 'published_at', 'view_count',
            'like_count', 'comment_count', 'reading_time', 'is_draft'
        ]
    
    def get_is_draft(self, obj):
        """检查是否为草稿"""
        return obj.status == 'draft'

class BlogDetailSerializer(serializers.ModelSerializer):
    """用于博客详情的序列化器（完整版）"""
    author_info = UserSerializer(source='author', read_only=True)
    author_name = serializers.CharField(source='author.username', read_only=True)
    author_email = serializers.EmailField(source='author.email', read_only=True)
    author_full_name = serializers.SerializerMethodField()
    reading_time = serializers.ReadOnlyField()
    is_liked = serializers.SerializerMethodField()
    is_collected = serializers.SerializerMethodField()
    is_draft = serializers.SerializerMethodField()
    is_author = serializers.SerializerMethodField()
    
    class Meta:
        model = Blog
        fields = [
            'id', 'title', 'summary', 'content', 'cover_image', 'category', 'tags',
            'author', 'author_info', 'author_name', 'author_email', 'author_full_name',
            'status', 'visibility', 'is_featured', 'view_count', 'like_count', 
            'comment_count', 'reading_time', 'is_liked', 'is_collected', 
            'is_draft', 'is_author', 'created_at', 'updated_at', 'published_at'
        ]
        read_only_fields = [
            'created_at', 'updated_at', 'published_at', 'view_count',
            'like_count', 'comment_count', 'reading_time', 'is_liked', 'is_collected',
            'author_info', 'author_name', 'author_email', 'author_full_name',
            'is_draft', 'is_author'
        ]
    
    def get_author_full_name(self, obj):
        """获取作者全名"""
        if obj.author.first_name and obj.author.last_name:
            return f"{obj.author.first_name} {obj.author.last_name}"
        elif obj.author.first_name:
            return obj.author.first_name
        else:
            return obj.author.username
    
    def get_is_draft(self, obj):
        """检查是否为草稿"""
        return obj.status == 'draft'
    
    def get_is_author(self, obj):
        """检查当前用户是否是作者"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.author == request.user
        return False
    
    def get_is_liked(self, obj):
        """检查当前用户是否点赞了该博客"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return BlogLike.objects.filter(blog=obj, user=request.user).exists()
        return False
    
    def get_is_collected(self, obj):
        """检查当前用户是否收藏了该博客"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return BlogCollection.objects.filter(blog=obj, user=request.user).exists()
        return False
    
    def create(self, validated_data):
        """创建博客时的处理"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['author'] = request.user
        
        # 如果状态是发布，确保发布时间被设置
        if validated_data.get('status') == 'published' and not validated_data.get('published_at'):
            from django.utils import timezone
            validated_data['published_at'] = timezone.now()
        
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """更新博客时的处理"""
        # 如果状态从草稿改为发布，设置发布时间
        if (instance.status == 'draft' and 
            validated_data.get('status') == 'published' and 
            not instance.published_at):
            from django.utils import timezone
            validated_data['published_at'] = timezone.now()
        
        return super().update(instance, validated_data)

# ... 其他序列化器保持不变 ...





# serializers.py - 修复 BlogCommentSerializer

class BlogCommentSerializer(serializers.ModelSerializer):
    user_info = UserSerializer(source='user', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    user_full_name = serializers.SerializerMethodField()
    user_avatar = serializers.SerializerMethodField()
    reply_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    parent_info = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()
    can_reply = serializers.SerializerMethodField()
    
    class Meta:
        model = BlogComment
        fields = [
            'id', 'blog', 'user', 'user_info', 'user_name', 'user_full_name',
            'user_avatar', 'parent', 'parent_info', 'content', 'like_count', 
            'is_approved', 'reply_count', 'is_liked', 'replies', 'can_reply', 
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'created_at', 'updated_at', 'like_count', 'is_approved',
            'reply_count', 'is_liked', 'user_info', 'user_name', 
            'user_full_name', 'user', 'user_avatar'
        ]
        extra_kwargs = {
            'user': {'required': False}
        }
    
    def get_user_full_name(self, obj):
        """获取用户全名"""
        if obj.user.first_name and obj.user.last_name:
            return f"{obj.user.first_name} {obj.user.last_name}"
        elif obj.user.first_name:
            return obj.user.first_name
        else:
            return obj.user.username
    
    def get_user_avatar(self, obj):
        """🔥 修复：使用Client模型中的真实头像"""
        request = self.context.get('request')
        
        try:
            # 导入Client模型
            from appone.models.client import Client
            
            # 查找对应的Client记录
            client = Client.objects.filter(user=obj.user).first()
            
            if client and client.avatar:
                # 如果有真实头像，返回完整URL
                print(f"✅ 評論者頭像路徑: {client.avatar}")
                if request:
                    return request.build_absolute_uri(client.avatar)
                return client.avatar
            
            # 如果没有Client记录或没有头像，使用默认头像
            name = obj.user.get_full_name() or obj.user.username
            return f"https://ui-avatars.com/api/?name={name}&background=667eea&color=fff&size=64"
            
        except Exception as e:
            print(f"❌ 获取用户头像失败: {str(e)}")
            # 返回默认头像
            name = obj.user.username if obj.user else 'User'
            return f"https://ui-avatars.com/api/?name={name}&background=667eea&color=fff&size=64"
    
    def get_reply_count(self, obj):
        """获取回复数量"""
        return obj.replies.count()
    
    def get_is_liked(self, obj):
        """检查当前用户是否点赞了该评论"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return CommentLike.objects.filter(comment=obj, user=request.user).exists()
        return False
    
    def get_parent_info(self, obj):
        """获取父评论信息"""
        if obj.parent:
            return {
                'id': obj.parent.id,
                'user_name': obj.parent.user.username,
                'user_full_name': self.get_user_full_name(obj.parent),
                'user_avatar': self.get_user_avatar(obj.parent),
                'content': obj.parent.content,
                'created_at': obj.parent.created_at
            }
        return None
    
    def get_replies(self, obj):
        """🔥 修复：正确获取子评论列表"""
        try:
            print(f"🔍 BlogCommentSerializer 获取评论 {obj.id} 的回复...")
            
            # 获取直接回复（第一级子评论）
            replies = BlogComment.objects.filter(
                parent=obj, 
                is_approved=True
            ).select_related('user').order_by('created_at')
            
            actual_count = replies.count()
            print(f"✅ 评论 {obj.id} 的直接回复数量: {actual_count}")
            
            # 🔥 修复：递归序列化所有层级的回复
            serialized_replies = []
            for reply in replies:
                # 对每个回复使用相同的序列化器，确保嵌套结构正确
                reply_data = BlogCommentSerializer(
                    reply, 
                    context=self.context
                ).data
                serialized_replies.append(reply_data)
            
            print(f"🎯 评论 {obj.id} 序列化后的回复数量: {len(serialized_replies)}")
            
            return serialized_replies
            
        except Exception as e:
            print(f"❌ 获取评论 {obj.id} 的回复时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_can_reply(self, obj):
        """检查是否可以回复此评论"""
        request = self.context.get('request')
        return request and request.user.is_authenticated
    
    def create(self, validated_data):
        """创建评论时的处理"""
        request = self.context.get('request')
        print(f"🔍 序列化器创建评论，用户: {request.user if request else 'None'}")
        
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
            print(f"✅ 设置用户: {request.user.username} (ID: {request.user.id})")
        else:
            print("❌ 用户未认证或请求为空")
            raise serializers.ValidationError("用户未认证")
        
        validated_data['is_approved'] = True
        
        try:
            result = super().create(validated_data)
            print(f"✅ 评论创建成功，ID: {result.id}")
            return result
        except Exception as e:
            print(f"❌ 评论创建失败: {str(e)}")
            raise


class BlogLikeSerializer(serializers.ModelSerializer):
    """博客点赞序列化器"""
    user_info = UserSerializer(source='user', read_only=True)
    
    class Meta:
        model = BlogLike
        fields = ['id', 'blog', 'user', 'user_info', 'created_at']
        read_only_fields = ['created_at']
    
    def create(self, validated_data):
        """创建点赞时的处理"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
        
        # 检查是否已经点赞
        blog = validated_data['blog']
        user = validated_data['user']
        if BlogLike.objects.filter(blog=blog, user=user).exists():
            raise serializers.ValidationError("您已经点赞过这篇博客了")
        
        return super().create(validated_data)

class CommentLikeSerializer(serializers.ModelSerializer):
    """评论点赞序列化器"""
    user_info = UserSerializer(source='user', read_only=True)
    
    class Meta:
        model = CommentLike
        fields = ['id', 'comment', 'user', 'user_info', 'created_at']
        read_only_fields = ['created_at']
    
    def create(self, validated_data):
        """创建评论点赞时的处理"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
        
        # 检查是否已经点赞
        comment = validated_data['comment']
        user = validated_data['user']
        if CommentLike.objects.filter(comment=comment, user=user).exists():
            raise serializers.ValidationError("您已经点赞过这条评论了")
        
        return super().create(validated_data)





class BlogCollectionSerializer(serializers.ModelSerializer):
    """博客收藏序列化器"""
    user_info = UserSerializer(source='user', read_only=True)
    blog_info = BlogListSerializer(source='blog', read_only=True)
    
    class Meta:
        model = BlogCollection
        fields = ['id', 'blog', 'blog_info', 'user', 'user_info', 'created_at']
        read_only_fields = ['created_at']
    
    def create(self, validated_data):
        """创建收藏时的处理"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
        
        # 检查是否已经收藏
        blog = validated_data['blog']
        user = validated_data['user']
        if BlogCollection.objects.filter(blog=blog, user=user).exists():
            raise serializers.ValidationError("您已经收藏过这篇博客了")
        
        return super().create(validated_data)





class BlogStatsSerializer(serializers.Serializer):
    """博客统计信息序列化器"""
    total_blogs = serializers.IntegerField()
    published_blogs = serializers.IntegerField()
    total_views = serializers.IntegerField()
    total_likes = serializers.IntegerField()
    total_comments = serializers.IntegerField()
    average_reading_time = serializers.FloatField()

# 向后兼容的别名
BlogSerializer = BlogDetailSerializer