from celery.result import AsyncResult
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import View, DetailView

from .tasks import image_task
from .validators import validate_images


class UploadView(View):
    def get(self, request):
        return render(request, "home.html")

    def post(self,request):
        try:
            images = request.FILES.getlist('images')
            validate_images(images)
            tasks = []
            for image in images:
                file_name = image.name
                print(f"Processing file: {file_name}")
                # Запуск задачи Celery для каждого файла
                task = image_task.delay(file_name)
                tasks.append(task.id)

            return JsonResponse({'task_ids': tasks}, status=202)

        except (ValidationError, ValueError, Exception) as exception:
            error_status = 400 if isinstance(exception, (ValidationError, ValueError)) else 500
            error_response = f"{type(exception).__name__} error: {str(exception)}"
            print(error_response)
            return JsonResponse({'Error': str(exception)}, status=error_status)



class TaskStatusView(DetailView):
    def get(self, request, *args, **kwargs):
        try:
            task_id = request.GET.get('task_id')
            task = AsyncResult(task_id)
            return JsonResponse({
                'status': task.status,
                'result': task.result if task.status == 'SUCCESS' else None
            })
        except Exception as e:
            error_message = f"{type(e).__name__} error: {str(e)}"
            return JsonResponse({'Error': error_message}, status=500)



