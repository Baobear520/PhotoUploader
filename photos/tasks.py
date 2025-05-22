import os
from importlib import import_module

from django.conf import settings
from django.db import OperationalError
from django.forms.models import model_to_dict
from celery import shared_task, group
from urllib3.exceptions import NameResolutionError

from .handlers import image_handler, get_handler
from .models import ImageRecord
import logging


logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def image_task(self, file_name: str) -> dict | None:
    try:
        num, execution_time = image_handler(file_name)
        record = ImageRecord.objects.create(file_name=file_name, image_random_num=num)
        data = model_to_dict(record)
        data["execution_time"] = execution_time

        msg = f"Task {self.request.id}: {data}"
        logger.info(msg, extra=data)

        # Send notifications to all backends
        alert_group = group(
            send_alert_task.s(backend, msg) for backend in settings.NOTIFICATION_BACKENDS
        )
        alert_group.delay()  # Запускаем все таски параллельно

        return data

    except OperationalError as exc:
        self.retry(exc=exc)  # Will propagate to result backend
    except NameResolutionError as exc:
        # Immediate failure for DNS issues
        raise self.retry(exc=exc, countdown=60)  # Long delay
    except Exception as e:
        logger.error(f"{type(e).__name__}: {e}")


@shared_task
def send_alert_task(backend: str, message: str):
    """Универсальная таска для отправки алертов."""
    try:
        handler = get_handler(backend)
        success = handler.send(message)

        if not success:
            raise Exception(f"{backend} alert failed")
    except Exception as e:
        logger.error(f"Alert error: {e}")
        raise







