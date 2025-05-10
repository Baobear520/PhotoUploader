from django.db import DatabaseError
from django.forms.models import model_to_dict
from celery import shared_task

from .handlers import image_handler
from .models import ImageRecord
import logging

logger = logging.getLogger(__name__)

@shared_task()
def image_task(file_name: str) -> dict | None:
    try:
        num, execution_time = image_handler(file_name)
        record = ImageRecord.objects.create(file_name=file_name, image_random_num=num)

        data = model_to_dict(record)
        data["execution_time"] = execution_time
        logger.info(f"Task completed: {data}", extra=data)
        return data

    except DatabaseError as e:
            logger.error(f"DB error saving record: {str(e)}")

    except Exception as e:
        logger.error(f"{type(e).__name__}: {e}")

    return






