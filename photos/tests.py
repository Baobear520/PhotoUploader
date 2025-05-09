import json

from unittest.mock import patch
from django.test import TestCase, RequestFactory
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from celery.result import AsyncResult

from .views import UploadView, TaskStatusView
from .tasks import image_task
from .validators import ImageValidator, ImageBatchValidator, validate_images


VALID_FILE_NAME = "valid_image.jpg"
INVALID_FILE_NAME = "invalid_file.txt"


class ResponseDataMixin:
    @staticmethod
    def get_response_data(response) -> dict:
        return json.loads(response.content.decode('utf-8'))


class UploadViewTest(ResponseDataMixin, TestCase):
    def setUp(self):
        self.request_factory = RequestFactory()
        self.upload_view = UploadView.as_view()
        self.valid_image_file = SimpleUploadedFile(
            VALID_FILE_NAME, b"file_content", content_type="image/jpeg"
        )
        self.invalid_image_file = SimpleUploadedFile(
            INVALID_FILE_NAME, b"file_content", content_type="text/plain"
        )

    @patch.object(image_task, 'delay')
    def test_valid_image_upload(self, mock_delay):
        mock_delay.return_value = AsyncResult('mock-task-id')
        request = self.request_factory.post('/upload/', {'images': [self.valid_image_file]})
        response = self.upload_view(request)
        response_data = self.get_response_data(response)

        self.assertEqual(response.status_code, 202)
        self.assertIn('task_ids', response_data)
        mock_delay.assert_called_once_with(VALID_FILE_NAME)

    def test_upload_without_files(self):
        request = self.request_factory.post('/upload/', {})
        response = self.upload_view(request)
        response_data = self.get_response_data(response)

        self.assertEqual(response.status_code, 400)
        self.assertIn('Error', response_data)

    @patch('photos.validators.validate_images')
    def test_invalid_image_upload(self, mock_validate):
        mock_validate.side_effect = ValidationError
        request = self.request_factory.post('/upload', {'images': [self.invalid_image_file, self.invalid_image_file]})
        response = self.upload_view(request)
        response_data = self.get_response_data(response)
        error_message = response_data['Error'].strip("'[]")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(error_message, 'No valid images found.')

    @patch.object(image_task, 'delay')
    def test_upload_multiple_images(self, mock_delay):
        mock_delay.side_effect = [
            AsyncResult('mock-task-1'),
            AsyncResult('mock-task-2')
        ]
        request = self.request_factory.post('/upload', {
            'images': [self.valid_image_file, self.valid_image_file]
        })
        response = self.upload_view(request)
        response_data = self.get_response_data(response)

        self.assertEqual(response.status_code, 202)
        self.assertEqual(len(response_data['task_ids']), 2)


class TaskStatusViewTest(ResponseDataMixin,TestCase):
    def setUp(self):
        self.request_factory = RequestFactory()
        self.task_status_view = TaskStatusView.as_view()


    @patch('photos.views.AsyncResult')
    def test_success_status(self, mock_async_result):
        mock_task = mock_async_result.return_value
        mock_task.status = 'SUCCESS'
        mock_task.result = {'filename': VALID_FILE_NAME, 'result': 42}

        request = self.request_factory.get('/?task_id=mock-task-id')
        response = self.task_status_view(request)
        response_data = self.get_response_data(response)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_data, {
            'status': 'SUCCESS',
            'result': {'filename': VALID_FILE_NAME, 'result': 42}
        })


class MockFile:
    def __init__(self, name, size):
        self.name = name
        self.size = size


class ImageValidatorTest(TestCase):
    def setUp(self):
        self.image_validator = ImageValidator()
        self.valid_image_file = SimpleUploadedFile(
            VALID_FILE_NAME, b"file_content", content_type="image/jpeg"
        )
        self.large_image_file = SimpleUploadedFile(
            "large.jpg", b"x" * (5 * 1024 * 1024 + 1), content_type="image/jpeg"
        )
        self.invalid_extension_file = SimpleUploadedFile(
            "test.txt", b"file_content", content_type="text/plain"
        )
        self.long_name_file = MockFile(name="x" * 256 + ".jpg", size=1000)

    def test_valid_image(self):
        self.image_validator(self.valid_image_file)

    def test_invalid_extension(self):
        with self.assertRaises(ValidationError) as cm:
            self.image_validator(self.invalid_extension_file)
        self.assertRegex(str(cm.exception), r"Unsupported file extension")

    def test_large_file_size(self):
        with self.assertRaises(ValidationError) as cm:
            self.image_validator(self.large_image_file)
        self.assertRegex(str(cm.exception), r"Image size should not exceed 5MB")

    def test_long_file_name(self):
        with self.assertRaises(ValidationError) as cm:
            self.image_validator(self.long_name_file)
        self.assertRegex(str(cm.exception), r"Image name should not exceed 255 characters")


class ImageBatchValidatorTest(TestCase):
    def setUp(self):
        self.validator = ImageBatchValidator()
        self.images = [
            SimpleUploadedFile(f"test{i}.jpg", b"file_content", "image/jpeg")
            for i in range(10)
        ]
        self.too_many_images = [
            SimpleUploadedFile(f"test{i}.jpg", b"file_content", "image/jpeg")
            for i in range(101)
        ]

    def test_valid_batch(self):
        try:
            self.validator(self.images)
        except ValidationError:
            self.fail("Validator raised ValidationError unexpectedly!")

    def test_too_many_images(self):
        with self.assertRaises(ValidationError) as cm:
            self.validator(self.too_many_images)
        self.assertIn("Number of images should not exceed 100", str(cm.exception))


class ValidateImagesFunctionTest(TestCase):
    def setUp(self):
        self.valid_images = [
            SimpleUploadedFile(f"valid{i}.jpg", b"file_content", "image/jpeg")
            for i in range(3)
        ]
        self.mixed_images = [
            SimpleUploadedFile("valid.jpg", b"file_content", "image/jpeg"),
            SimpleUploadedFile("invalid.txt", b"file_content", "text/plain"),
            SimpleUploadedFile("valid2.jpg", b"file_content", "image/jpeg")
        ]
        self.all_invalid = [
            SimpleUploadedFile("invalid1.txt", b"file_content", "text/plain"),
            SimpleUploadedFile("invalid2.txt", b"file_content", "text/plain")
        ]

    def test_all_valid_images(self):
        result = validate_images(self.valid_images)
        self.assertEqual(len(result), 3)

    def test_mixed_images(self):
        result = validate_images(self.mixed_images)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].name, "valid.jpg")
        self.assertEqual(result[1].name, "valid2.jpg")

    def test_all_invalid_images(self):
        with self.assertRaises(ValidationError) as cm:
            validate_images(self.all_invalid)
        self.assertIn("No valid images found", str(cm.exception))

    def test_empty_list(self):
        with self.assertRaises(ValidationError):
            validate_images([])