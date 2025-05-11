import os
import socket
import logging

from celery import Celery


logger = logging.getLogger(__name__)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


def check_celery_available(timeout=3) -> bool | None:
    """
    Check if Celery workers are available with a timeout
    Returns True if workers are available else raises exception
    """
    try:
        # Check Redis connection first
        redis_conn = app.connection()
        redis_conn.ensure_connection(max_retries=1, timeout=timeout)

        # Check active workers
        inspector = app.control.inspect(timeout=timeout)
        workers = inspector.ping() or {}

        if not workers:
            logger.error("No active Celery workers found")
            raise ConnectionError("No active Celery workers found")

        return True

    except (ConnectionError, socket.timeout, OSError) as e:
        logger.error(f"{type(e).__name__} error: {str(e)}")
        raise ConnectionError("Celery server unavailable")

    except Exception as e:
        logger.exception("Celery check error: %s", str(e))
        raise