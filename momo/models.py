from django.db import models
from django.utils import timezone
from momo.managers import COLLECTIONS_PRODUCT, DISBURSEMENT_PRODUCT, REMITTANCE_PRODUCT ,CollectionManager, DisbursementManager, \
    APIUserManager
from utils.uuid import generate_uuid
from utils.ussd import AuthSignature


PRODUCT_TYPES = (
    (COLLECTIONS_PRODUCT, "Collection"),
    (DISBURSEMENT_PRODUCT, "Disbursement"),
    (REMITTANCE_PRODUCT, "Remittance"),
)

SAND_BOX = 'sandbox'
PRODUCTION = 'production'

TARGET_ENV = (
    (SAND_BOX, SAND_BOX),
    (PRODUCTION, PRODUCTION)
)

class Product(models.Model):
    name = models.CharField(
        max_length=200,
        help_text="Product name"
    )

    product_type = models.CharField(
        max_length=20,
        choices=PRODUCT_TYPES,
        help_text="Represents MTN MOMO API product"
    )
    primary_key = models.CharField(
        max_length=33,
        help_text="MOMO Product subscription primary key"
    )
    secondary_key = models.CharField(
        max_length=33,
        help_text="MOMO Product subscription secondary key"
    )


    def __str__(self):
        return self.name

    class Meta:
        ordering = ["-id"]

class Collection(Product):
    objects = CollectionManager()

    class Meta:
        proxy = True


class Disbursement(Product):
    objects = DisbursementManager()

    class Meta:
        proxy = True

'''
Meta class with proxy=True: The Meta class with proxy = True indicates that this model is a proxy model. 
Proxy models don't create database tables on their own; instead, 
they operate on the same database table as the model they inherit from (Product in this case).
'''


class APIUser(AuthSignature):
    x_reference_id = models.UUIDField(
        max_length=36,
        unique=True,
        default=generate_uuid,
        help_text="User x-reference Id"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        help_text="A product which this User authenticates"
    )
    target_environment = models.CharField(
        max_length=15,
        choices=TARGET_ENV,
        help_text="Environment in which the user operates"
    )
    callback_host = models.URLField(
        help_text="We shall send this in a header as call back when creating the API user",
    )
    ocp_apim_subscription_key = models.CharField(
        max_length=33,
        null=True
    )

    api_key = models.CharField(
        max_length=33,
        help_text="This will be used to generate an Access token",
        null=True
    )
    objects = models.Manager()
    users = APIUserManager()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            token = AccessToken.objects.get(api_user=self)
            self.access_token = token
        except:
            self.access_token = None

    def __str__(self):
        return self.x_reference_string

    def save(self, *args, **kwargs):
        self.ocp_apim_subscription_key = self.product.primary_key
        super().save(*args, **kwargs)

    @property
    def x_reference_string(self):
        return str(self.x_reference_id)

    class Meta:
        db_table = "momo_api_user"
        ordering = ["-id"]


ACCESS_TOKEN = 'access_token'
ZERO_AUTH_TOKEN = "0auth2"

TOKEN_TYPES = (
    (ACCESS_TOKEN, ACCESS_TOKEN),
    (ZERO_AUTH_TOKEN, ZERO_AUTH_TOKEN)
)


class AccessToken(AuthSignature):
    api_user = models.ForeignKey(
        APIUser,
        on_delete=models.CASCADE
    )
    access_token = models.TextField()
    token_type = models.CharField(
        max_length=30,
        choices=TOKEN_TYPES,
        default=ACCESS_TOKEN
    )
    expires_in = models.IntegerField(
        default=3600
    )
    expired = models.BooleanField(
        default=False
    )
    scope = models.CharField(
        max_length=100,
        null=True
    )

    refresh_token = models.CharField(
        max_length=50,
        null=True,
    )

    refresh_token_expired_in = models.IntegerField(
        default=0
    )
    created_on = models.DateTimeField(default=timezone.now, editable=False, blank=True)

    def __str__(self):
        return self.access_token

    class Meta:
        db_table = "momo_access_token"
        ordering = ["-id"]


CREATE_USER = 'create_user'
GET_API_USER = 'get_api_user'
GENERATE_API_KEY = 'generate_api_key'
GENERATE_ACCESS_TOKEN = 'generate_access_token'
GET_USER_INFO = 'get_user_info'
GET_ACCOUNT_BALANCE = 'get_account_balance'
VALIDATE_ACCOUNT_HOLDER_STATUS = 'validate_account_holder_status'
# Collection
REQUEST_TO_PAY = 'request_to_pay'
REQUEST_TO_PAY_DELIVERY_NOTIFICATION = 'request_to_pay_delivery_notification'
REQUEST_TO_PAY_TRANSACTION_STATUS = 'request_to_pay_transaction_status'
REQUEST_TO_WITHDRAW = 'request_to_withdraw'
REQUEST_TO_WITHDRAW_STATUS = 'request_to_withdraw_transaction_status'
REQUEST_TYPES = ()

# DISBURSEMENT

DEPOSIT = 'deposit'
DEPOSIT_TRANSACTION_STATUS = 'deposit_transaction_status'
REFUND = 'refund'
GET_REFUND_STATUS = 'get_refund_status'
TRANSFER = 'transfer'
GET_TRANSFER_STATUS = 'get_transfer_status'



