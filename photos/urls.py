from django.urls import path


from photos.views import UploadView, TaskStatusView

urlpatterns = [
    path('', UploadView.as_view(), name='home'),
    path('upload/', UploadView.as_view(), name='upload-images'),
    path('task-status/', TaskStatusView.as_view(), name='task-status'),
]


