from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as gettext
import os


MAX_SIZE = 5 * 1024 * 1024
ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png']
MAX_NUMBER_OF_IMAGES = 100
MAX_LENGTH_OF_NAME = 255

class ImageValidator:
    allowed_extensions = ALLOWED_EXTENSIONS
    max_size = MAX_SIZE
    max_count = MAX_NUMBER_OF_IMAGES
    max_length = MAX_LENGTH_OF_NAME

    def __call__(self, value):
        self.validate_extension(value)
        self.validate_size(value)
        self.validate_name(value)
        return value

    def validate_extension(self, value):
        _, ext = os.path.splitext(value.name)
        ext = ext.lower().lstrip('.')
        if ext not in self.allowed_extensions:
            raise ValidationError(gettext(f"Unsupported file extension. Only {(', '.join(self.allowed_extensions))} are allowed."))

    def validate_size(self, value):
        if value.size > self.max_size:
            raise ValidationError(gettext('Image size should not exceed 5MB.'))

    def validate_name(self, value):
        if len(value.name) > self.max_length:
            raise ValidationError(gettext(f"Image name should not exceed {self.max_length} characters."))


class ImageBatchValidator:
    max_count = MAX_NUMBER_OF_IMAGES

    def __call__(self, value):
        if len(value) > self.max_count:
            raise ValidationError(gettext(f"Number of images should not exceed {self.max_count}."))
        return True


def validate_images(images) -> list:
    if not ImageBatchValidator()(images):
        raise ValidationError(gettext('Number of images should not exceed 100.'))
    validator = ImageValidator()
    validated_images = []
    for image in images:
        try:
            validator(image)
            print(f"Valid image: {image.name}")
            validated_images.append(image)
        except ValidationError as e:
            print(f"Validation error on image {image.name}: {e}")
    if len(validated_images) == 0:
        raise ValidationError(gettext('No valid images found.'))
    return validated_images