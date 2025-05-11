import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, RequestFactory
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from celery.result import AsyncResult
from django.http import JsonResponse

from .views import UploadView, TaskStatusView
from .tasks import image_task
from .validators import ImageValidator, ImageBatchValidator
from config.celery import check_celery_available

VALID_FILE_NAME = "valid_image.jpg"
INVALID_FILE_NAME = "invalid_file.txt"
LARGE_FILE_NAME = "large_image.jpg"
LONG_NAME_FILE = "x" * 256 + ".jpg"


class ResponseDataMixin:
    @staticmethod
    def get_response_data(response) -> dict:
        return json.loads(response.content.decode('utf-8'))


class UploadViewTest(ResponseDataMixin, TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.view = UploadView.as_view()
        self.valid_file = SimpleUploadedFile(
            VALID_FILE_NAME, b"file_content", "image/jpeg"
        )
        self.invalid_file = SimpleUploadedFile(
            INVALID_FILE_NAME, b"file_content", "text/plain"
        )
        self.large_file = SimpleUploadedFile(
            LARGE_FILE_NAME, b"x" * (6 * 1024 * 1024), "image/jpeg"  # 6MB
        )

    @patch.object(image_task, 'delay')
    @patch('photos.views.check_celery_available')
    def test_valid_upload(self, mock_celery_check, mock_delay):
        mock_celery_check.return_value = True
        mock_delay.return_value = AsyncResult('mock-task-id')

        request = self.factory.post('/update/', {'images': [self.valid_file]})
        response = self.view(request)
        data = self.get_response_data(response)

        self.assertEqual(response.status_code, 202)
        self.assertEqual(len(data['task_ids']), 1)
        self.assertEqual(len(data['valid_images']), 1)
        mock_delay.assert_called_once_with(VALID_FILE_NAME)

    @patch('photos.views.check_celery_available')
    def test_no_files_upload(self, mock_celery_check):
        mock_celery_check.return_value = True

        request = self.factory.post('/update/', {})
        response = self.view(request)
        data = self.get_response_data(response)

        self.assertEqual(response.status_code, 400)
        self.assertIn('Error', data)

    @patch('photos.views.check_celery_available')
    def test_invalid_files_upload(self, mock_celery_check):
        mock_celery_check.return_value = True

        request = self.factory.post('/update/', {'images': [self.invalid_file]})
        response = self.view(request)
        data = self.get_response_data(response)

        self.assertEqual(response.status_code, 400)
        self.assertIn('Unsupported extension', data['Error'])

    @patch('photos.views.check_celery_available')
    def test_large_files_upload(self, mock_celery_check):
        mock_celery_check.return_value = True

        request = self.factory.post('/update/', {'images': [self.large_file]})
        response = self.view(request)
        data = self.get_response_data(response)

        self.assertEqual(response.status_code, 400)
        self.assertIn('exceeds maximum', data['Error'])

    @patch.object(image_task, 'delay')
    @patch('photos.views.check_celery_available')
    def test_mixed_files_upload(self, mock_celery_check, mock_delay):
        mock_celery_check.return_value = True
        mock_delay.return_value = AsyncResult('mock-task-id')

        request = self.factory.post('/update/', {
            'images': [self.valid_file, self.invalid_file, self.large_file]
        })
        response = self.view(request)
        data = self.get_response_data(response)

        self.assertEqual(response.status_code, 202)
        self.assertEqual(len(data['task_ids']), 1)
        self.assertEqual(len(data['valid_images']), 1)

    @patch('photos.views.check_celery_available')
    def test_celery_unavailable(self, mock_celery_check):
        mock_celery_check.side_effect = ConnectionError("Celery down")

        request = self.factory.post('/update/', {'images': [self.valid_file]})
        response = self.view(request)
        data = self.get_response_data(response)

        self.assertEqual(response.status_code, 503)
        self.assertIn('problem on our end', data['error'])


class TaskStatusViewTest(ResponseDataMixin, TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.view = TaskStatusView.as_view()

    @patch('photos.views.AsyncResult')
    def test_success_status(self, mock_async):
        mock_task = MagicMock()
        mock_task.status = 'SUCCESS'
        mock_task.result = {'file_name': 'test.jpg', 'number': 42}
        mock_async.return_value = mock_task

        request = self.factory.get('task-status/?task_id=123')
        response = self.view(request, *[], **{})
        data = self.get_response_data(response)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'SUCCESS')
        self.assertEqual(data['result']['number'], 42)

    @patch('photos.views.AsyncResult')
    def test_pending_status(self, mock_async):
        mock_task = MagicMock()
        mock_task.status = 'PENDING'
        mock_task.result = None
        mock_async.return_value = mock_task

        request = self.factory.get('task-status/?task_id=123')
        response = self.view(request, *[], **{})
        data = self.get_response_data(response)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'PENDING')
        self.assertIsNone(data['result'])

    @patch('photos.views.AsyncResult')
    def test_failed_status(self, mock_async):
        mock_task = MagicMock()
        mock_task.status = 'FAILURE'
        mock_task.result = Exception("Task failed")
        mock_async.return_value = mock_task

        request = self.factory.get('task-status/?task_id=123')
        response = self.view(request, *[], **{})
        data = self.get_response_data(response)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'FAILURE')
        self.assertIn('Task failed', str(data['result']))

    def test_missing_task_id(self):
        request = self.factory.get('/task-status/')
        response = self.view(request, *[], **{})
        data = self.get_response_data(response)

        self.assertEqual(response.status_code, 500)
        self.assertIn('Error', data)


class ImageValidatorTest(TestCase):
    def setUp(self):
        self.validator = ImageValidator()
        self.valid_file = SimpleUploadedFile(
            VALID_FILE_NAME, b"content", "image/jpeg"
        )
        self.invalid_ext_file = SimpleUploadedFile(
            INVALID_FILE_NAME, b"content", "text/plain"
        )
        self.large_file = SimpleUploadedFile(
            LARGE_FILE_NAME, b"x" * (6 * 1024 * 1024), "image/jpeg"
        )
        self.long_name_file = MagicMock()
        self.long_name_file.name = LONG_NAME_FILE
        self.long_name_file.size = 1000

    def test_valid_file(self):
        try:
            self.validator(self.valid_file)
        except ValidationError:
            self.fail("Valid file failed validation")

    def test_invalid_extension(self):
        with self.assertRaises(ValidationError) as ctx:
            self.validator(self.invalid_ext_file)
        self.assertIn("Unsupported extension", str(ctx.exception))

    def test_large_file(self):
        with self.assertRaises(ValidationError) as ctx:
            self.validator(self.large_file)
        self.assertIn("exceeds maximum", str(ctx.exception))

    def test_long_filename(self):
        with self.assertRaises(ValidationError) as ctx:
            self.validator(self.long_name_file)
        self.assertIn("Name too long", str(ctx.exception))


class ImageBatchValidatorTest(TestCase):
    def setUp(self):
        self.validator = ImageBatchValidator()
        self.valid_files = [
            SimpleUploadedFile(f"img{i}.jpg", b"content", "image/jpeg")
            for i in range(5)
        ]
        self.too_many_files = [
            SimpleUploadedFile(f"img{i}.jpg", b"content", "image/jpeg")
            for i in range(101)
        ]
        self.mixed_files = [
            SimpleUploadedFile("img1.jpg", b"content", "image/jpeg"),
            SimpleUploadedFile("invalid.txt", b"content", "text/plain"),
            SimpleUploadedFile("img2.jpg", b"content", "image/jpeg")
        ]

    def test_valid_batch(self):
        result = self.validator(self.valid_files)
        self.assertEqual(len(result), 5)

    def test_too_many_files(self):
        with self.assertRaises(ValidationError) as ctx:
            self.validator(self.too_many_files)
        self.assertIn("Too many images", str(ctx.exception))

    def test_mixed_files(self):
        result = self.validator(self.mixed_files)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].name, "img1.jpg")
        self.assertEqual(result[1].name, "img2.jpg")

    def test_all_invalid(self):
        invalid_files = [
            SimpleUploadedFile(f"invalid{i}.txt", b"content", "text/plain")
            for i in range(3)
        ]
        with self.assertRaises(ValidationError) as ctx:
            self.validator(invalid_files)
        self.assertIn("No valid images provided", str(ctx.exception))