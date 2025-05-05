from django.db import models


class Photo(models.Model):
    image_random_num = models.IntegerField(default=None)

    def __str__(self):
        return f"Image's random number{self.image_random_num}"



