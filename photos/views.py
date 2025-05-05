import random
import time

from django.db import OperationalError, transaction
from django.shortcuts import render
from django.http import HttpResponseNotAllowed, HttpResponseBadRequest, HttpResponseServerError
from photos.models import Photo


def upload_photo(request):
    allowed_methods = ["GET", "POST"]
    wait_time = 2
    context = {
        'content': 'Please upload an image',
        'is_post': False,
        'single_upload': None,
        'multiple_uploads': []
    }

    if request.method not in allowed_methods:
        return HttpResponseNotAllowed(allowed_methods)

    if request.method == "POST":
        try:
            # Определяем тип формы по имени кнопки submit
            form_type = request.POST.get('form_type')

            # Обработка единичной загрузки
            if form_type == 'single':
                if 'single_image' not in request.FILES:
                    return HttpResponseBadRequest("No image provided", status=400)

                file = request.FILES['single_image']
                photo = Photo(image_random_num=random.randint(1, 1000))
                photo.save()

                context.update({
                    'single_upload': {
                        'filename': file.name,
                        'random_num': photo.image_random_num
                    }
                })

            # Обработка множественной загрузки
            elif form_type == 'multiple':
                files = request.FILES.getlist('multiple_images')
                if not files:
                    return HttpResponseBadRequest("No images provided", status=400)

                with transaction.atomic():
                    photos = Photo.objects.bulk_create([Photo(image_random_num=random.randint(1, 1000)) for _ in range(len(files))])
                photo_attrs = []
                for file, photo in zip(files, photos):
                    photo_attrs.append({
                        'filename': file.name,
                        'random_num': photo.image_random_num
                    })

                context.update({
                    'multiple_uploads': photo_attrs
                })

                # Общие обновления контекста
                time.sleep(wait_time)
                context.update({
                    'is_post': True,
                    'content': 'Uploaded successfully!',
                    'wait_time': f"{wait_time} seconds"
                })

        except OperationalError as e:
            return HttpResponseServerError("Database error", status=500)
        except Exception as e:
            print(f"Unexpected error: {e}")
            return HttpResponseServerError("Something went wrong", status=500)

    return render(request, "photos/index.html", context)