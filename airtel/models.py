from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from .managers import ApplicationManager
from utils.ussd import AuthSignature

BEARER_TOKEN = "bearer"
CLIENT_CREDENTIALS = "client_credentials"

GRANT_TYPES = (
    (CLIENT_CREDENTIALS, "Client Credentials"),
)

GENERATE_TOKEN = "airtel_generate_token"
GET_AIRTEL_USER = "get_airtel_user"
GET_ACCOUNT_BALANCE = "get_airtel_acc_balance"
COLLECTIONS_MAKE_PAYMENT = "airtel_collections_make_payment"
REFUND = "airtel_collections_refund"
PAYMENT_STATUS = "airtel_payment_status"
DISBURSE = "airtel_disburse"
DISBURSE_STATUS = "airtel_disburse_status"


class AirtelApplication(models.Model):

    @classmethod
    def allows_addition(cls):
        return cls.objects.all().count() < 1

    name = models.CharField(
        max_length=100,
        null=True
    )
    client_id = models.CharField(
        max_length=38
    )
    client_secret_key = models.CharField(
        max_length=38
    )
    grant_type = models.CharField(
        max_length=30,
        choices=GRANT_TYPES,
        default=CLIENT_CREDENTIALS
    )
    pin_enc_public_key = models.TextField()
    account_pin = models.CharField(
        max_length=4,
        help_text="Collections account PIN,Used for disbursements",
        null=True
    )
    hash_key = models.CharField(
        max_length=35,
        null=True
    )

    @property
    def access_token(self):
        try:
            return AirtelAccessToken.objects.get(application=self)
        except:
            return None

    objects = models.Manager()
    apps = ApplicationManager()

    class Meta:
        db_table = "airtel_application"
        ordering = ["-id"]

    def clean(self):
        super().clean()
        if not self.id and AirtelApplication.objects.exists():
            raise ValidationError("You can not add more entries maximum is just one")


# We only need one instance of the above class
class AirtelApplicationAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        base_perm = super().has_add_permission(request)
        if base_perm:
            count = AirtelApplication.objects.all().count()
            if count == 0:
                return True
            else:
                return False


class AirtelAccessToken(AuthSignature):
    application = models.ForeignKey(
        AirtelApplication, on_delete=models.CASCADE
    )
    access_token = models.TextField()

    token_type = models.CharField(
        max_length=30,
        default=BEARER_TOKEN
    )
    expires_in = models.IntegerField(
        default=3600
    )
    expired = models.BooleanField(
        default=False
    )

    def save(self, *args, **kwargs):
        user = self.application.created_by
        if user and user.is_authenticated:
            self.modified_by = user
            self.created_by = user
        super(AuthSignature, self).save(*args, **kwargs)

    def __str__(self):
        return self.access_token

    class Meta:
        db_table = "airtel_access_token"
