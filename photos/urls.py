from django.urls import path

from photos.views import TestView



urlpatterns = [
    path('test', TestView.as_view(), name='test'),
    path('success', TestView.as_view(), name='success'),
]


