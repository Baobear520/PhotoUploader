from celery.result import AsyncResult
from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import View, DetailView

from .tasks import image_task


class UploadView(View):
    def get(self, request):
        return render(request, "home.html")

    def post(self,request):
        try:
            images = request.FILES.getlist('images')
            if images:
                tasks = []
                for image in images:
                    file_name = image.name
                    print(f"Processing file: {file_name}")
                    # Запуск задачи Celery для каждого файла
                    task = image_task.delay(file_name)
                    tasks.append(task.id)

                return JsonResponse({'task_ids': tasks}, status=202)
            return JsonResponse({'error': 'No files uploaded'}, status=400)
        except Exception as e:
            return JsonResponse({'Error': str(e)}, status=500)


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
            return JsonResponse({'Error': str(e)}, status=500)



