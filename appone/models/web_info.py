from django.db import models
#deepseek已經修改默認值
class WebInfo(models.Model):
    web_name = models.CharField(max_length=16, verbose_name='网站名称', default='')
    web_title = models.CharField(max_length=512, verbose_name='网站信息', default='欢迎来到我的技术博客')
    notices = models.CharField(max_length=512, null=True, blank=True, verbose_name='公告', default='🎉 欢迎访问！网站正在建设中...')
    footer = models.CharField(max_length=256, verbose_name='页脚', default='© 2024 我的博客 · Powered by Django')
    background_image = models.CharField(max_length=256, null=True, blank=True, verbose_name='背景', default='/static/images/default-bg.jpg')
    avatar = models.CharField(max_length=256, verbose_name='头像', default='/static/images/default-avatar.png')
    random_avatar = models.TextField(null=True, blank=True, verbose_name='随机头像', default='/static/images/avatar1.jpg,/static/images/avatar2.jpg,/static/images/avatar3.jpg')
    random_name = models.CharField(max_length=4096, null=True, blank=True, verbose_name='随机名称', default='访客,用户,小伙伴,朋友')
    random_cover = models.TextField(null=True, blank=True, verbose_name='随机封面', default='/static/images/cover1.jpg,/static/images/cover2.jpg')
    waifu_json = models.TextField(null=True, blank=True, verbose_name='看板娘消息', default='{"welcome": "欢迎来到我的博客！", "messages": ["你好呀！", "今天过得怎么样？", "有什么需要帮助的吗？"]}')
    status = models.BooleanField(default=True, verbose_name='是否启用[0:否，1:是]')

    class Meta:
        db_table = 'web_info'
        verbose_name = '网站信息表'
        verbose_name_plural = verbose_name

    def __str__(self):
        return str(self.id) + '-' + str(self.web_name)