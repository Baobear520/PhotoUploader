from django.db import OperationalError
from django.forms.models import model_to_dict
from celery import shared_task

from .handlers import image_handler
from .models import ImageRecord


@shared_task()
def image_task(file_name: str, *args, **kwargs) -> dict | None:
    try:
        num, execution_time = image_handler(file_name)
        record = ImageRecord.objects.create(file_name=file_name, image_random_num=num)
        data = model_to_dict(record)
        data["execution_time"] = execution_time
        return data

    except OperationalError as e:
        print(f"Error: {e}")

    except Exception as e:
        print(f"Error: {e}")

    return






