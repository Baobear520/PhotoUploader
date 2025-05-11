from django.db import OperationalError
from django.forms.models import model_to_dict
from celery import shared_task
from urllib3.exceptions import NameResolutionError

from .handlers import image_handler
from .models import ImageRecord
import logging


logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def image_task(self, file_name: str) -> dict | None:
    try:
        num, execution_time = image_handler(file_name)
        record = ImageRecord.objects.create(file_name=file_name, image_random_num=num)
        logger.info(f"Record to save: {record}")

        data = model_to_dict(record)
        data["execution_time"] = execution_time
        logger.info(f"Task completed: {data}", extra=data)
        return data

    except OperationalError as exc:
        self.retry(exc=exc)  # Will propagate to result backend
    except NameResolutionError as exc:
        # Immediate failure for DNS issues
        raise self.retry(exc=exc, countdown=60)  # Long delay
    except Exception as e:
        logger.error(f"{type(e).__name__}: {e}")








