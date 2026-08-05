from django.contrib import admin
from .models import Task, TaskParticipant, TaskProof


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'amount', 'balance', 'completed_count', 'status', 'creator', 'create_time')
    list_filter = ('status', 'deleted')
    search_fields = ('title', 'description')


@admin.register(TaskParticipant)
class TaskParticipantAdmin(admin.ModelAdmin):
    list_display = ('id', 'task', 'user', 'status', 'reward', 'create_time')
    list_filter = ('status', 'deleted')
    search_fields = ('task__title', 'user__username')


@admin.register(TaskProof)
class TaskProofAdmin(admin.ModelAdmin):
    list_display = ('id', 'participant', 'image', 'create_time')
    search_fields = ('participant__task__title', 'image')
