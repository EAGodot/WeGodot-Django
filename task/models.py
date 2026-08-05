from django.db import models
from appone.models.client import Client


class Task(models.Model):
    STATUS_CHOICES = (
        (0, '进行中'),
        (1, '已完成'),
        (2, '已关闭'),
    )
    title = models.CharField(max_length=128, verbose_name='任务标题')
    description = models.TextField(null=True, blank=True, verbose_name='任务描述')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='任务总金额')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='剩余金额')
    max_participants = models.IntegerField(default=0, verbose_name='最大参与人数(0为不限)')
    completed_count = models.IntegerField(default=0, verbose_name='已完成人数')
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=0, verbose_name='任务状态')
    creator = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='created_tasks', verbose_name='发布者')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='最终修改时间')
    deleted = models.BooleanField(default=False, verbose_name='是否删除')

    class Meta:
        db_table = 'task'
        verbose_name = '任务表'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.id}-{self.title}"


class TaskParticipant(models.Model):
    STATUS_CHOICES = (
        (0, '已参与'),
        (1, '待审核'),
        (2, '已完成'),
        (3, '已驳回'),
    )
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='participants', verbose_name='任务')
    user = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='task_participations', verbose_name='参与用户')
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=0, verbose_name='参与状态')
    proof = models.URLField(max_length=256, null=True, blank=True, verbose_name='凭证图片')
    reward = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='获得奖励')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='参与时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='最终修改时间')
    deleted = models.BooleanField(default=False, verbose_name='是否删除')

    class Meta:
        db_table = 'task_participant'
        verbose_name = '任务参与者表'
        verbose_name_plural = verbose_name
        unique_together = ('task', 'user')

    def __str__(self):
        return f"{self.task_id}-{self.user_id}"


class TaskProof(models.Model):
    participant = models.ForeignKey(TaskParticipant, on_delete=models.CASCADE, related_name='proofs', verbose_name='参与记录')
    image = models.URLField(max_length=256, verbose_name='凭证图片地址')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='上传时间')

    class Meta:
        db_table = 'task_proof'
        verbose_name = '任务凭证表'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.id}-{self.participant_id}"
