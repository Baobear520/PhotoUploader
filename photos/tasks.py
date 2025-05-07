import json
import time
import random
from django.forms.models import model_to_dict
from celery import shared_task, group
from celery.contrib.abortable import AbortableTask
from celery_progress.backend import ProgressRecorder

from .models import ImageRecord


@shared_task(bind=True)
def test_task(self,file_name):
    try:
        total_steps = 100
        execution_time = 5
        delay_per_step = execution_time / total_steps
        progres_recorder = ProgressRecorder(self)
        # Основной цикл прогресса
        for i in range(total_steps):
            time.sleep(delay_per_step)
            progres_recorder.set_progress((i + 1), total_steps)
        num = random.randint(1, 1000)
        record = ImageRecord.objects.create(file_name=file_name, image_random_num=num)
        data = model_to_dict(record)
        data["execution_time"] = execution_time
        result = json.dumps(data)
        return result

    except Exception as e:
        return "Error: " + str(e)







