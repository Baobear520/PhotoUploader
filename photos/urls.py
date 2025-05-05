from django.urls import path

from photos import views

urlpatterns = [
    path('photo', views.upload_photo, name='upload_photo'),

]