from celery import group
from django.shortcuts import render

from .tasks import test_task
from django.views.generic import View



class TestView(View):
    def get(self, request):
        return render(request, "test.html")

    def post(self,request):
        try:
            files = request.FILES.getlist("photos")
            if not files:
                return render(request, "error.html", {"error": "No files uploaded"})
            elif len(files) > 100:
                return render(request, "error.html", {"error": "Too many files"})
            elif len(files) == 1:
                file_name = files[0].name
                task = test_task.delay(file_name)
                context = {
                    "task_id": task.id,
                    "is_group": False,
                    "file_name": file_name
                }
            else:
                task_group = group(test_task.s(file.name) for file in files)
                group_result = task_group.apply_async()
                # you must explicitly call the save function on the group_result after calling the tasks
                group_result.save()
                context = {
                    "task_id": group_result.id,
                    "is_group": True
                }

            return render(request, 'success.html', context)

        except Exception as e:
            print(f"{type(e).__name__}: {e}")
            return render(request, "error.html", {"error": str(e)})


#
#
#
#
#
#
# def test(request):
#     files = request.FILES.getlist("photos")
#     if not files:
#         return render(request, "photos/error.html", {"error": "No files uploaded"})
#     file_name = files[0].name
#
#     task = test_task.delay(file_name)
#     context = {
#         "task_id": task.id,
#         "file_name": file_name
#     }
#     return render(request, "photos/test.html", context)


# def success(request):
#     tasks = AsyncResult(request.GET.get("task_id"))
#     return render(request, "photos/success.html", {"tasks": tasks})



# class UploadImageView(View):
#     def get(self, request):
#         return render(request, "photos/upload.html")
#
#     def post(self, request):
#         try:
#             files = request.FILES.getlist("photos")
#             if not files:
#                 return render(request, "photos/upload.html", {"error": "No files uploaded"})
#
#             records = ImageRecord.bulk_create(
#                 [ImageRecord(file_name=file) for file in files]
#             )
#             updated_records  = group_handler(records)
#
#             return render(request, "photos/success.html", {"records": updated_records})
#         except Exception as e:
#             return render(request, "photos/upload.html", {"error": str(e)})
    #
    # class UploadedImagesListView(View):
    #     def get(self, request):
    #         records = ImageRecord.objects.all().order_by("-id")
    #         return render(request, "photos/success.html", {"records": records})


#
# def home(request):
#     records = ImageRecord.objects.all().order_by("-id")
#     return render(request, "photos/home.html", {"records": records})


# @csrf_exempt
# def test(request):
#     if request.method == 'POST':
#         files = request.FILES.getlist("photos")
#         if not files:
#             return JsonResponse({"error": "No files uploaded"}, status=400)
#         return JsonResponse({
#             'status': 'success',
#             'received_files': [{'name': file.name, 'size': file.size} for file in files]
#         })
        # Запуск задач для каждого файла








# def upload_photo(request):
#     context = {
#         'single_form': SingleUploadForm(),
#         'multiple_form': MultipleUploadForm()
#     }
#
#     if request.method == 'POST':
#         # Определяем тип формы
#         if 'single_form' in request.POST:
#             form = SingleUploadForm(request.POST, request.FILES)
#             if form.is_valid():
#                 file = request.FILES['image']
#                 photo = Photo.objects.create(image_random_num=random.randint(1,1000))
#                 return render(
#                     request, 'photos/success.html',
#                     {'filename': file.name, 'random_num': photo.image_random_num}
#                 )
#             # Если формы невалидны
#             context['single_form'] = form
#
#         elif 'multiple_form' in request.POST:
#             form = MultipleUploadForm(request.POST, request.FILES)
#             if form.is_valid():
#                 files = request.FILES.getlist('files')
#                 with transaction.atomic():
#                     photos = Photo.objects.bulk_create(
#                         [Photo(random_num=random.randint(1,1000)) for _ in range(len(files))]
#                     )
#                     photo_attrs = []
#                     for file, photo in zip(files, photos):
#                         photo_attrs.append({
#                             'filename': file.name,
#                             'random_num': photo.image_random_num
#                         })
#                 return render(request, 'photos/success.html', {'files': photo_attrs})
#
#             # Если форма невалидны
#
#             context['multiple_form'] = form if 'multiple_form' in request.POST else MultipleUploadForm()
#     return render(request, 'photos/upload.html', context)






# def upload_photo(request):
#     allowed_methods = ["GET", "POST"]
#     wait_time = 2
#     random_num = random.randint(1, 1000)
#     context = {
#         'content': 'Please upload an image',
#         'is_post': False,
#         'single_upload': None,
#         'multiple_uploads': []
#     }
#
#     if request.method not in allowed_methods:
#         return HttpResponseNotAllowed(allowed_methods)
#
#     if request.method == "POST":
#         try:
#             # Определяем тип формы по имени кнопки submit
#             form_type = request.POST.get('form_type')
#
#             # Обработка единичной загрузки
#             if form_type == 'single':
#                 if 'single_image' not in request.FILES:
#                     return HttpResponseBadRequest("No image provided", status=400)
#
#                 file = request.FILES['single_image']
#                 photo = Photo(image_random_num=random_num)
#                 photo.save()
#
#                 context.update({
#                     'single_upload': {
#                         'filename': file.name,
#                         'random_num': photo.image_random_num
#                     }
#                 })
#
#             # Обработка множественной загрузки
#             elif form_type == 'multiple':
#                 files = request.FILES.getlist('multiple_images')
#                 if not files:
#                     return HttpResponseBadRequest("No images provided", status=400)
#                 # Загружаем фото в базу за одну транзакцию
#                 with transaction.atomic():
#                     photos = Photo.objects.bulk_create([Photo(image_random_num=random_num) for _ in range(len(files))])
#                 photo_attrs = []
#                 for file, photo in zip(files, photos):
#                     photo_attrs.append({
#                         'filename': file.name,
#                         'random_num': photo.image_random_num
#                     })
#
#                 context.update({
#                     'multiple_uploads': photo_attrs
#                 })
#
#                 # Общие обновления контекста
#                 time.sleep(wait_time)
#                 context.update({
#                     'is_post': True,
#                     'content': 'Uploaded successfully!',
#                     'wait_time': f"{wait_time} seconds"
#                 })
#
#         except OperationalError as e:
#             return HttpResponseServerError(f"Database error: {e}", status=500)
#
#         except Exception as e:
#             print(f"Unexpected error: {e}")
#             return HttpResponseServerError(f"Something went wrong: {type(e).__name__} - {e}", status=500)
#
#     return render(request, "photos/index.html", context)