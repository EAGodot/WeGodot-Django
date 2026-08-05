from django.urls import path
from task.views.task import TaskListView, TaskDetailView, JoinTaskView, MyTaskView, CreatorTaskView, CompleteTaskView, UploadProofView, CreateTaskView, TaskParticipantsView

urlpatterns = [
    path("api/task/list/", TaskListView.as_view(), name="taskList"),
    path("api/task/detail/", TaskDetailView.as_view(), name="taskDetail"),
    path("api/task/join/", JoinTaskView.as_view(), name="joinTask"),
    path("api/task/my/", MyTaskView.as_view(), name="myTask"),
    path("api/task/creator/", CreatorTaskView.as_view(), name="creatorTask"),
    path("api/task/complete/", CompleteTaskView.as_view(), name="completeTask"),
    path("api/task/uploadProof/", UploadProofView.as_view(), name="uploadProof"),
    path("api/task/create/", CreateTaskView.as_view(), name="createTask"),
    path("api/task/participants/", TaskParticipantsView.as_view(), name="taskParticipants"),
]
