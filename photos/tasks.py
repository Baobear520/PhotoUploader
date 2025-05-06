import time
import random
from celery import shared_task
from .models import ImageRecord

@shared_task
def process_file(file_name):
    time.sleep(20)  # 20 сек на файл
    number = random.randint(1, 1000)
    ImageRecord.objects.create(
        file_name=file_name,
        image_randomnumber=number
    )
    return number