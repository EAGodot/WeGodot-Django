import time
import json
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import AllowAny
from task.models import Task, TaskParticipant
from appone.models.client import Client


class TaskListView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        data = request.data
        current = int(data.get('current', 0))
        size = int(data.get('size', 0))
        searchKey = data.get('searchKey', '').strip()
        task_status = data.get('status', '').strip()

        dataall = []
        data_list = []
        query = Q(deleted=False)

        if searchKey:
            query &= Q(title__contains=searchKey)
        if task_status != '':
            try:
                query &= Q(status=int(task_status))
            except ValueError:
                pass

        tasks = Task.objects.filter(query).order_by('-create_time')
        total = tasks.count()
        start = (current - 1) * size if current and size else 0
        end = start + size if size else total
        page_tasks = tasks[start:end]

        for task in page_tasks:
            try:
                creator = Client.objects.get(user_id=task.creator_id, deleted=False)
                creator_name = creator.username
            except Client.DoesNotExist:
                creator_name = "未知用户"

            participants_count = TaskParticipant.objects.filter(task=task, deleted=False).count()
            data_list.append({
                'id': task.id,
                'title': task.title,
                'description': task.description or '',
                'amount': float(task.amount),
                'balance': float(task.balance),
                'max_participants': task.max_participants,
                'completed_count': task.completed_count,
                'participants_count': participants_count,
                'status': task.status,
                'status_display': task.get_status_display(),
                'creator_id': task.creator_id,
                'creator_name': creator_name,
                'create_time': task.create_time,
            })

        dataall.append({
            'code': 200,
            'message': "null",
            'total': total,
            'data': data_list,
            'currentTimeMillis': int(time.time() * 1000),
        })
        return Response({'result': dataall})


class TaskDetailView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        task_id = request.data.get('task_id')
        if not task_id:
            return Response({'result': [{'code': 400, 'message': 'task_id 不能为空'}]})

        try:
            task = Task.objects.get(id=task_id, deleted=False)
        except Task.DoesNotExist:
            return Response({'result': [{'code': 404, 'message': '任务不存在'}]})

        try:
            creator = Client.objects.get(user_id=task.creator_id, deleted=False)
            creator_name = creator.username
        except Client.DoesNotExist:
            creator_name = "未知用户"

        participants_count = TaskParticipant.objects.filter(task=task, deleted=False).count()

        return Response({
            'result': [{
                'code': 200,
                'data': {
                    'id': task.id,
                    'title': task.title,
                    'description': task.description or '',
                    'amount': float(task.amount),
                    'balance': float(task.balance),
                    'max_participants': task.max_participants,
                    'completed_count': task.completed_count,
                    'participants_count': participants_count,
                    'status': task.status,
                    'status_display': task.get_status_display(),
                    'creator_id': task.creator_id,
                    'creator_name': creator_name,
                    'create_time': task.create_time,
                    'update_time': task.update_time,
                }
            }]
        })


class JoinTaskView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        task_id = request.data.get('task_id')
        user_id = request.data.get('user_id')
        if not task_id or not user_id:
            return Response({'result': [{'code': 400, 'message': 'task_id 和 user_id 不能为空'}]})

        try:
            task = Task.objects.get(id=task_id, deleted=False)
        except Task.DoesNotExist:
            return Response({'result': [{'code': 404, 'message': '任务不存在'}]})

        if task.status != 0:
            return Response({'result': [{'code': 400, 'message': '任务已关闭或已完成'}]})

        if task.balance <= 0:
            return Response({'result': [{'code': 400, 'message': '任务余额不足'}]})

        try:
            client = Client.objects.get(user_id=user_id, deleted=False)
        except Client.DoesNotExist:
            return Response({'result': [{'code': 404, 'message': '用户不存在'}]})

        participant, created = TaskParticipant.objects.get_or_create(
            task=task,
            user=client,
            deleted=False,
            defaults={'status': 1}
        )
        if not created:
            return Response({'result': [{'code': 400, 'message': '您已参与该任务'}]})

        return Response({
            'result': [{
                'code': 200,
                'message': '参与成功',
                'data': {
                    'participant_id': participant.id,
                    'status': participant.get_status_display(),
                }
            }]
        })


class MyTaskView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        user_id = request.data.get('user_id')
        current = int(request.data.get('current', 0))
        size = int(request.data.get('size', 0))

        if not user_id:
            return Response({'result': [{'code': 400, 'message': 'user_id 不能为空'}]})

        dataall = []
        data_list = []

        query = Q(user_id=user_id, deleted=False)
        participants = TaskParticipant.objects.filter(query).order_by('-create_time')
        total = participants.count()
        start = (current - 1) * size if current and size else 0
        end = start + size if size else total
        page_participants = participants[start:end]

        for participant in page_participants:
            task = participant.task
            try:
                creator = Client.objects.get(user_id=task.creator_id, deleted=False)
                creator_name = creator.username
            except Client.DoesNotExist:
                creator_name = "未知用户"

            data_list.append({
                'id': task.id,
                'title': task.title,
                'description': task.description or '',
                'amount': float(task.amount),
                'balance': float(task.balance),
                'completed_count': task.completed_count,
                'status': task.status,
                'status_display': task.get_status_display(),
                'creator_name': creator_name,
                'participant_status': participant.get_status_display(),
                'participant_status_code': participant.status,
                'proof': participant.proof or '',
                'reward': float(participant.reward),
                'create_time': task.create_time,
            })

        dataall.append({
            'code': 200,
            'message': "null",
            'total': total,
            'data': data_list,
            'currentTimeMillis': int(time.time() * 1000),
        })
        return Response({'result': dataall})


class CreatorTaskView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        user_id = request.data.get('user_id')
        current = int(request.data.get('current', 0))
        size = int(request.data.get('size', 0))

        if not user_id:
            return Response({'result': [{'code': 400, 'message': 'user_id 不能为空'}]})

        dataall = []
        data_list = []

        query = Q(creator_id=user_id, deleted=False)
        tasks = Task.objects.filter(query).order_by('-create_time')
        total = tasks.count()
        start = (current - 1) * size if current and size else 0
        end = start + size if size else total
        page_tasks = tasks[start:end]

        for task in page_tasks:
            participants_count = TaskParticipant.objects.filter(task=task, deleted=False).count()
            data_list.append({
                'id': task.id,
                'title': task.title,
                'description': task.description or '',
                'amount': float(task.amount),
                'balance': float(task.balance),
                'max_participants': task.max_participants,
                'completed_count': task.completed_count,
                'participants_count': participants_count,
                'status': task.status,
                'status_display': task.get_status_display(),
                'create_time': task.create_time,
            })

        dataall.append({
            'code': 200,
            'message': "null",
            'total': total,
            'data': data_list,
            'currentTimeMillis': int(time.time() * 1000),
        })
        return Response({'result': dataall})


class CompleteTaskView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        task_id = request.data.get('task_id')
        user_id = request.data.get('user_id')
        if not task_id or not user_id:
            return Response({'result': [{'code': 400, 'message': 'task_id 和 user_id 不能为空'}]})

        try:
            task = Task.objects.get(id=task_id, deleted=False)
        except Task.DoesNotExist:
            return Response({'result': [{'code': 404, 'message': '任务不存在'}]})

        if task.creator_id != user_id:
            return Response({'result': [{'code': 403, 'message': '只有发布者可以完成任务'}]})

        if task.status != 0:
            return Response({'result': [{'code': 400, 'message': '任务已关闭或已完成'}]})

        participants = TaskParticipant.objects.filter(task=task, status__in=[0, 1], deleted=False)
        if participants.count() == 0:
            return Response({'result': [{'code': 400, 'message': '没有参与者'}]})

        reward_per_person = task.balance / participants.count() if participants.count() > 0 else 0

        for participant in participants:
            participant.status = 2
            participant.reward = reward_per_person
            participant.save()

        task.balance = 0
        task.status = 1
        task.save()

        return Response({
            'result': [{
                'code': 200,
                'message': '任务已完成',
                'data': {
                    'reward_per_person': float(reward_per_person),
                    'total_participants': participants.count(),
                }
            }]
        })


class UploadProofView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        task_id = request.data.get('task_id')
        user_id = request.data.get('user_id')
        image = request.data.get('image', '').strip()

        if not task_id or not user_id or not image:
            return Response({'result': [{'code': 400, 'message': 'task_id, user_id, image 不能为空'}]})

        try:
            task = Task.objects.get(id=task_id, deleted=False)
        except Task.DoesNotExist:
            return Response({'result': [{'code': 404, 'message': '任务不存在'}]})

        if task.status != 0:
            return Response({'result': [{'code': 400, 'message': '任务已关闭或已完成'}]})

        try:
            participant = TaskParticipant.objects.get(task=task, user_id=user_id, deleted=False)
        except TaskParticipant.DoesNotExist:
            return Response({'result': [{'code': 404, 'message': '您还未参与该任务'}]})

        participant.proof = image
        participant.status = 1
        participant.save()

        TaskProof.objects.create(participant=participant, image=image)

        return Response({
            'result': [{
                'code': 200,
                'message': '凭证上传成功',
            }]
        })


class CreateTaskView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        title = request.data.get('title', '').strip()
        description = request.data.get('description', '').strip()
        amount = request.data.get('amount')
        max_participants = request.data.get('max_participants', 0)
        creator_id = request.data.get('creator_id')

        if not title or amount is None or not creator_id:
            return Response({'result': [{'code': 400, 'message': '标题、金额和发布者不能为空'}]})

        try:
            client = Client.objects.get(user_id=creator_id, deleted=False)
        except Client.DoesNotExist:
            return Response({'result': [{'code': 404, 'message': '发布者不存在'}]})

        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError()
        except (ValueError, TypeError):
            return Response({'result': [{'code': 400, 'message': '金额必须大于0'}]})

        task = Task.objects.create(
            title=title,
            description=description,
            amount=amount,
            balance=amount,
            max_participants=int(max_participants) if max_participants else 0,
            creator=client,
        )

        return Response({
            'result': [{
                'code': 200,
                'message': '发布成功',
                'data': {
                    'id': task.id,
                    'title': task.title,
                    'amount': float(task.amount),
                    'balance': float(task.balance),
                }
            }]
        })


class TaskParticipantsView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        task_id = request.data.get('task_id')
        if not task_id:
            return Response({'result': [{'code': 400, 'message': 'task_id 不能为空'}]})

        try:
            task = Task.objects.get(id=task_id, deleted=False)
        except Task.DoesNotExist:
            return Response({'result': [{'code': 404, 'message': '任务不存在'}]})

        participants = TaskParticipant.objects.filter(task=task, deleted=False).select_related('user')
        data_list = []
        for participant in participants:
            user = participant.user
            data_list.append({
                'id': participant.id,
                'user_id': user.user_id,
                'user_name': user.username,
                'status': participant.get_status_display(),
                'status_code': participant.status,
                'proof': participant.proof or '',
                'reward': float(participant.reward),
                'create_time': participant.create_time,
            })

        return Response({
            'result': [{
                'code': 200,
                'data': data_list,
            }]
        })

