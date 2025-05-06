from django.db import models


class ImageRecord(models.Model):
    file_name = models.ImageField()
    image_random_num = models.IntegerField(default=None)

    def __str__(self):
        return str(self.pk)



