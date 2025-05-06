from django.contrib import admin

from photos.models import ImageRecord


class ImageRecordAdmin(admin.ModelAdmin):
    pass


admin.site.register(ImageRecord, ImageRecordAdmin)