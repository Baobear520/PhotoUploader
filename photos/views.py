import logging

from celery.result import AsyncResult
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import View, DetailView

from .tasks import image_task
from .validators import validate_images


logger = logging.getLogger(__name__)

class UploadView(View):
    def get(self, request):
        return render(request, "home.html")

    def post(self,request):
        try:
            images = request.FILES.getlist('images')
            validate_images(images)
            logger.info(f"Validated {len(images)} images")
            tasks = []
            for image in images:
                file_name = image.name
                logger.info(f"Processing file: {file_name}")
                # Запуск задачи Celery для каждого файла
                task = image_task.delay(file_name)
                tasks.append(task.id)
            logger.info(f"Successfully scheduled {len(tasks)} tasks")
            return JsonResponse({'task_ids': tasks}, status=202)

        except (ValidationError, ValueError, Exception) as exception:
            error_status = 400 if isinstance(exception, (ValidationError, ValueError)) else 500
            log_error_response = f"{type(exception).__name__} error: {str(exception)}"
            logger.error(log_error_response)
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
            log_error_message = f"{type(e).__name__} error: {str(e)}"
            logger.error(log_error_message)
            return JsonResponse({'Error': str(e)}, status=500)



