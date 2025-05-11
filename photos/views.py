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

            if 'images' not in request.FILES:
                return JsonResponse({"error": "No files provided"}, status=400)

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
            return JsonResponse({"error": "Service unavailable. Please try again later."}, status=503)

        except ValidationError as e:
            return JsonResponse({"error": str(e)}, status=400)

        except Exception as e:
            logger.exception("Unexpected upload error")
            return JsonResponse({"error": "Internal server error"}, status=500)


class TaskStatusView(DetailView):
    def get(self, request, *args, **kwargs):
        try:
            task_id = request.GET.get('task_id')
            task = AsyncResult(task_id)
            response_data = {
                'status': task.status,
                'result': task.result if task.status == 'SUCCESS' else None
            }
            if task.failed():
                response_data['error'] = str(task.result)

            return JsonResponse(response_data, status=200)

        except Exception as e:
            logger.error("Unexpected error: %s", str(e))
            return JsonResponse({'Error': str(e)}, status=500)



