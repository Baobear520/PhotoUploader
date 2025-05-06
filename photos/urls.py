from django.urls import path

from photos import views

urlpatterns = [
    path('photo', views.UploadFilesView.as_view(), name='upload_photo'),

]