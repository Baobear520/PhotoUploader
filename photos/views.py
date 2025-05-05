import random
import time

from django.http import HttpResponseNotAllowed, HttpResponseServerError, HttpResponseBadRequest
from django.shortcuts import render
from django.db import OperationalError
from photos.models import Photo

def upload_photo(request):
    # 1. Определяем разрешенные методы
    allowed_methods = ["GET", "POST"]
    wait_time = 2

    # 2. Проверяем метод запроса
    if request.method not in allowed_methods:
        return HttpResponseNotAllowed(allowed_methods)

    # 3. Инициализируем контекст с базовыми значениями
    context = {
        'content': 'Please upload an image',
        'is_post': False  # Флаг для определения типа запроса в шаблоне
    }

    # 4. Обрабатываем POST-запрос
    if request.method == "POST":
        try:
            file = request.FILES["image"]
            photo = Photo(image_random_num=random.randint(1, 1000))
            photo.save()
            time.sleep(wait_time)
            context.update(
                {
                'is_post': True,
                'content': 'Image uploaded successfully!',
                'filename':file,
                'image_random_num': photo.image_random_num,
                'wait_time': f"{wait_time} seconds"
                }
            )
        except (KeyError, OperationalError, Exception) as e:
            if isinstance(e, KeyError):
                return HttpResponseBadRequest("No image provided",status=400)
            elif isinstance(e, OperationalError):
                return HttpResponseServerError("Database error",status=500)
            else:
                return HttpResponseServerError("Something went wrong",status=500)

    # 5. Возвращаем ответ
    return render(request, "photos/index.html", context)