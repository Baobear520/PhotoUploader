import logging

from celery.result import AsyncResult
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import View, DetailView

from config.celery import check_celery_available
from .tasks import image_task
from .validators import ImageBatchValidator

logger = logging.getLogger(__name__)

class UploadView(View):
    def get(self, request):
        return render(request, "home.html")

    def post(self,request):
        try:
            # Check Celery status first
            check_celery_available()

            images = request.FILES.getlist('images')
            # Validate all images at once
            valid_images = ImageBatchValidator()(images)

            # Only process valid images
            task_ids = []
            for image in valid_images:
                logger.info("Processing file: %s", image.name)
                task = image_task.delay(image.name)
                task_ids.append(task.id)
            logger.info("Successfully scheduled %s tasks", len(task_ids))
            data = {
                'task_ids': task_ids,
                'valid_images': [image.name for image in valid_images]
            }
            return JsonResponse(data,status=202)

        except ConnectionError as e:
            logger.error("Connection error: %s", str(e))
            user_message = "There was a problem on our end. Please try again later."
            return JsonResponse({"error": user_message}, status=503)

        except (ValidationError, ValueError, Exception) as exception:
            error_status = 400 if isinstance(exception, (ValidationError, ValueError)) else 500
            print(exception)

            logger.error("%s occurred: %s", type(exception).__name__, str(exception))
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



