from django.db import models
from PIL import Image

class TermsAndConditions(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class SlidePhoto(models.Model):
    image = models.ImageField(upload_to='slide_photos/')
    description = models.CharField(max_length=255)

    def __str__(self):
        return self.description

    def save(self,*args,**kwargs):
        super(SlidePhoto, self).save(*args, **kwargs)

        img = Image.open(self.image.path)

        if img.height > 200 or img.width > 500:
            new_img_size = (500, 200)
            img.thumbnail(new_img_size)
            img.save(self.image.path)