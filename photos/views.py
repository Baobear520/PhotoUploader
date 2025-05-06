import random
import time

from django.core.exceptions import ValidationError
from django.db import OperationalError, transaction, IntegrityError, DatabaseError
from django.shortcuts import render
from django.http import HttpResponseNotAllowed, HttpResponseBadRequest, HttpResponseServerError, HttpResponse

from photos.models import Photo

# views.py
from django.views.generic import FormView, TemplateView, CreateView
from .forms import SingleUploadForm, FileFieldForm


class UploadFilesView(CreateView):
    model = Photo
    fields = ['image_random_num']
    template_name = 'photos/upload.html'

    def form_valid(self, form):
        obj = form.save(commit=False)
        if self.request.FILES:
            for f in self.request.FILES.getlist('file'):
                obj = self.model.objects.create(image_random_num=random.randint(1,1000))


        return super(UploadFilesView, self).form_valid(form)






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