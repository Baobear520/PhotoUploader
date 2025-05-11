import os
import logging
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = ('jpg', 'jpeg', 'png', 'pdf', 'webp')
MAX_SIZE = 5 * 1024 * 1024 # 5MB
MAX_LENGTH = 255
BATCH_MAX_COUNT = 100



class ImageValidator:
    def __init__(
            self,
            allowed_extensions=ALLOWED_EXTENSIONS,
            max_size=MAX_SIZE,
            max_length=MAX_LENGTH
    ):
        self.allowed_extensions = allowed_extensions
        self.max_size = max_size
        self.max_length = max_length

    def __call__(self, image):
        """Validate a single image file"""
        self.validate_extension(image)
        self.validate_size(image)
        self.validate_name(image)
        return True

    def validate_extension(self, image):
        ext = os.path.splitext(image.name)[1][1:].lower()
        if ext not in self.allowed_extensions:
            raise ValidationError(
                _("Unsupported extension '%(ext)s'. Allowed: %(allowed)s"),
                params={
                    'ext': ext,
                    'allowed': ', '.join(self.allowed_extensions)
                }
            )

    def validate_size(self, image):
        if image.size > self.max_size:
            raise ValidationError(
                _("File size %(size).2fMB exceeds maximum %(max).2fMB"),
                params={
                    'size': image.size / (1024 * 1024),
                    'max': self.max_size / (1024 * 1024)
                }
            )

    def validate_name(self, image):
        if len(image.name) > self.max_length:
            raise ValidationError(
                _("Name too long (%(length)d > %(max)d characters)"),
                params={'length': len(image.name), 'max': self.max_length}
            )


class ImageBatchValidator:
    def __init__(self, max_count=BATCH_MAX_COUNT):
        self.max_count = max_count

    def __call__(self, images):
        """Validate a batch of images"""
        if len(images) > self.max_count:
            raise ValidationError(
                _("Too many images (%(count)d > %(max)d)"),
                params={'count': len(images), 'max': self.max_count}
            )

        validator = ImageValidator()
        valid_images = []

        for image in images:
            try:
                validator(image)
                valid_images.append(image)
                logger.info("Valid image: %s", image.name)
            except ValidationError as e:
                logger.warning("Invalid image %s: %s", image.name, str(e))

        if not valid_images:
            raise ValidationError(_("No valid images provided"))

        return valid_images