from django.urls import path

from photos import views

urlpatterns = [
    path('photo', views.upload_image, name='upload_image'),

]