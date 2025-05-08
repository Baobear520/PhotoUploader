import random
import time


MOCK_PROCESSING_TIME = 20

def image_handler(file_name: str, *args, **kwargs)-> tuple[int, float]:
    """Функция для процессинга изображения.

    Args:
        file_name (str): Имя файла (в данной имплементации не используется).

    Returns:
        tuple[int, float]: Рандомное число и время выполнения

    """


    start = time.perf_counter()

    num = random.randint(1, 1000)
    time.sleep(MOCK_PROCESSING_TIME)

    finish = time.perf_counter()
    execution_time = finish - start

    return num, execution_time