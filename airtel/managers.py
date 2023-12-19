from django.db import models


class ApplicationManager(models.Manager):
    def get_app(self):
        try:
            return super().get_queryset().get()
        except:
            raise Exception("There is no application Configured for Airtel Money API access")

