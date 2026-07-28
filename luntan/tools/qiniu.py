import uuid
import io
import qiniu
from PIL import Image
from appone.models.client import Client


def upload_to_qiniu(image_file, user_id, key=None):
    try:
        client = Client.objects.get(user_id=user_id)
        access_key = client.qiniu_access_key
        secret_key = client.qiniu_secret_key
        bucket_name = client.qiniu_bucket_name
        domain = client.qiniu_domain
        # 初始化 Auth 对象
        q = qiniu.Auth(access_key=access_key, secret_key=secret_key)
        """上传图片到七牛云并返回图片 URL"""
        key = 'images/' + str(uuid.uuid1()).replace('-', '')
        _img = image_file.read()
        image = Image.open(io.BytesIO(_img))
        # 获取image的后缀名
        name = 'upfile.{0}'.format(image.format)
        image.save('./' + name)
        path = './' + name
        # 生成上传 Token，可以指定过期时间等
        token = q.upload_token(bucket=bucket_name, key=key, expires=3600)
        # 调用 put_file 方法上传图片，返回图片的哈希值和信息
        ret, info = qiniu.put_file(token, key, path)
        # 判断图片是否上传成功
        if info.status_code == 200:
            # 返回图片的访问 URL，拼接方式：http://domain/key
            return f'{domain}{ret["key"]}'
        else:
            print(info.exception())
    except Exception as e:
        print(e)


def delete_image(image_url, user_id):
    try:
        client = Client.objects.get(user_id=user_id)
        access_key = client.qiniu_access_key
        secret_key = client.qiniu_secret_key
        bucket_name = client.qiniu_bucket_name
        domain = client.qiniu_domain
        q = qiniu.Auth(access_key=access_key, secret_key=secret_key)
        bucket = qiniu.BucketManager(q)
        image_key = image_url.replace(f'{domain}', '')
        ret, info = bucket.delete(bucket_name, image_key)
        if info.status_code == 200:
            return True
        else:
            return False
    except Exception as error:
        print(error)







import os
from PIL import Image
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import InMemoryUploadedFile
from appone.models.client import Client
from appone.models.image import UserImage  # 導入新的圖片模型
# 正確導入 Django settings
from django.conf import settings



# 初始化文件存儲

# Python的執行順序：
#1. 導入 luntan.tools.qiniu 模塊
#2. 執行 qiniu.py 頂層代碼（包括fs初始化）
#3. 執行 import 語句

fs = FileSystemStorage(location=settings.MEDIA_ROOT)
# luntan/tools/qiniu.py
import uuid
import io
from PIL import Image
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import InMemoryUploadedFile

# 初始化文件存儲
fs = FileSystemStorage(location=settings.MEDIA_ROOT)

def upload_to_local(image_file, user_id):
    """
    上傳圖片到本地存儲並保存記錄到數據庫
    """
    try:
        client = Client.objects.get(user_id=user_id)        
        # 處理文件名
        original_name = image_file.name
        ext = original_name.split('.')[-1].lower()
        
        # 使用PIL處理圖片
        img = Image.open(image_file)
        
        # 轉換為RGB模式（處理PNG透明背景等問題）
        if img.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1])
            img = background
        
        # 保存到內存
        img_io = io.BytesIO()
        img.save(img_io, format='JPEG', quality=85)
        img_file_size = img_io.getbuffer().nbytes  # 獲取文件大小
        img_io.seek(0)
        
        # 生成文件名
        filename = f"{uuid.uuid4()}.jpg"
        
        # 創建InMemoryUploadedFile
        processed_file = InMemoryUploadedFile(
            img_io,
            'ImageField',
            filename,
            'image/jpeg',
            img_file_size,
            None
        )
        
        # 創建圖片記錄並提供所有必需字段
        user_image = UserImage(
            user=client.user,
            original_filename=original_name,
            file_size=img_file_size,  # 提供file_size
            mime_type='image/jpeg'    # 提供mime_type
        )
        
        # 保存圖片文件
        user_image.image.save(filename, processed_file)
        user_image.save()
        
        # 返回訪問URL
        return user_image.image.url
        
    except Exception as e:
        print(f"上傳失敗: {e}")
        import traceback
        traceback.print_exc()
        return None

def delete_local_image(image_url, user_id):
    """
    刪除本地存儲的圖片
    """
    try:
        # 導入UserImage模型
        try:
            from appone.models.image import UserImage
        except ImportError:
            from luntan.models.image import UserImage
        
        # 從URL中提取圖片路徑
        image_path = image_url.replace(settings.MEDIA_URL, '')
        
        # 查找圖片記錄
        user_image = UserImage.objects.get(
            image=image_path, 
            user_id=user_id
        )
        
        # 刪除物理文件
        if user_image.image:
            if fs.exists(user_image.image.name):
                fs.delete(user_image.image.name)
        
        # 刪除數據庫記錄
        user_image.delete()
        return True
        
    except UserImage.DoesNotExist:
        print("圖片記錄不存在")
        return False
    except Exception as error:
        print(f"刪除失敗: {error}")
        import traceback
        traceback.print_exc()
        return False





