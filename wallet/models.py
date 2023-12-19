import threading
import string
import random
from time import time
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property
# from django.contrib.postgres.fields import hstore
from utils.constants import *
from utils.uuid import uuid4
from airtel.models import AirtelApplication
from momo.models import Product
from momo.managers import AccountManager
from user.models import User
from user.models import User as AuthUser

'''
It's common to use this kind of mechanism in Django middleware or
other components where the request context is not readily available, 
especially in cases where you want to track the current user in asynchronous or background tasks.

_thread_locals = threading.local(): Creates an instance of threading.local() to store thread-local data. This is used to store the current user.
_thread_locals.user = user: Stores the provided user object in the thread-local storage.
'''

_thread_locals = threading.local()

def set_current_user(user):
    _thread_locals.user = user


def get_current_user():
    return getattr(_thread_locals, 'user', None)


def remove_current_user():
    _thread_locals.user = None

class AuthSignature(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, editable=False,
                                   related_name='%(class)s_created')
    modified_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, editable=False,
                                    related_name='%(class)s_modified')
    created_on = models.DateTimeField(auto_now_add=True, db_index=True)
    modified_on = models.DateTimeField(auto_now=True, db_index=True)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        user = get_current_user()
        if user and user.is_authenticated:
            self.modified_by = user
            self.modified_on = timezone.now()
            if not self.id:
                self.created_by = user
        super(AuthSignature, self).save(*args, **kwargs)

    class Meta:
        abstract = True


REQUEST_STATUS = (
    (TRANS_SUCCESS, TRANS_SUCCESS),
    (TRANS_PENDING, TRANS_PENDING),
    (TRANS_FAILED, TRANS_FAILED)

)

WALLET_ACCOUNTS = (
    (TELECOM, "Telecom"),
    (WALLET, "Wallet")
)
ACCOUNT_TYPES = (
    (CONSUMER, "Consumer"),
    (EMPLOYEE, 'Employee')
)

TELECOMS = (
    (MTN, "MTN"),
    (AIRTEL, "AIRTEL"),
    (SYSTEM, "SYSTEM")
)

TRANSACTION_TYPE = (
    (PAYMENT, "Payment"),
    (DISBURSEMENT, "Disbursement"),
    (SYSTEM, "SYSTEM"),
    (REFUND, "Refund")
) 

TRANSACTION_STATUS = (
    (TRANS_PENDING, "Pending"),
    (TRANS_SUCCESS, "Success"),
    (TRANS_FAILED, "Failed")
)


def get_msisdn_prefix(msisdn: str):
    """
        assumes the msisdn is a standard one, e.g 256787411865
    """
    if msisdn:
        return msisdn[3:5]
    return None


def id_generator(size=16, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def generate_tid():
    """ generates a transaction Id """

    return f"TID{id_generator()}{int(time())}"


def generate_ref_id():
    """ generates a transaction Id"""
    now = int(time())
    return f"REF{now}"


def get_telecom(telephone):
    prefix = get_msisdn_prefix(telephone)
    if prefix in MTN_PREFIX:
        telecom = MTN
    elif prefix in AIRTEL_PREFIX:
        telecom = AIRTEL
    else:
        telecom = None
    return telecom


class User(AuthUser):
    """
    Proxy model to add additional functionality for the waller user
    """

    @property
    def name(self) -> str:
        return self.get_full_name()

    # @property
    # def account(self):
    #     return WalletAccount.accounts.get_account_by_user(self)

    @cached_property
    def profile(self):
        assert self.is_authenticated, "can't fetch user Profile for anonymous users"

        return UserProfile.objects.get_or_create(user=self)[0]

    def record_auth(self):
        """
        Records that this user authenticated
        """
        self.profile.last_auth_on = timezone.now()
        self.profile.save(update_fields=("last_auth_on",))

    def __str__(self):
        return self.name or self.username

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.profile = UserProfile.objects.get(user=self)
        except:
            self.profile = None

    class Meta:
        proxy = True


# class WalletAccount(AuthSignature):
#     """
#         Represents mobile money account.
#         To be used during double entry book-keeping.
#     """
#     uuid = models.UUIDField(unique=True, default=uuid4)
#     account_type = models.CharField(
#         max_length=10,
#         choices=WALLET_ACCOUNTS,
#         default=WALLET,
#         help_text="Represents the type of system supported accounts"
#     )
#     user = models.ForeignKey(
#         User, models.CASCADE,
#         help_text="User who owns this account, for authentication and access control",
#         null=True  # some accounts type  will not have users
#     )

#     telecom = models.CharField(
#         max_length=10,
#         choices=TELECOMS,
#         null=True,
#         help_text="Represents telecom to which this account belongs"
#     )

#     available_balance = models.DecimalField(
#         max_digits=10,
#         decimal_places=2,
#         help_text="How much available amount is on the account includes money pending for other transaction",
#         default=0.0
#     )
#     actual_balance = models.DecimalField(
#         max_digits=10,
#         decimal_places=2,
#         help_text="This is the actual balance an account user can transact",
#         default=0.0
#     )
#     meta_data = hstore.HStoreField(
#         blank=True,
#         null=True,
#         help_text="For storing transaction data"
#     )
#     product = models.ForeignKey(  # for MTN accounts
#         Product, on_delete=models.CASCADE,
#         null=True,
#     )
#     application = models.ForeignKey(
#         AirtelApplication, on_delete=models.CASCADE,
#         null=True
#     )
#     accounts = AccountManager()
#     objects = models.Manager()

#     def __str__(self):
#         if self.user:
#             if self.user.profile:
#                 return f"{self.user.name}-{self.user.profile.telephone}-wallet"
#             else:
#                 return f"{self.user.name}-wallet"
#         elif self.product:
#             return f"{self.product.name}-{self.telecom}"
#         else:
#             return f"{self.application.name}-{self.telecom}"

#     class Meta:
#         db_table = 'wallet_account'
#         ordering = ["-id"]


class RequestLogs(AuthSignature):
    status_code = models.IntegerField(default=200)
    status = models.CharField(
        max_length=15,
        choices=REQUEST_STATUS,
        default=TRANS_PENDING
    )
    end_point = models.URLField()
    request_type = models.CharField(
        max_length=100
    )
    request_body = models.TextField(blank=True, null=True)
    # request_body = hstore.HStoreField(blank=True, null=True)
    response_body = models.TextField(blank=True, null=True)
    # response_body = hstore.HStoreField(blank=True, null=True)

    class Meta:
        db_table = "wallet_requests_log"
        ordering = ["-id"]


class Transaction(AuthSignature):
    """
        Represents funds transaction with in the wallet
    """
    transaction_id = models.CharField(
        max_length=30
    )
    x_reference_id = models.CharField(
        max_length=36
    )
    transaction_type = models.CharField(
        max_length=30,
        choices=TRANSACTION_TYPE
    )
    external_request = models.ForeignKey(
        RequestLogs, on_delete=models.PROTECT,
        null=True
    )

    # debited_account = models.ForeignKey(
    #     WalletAccount, on_delete=models.PROTECT, related_name="debited_account",
    #     null=True
    # )

    # credited_account = models.ForeignKey(
    #     WalletAccount,
    #     on_delete=models.PROTECT,
    #     null=True,
    #     related_name="credited_account"
    # )

    status = models.CharField(
        max_length=20,
        choices=TRANSACTION_STATUS,
        default=TRANS_PENDING
    )
    currency = models.CharField(
        max_length=5,
        default=settings.DEFAULT_CURRENCY
    )
    msisdn = models.CharField(
        max_length=15,
        null=True
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()

    class Meta:
        ordering = ["-id"]


class AuditLog(AuthSignature):
    """
        Represent double entry accounting, where a pair will be entered.
    """

    transaction = models.ForeignKey(
        Transaction, on_delete=models.PROTECT
    )
    transaction_type = models.CharField(
        max_length=15,
        choices=TRANSACTION_TYPE
    )
    # account = models.ForeignKey(
    #     WalletAccount, on_delete=models.PROTECT
    # )
    amount = models.DecimalField(max_digits=10, decimal_places=2)


class UserProfile(AuthSignature):
    """
    Custom fields for wallet users
    """
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="userprofile")
    account_type = models.CharField(
        max_length=15,
        choices=ACCOUNT_TYPES,
        null=True
    )
    telephone = models.CharField(max_length=25, null=True)
    last_auth_on = models.DateTimeField(null=True)
    # wallet_account = models.ForeignKey(
    #     WalletAccount,
    #     on_delete=models.PROTECT,
    #     null=True,
    #     related_name="wallet_account")  # this represents the wallet account
    # telecom_account = models.ForeignKey(
    #     WalletAccount,
    #     on_delete=models.PROTECT,
    #     null=True,
    #     related_name="telecom_account")  # this represents the registered telephone mobile money account

    # operations = UserProfileManager()
    objects = models.Manager()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.telecom = get_telecom(self.telephone)

    def save(self, *args, **kwargs):
        # create wallet account
        user = get_current_user()
        if not self.telecom and self.telephone:
            self.telecom = get_telecom(self.telephone)

        # wallet_account_fields = dict(account_type=WALLET, user=self.user, telecom=SYSTEM)
        # telecom_account_fields = dict(account_type=TELECOM, user=self.user, telecom=self.telecom)
        # if user:
        #     wallet_account_fields.update(dict(created_by=user, modified_by=user))
        #     telecom_account_fields.update(dict(created_by=user, modified_by=user))

        # wallet_account, created = WalletAccount.objects.get_or_create(**wallet_account_fields)
        # telecom_account, ct = WalletAccount.objects.get_or_create(**telecom_account_fields)
        # if created and ct:
        #     self.wallet_account = wallet_account
        #     self.telecom_account = telecom_account
        #     self.save()
        #     super().save(*args, **kwargs)
        remove_current_user()

    def __str__(self):
        return f"{self.user.username}'s Profile"

    class Meta:
        ordering = ["-id"]


DEPOSIT = 'deposit'  # when a wallet user has deposited on their wallet
PAYMENT = PAYMENT  # when a consumer pays for a service
LIQUIDATE = "liquidate"  # When admin liquidates the account.
REFUND = "refund"

PAYMENT_TYPES = (
    (DEPOSIT, "Deposit"),
    (PAYMENT, "Payment"),
    (REFUND, "Refund")
)


class PaymentsLog(AuthSignature):
    """
        Any money that goes to the payments account is logged here as well for auditing especially in cases where we
        can not
    """
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.0
    )

    msisdn = models.CharField(
        max_length=15
    )
    transaction = models.ForeignKey(
        Transaction, on_delete=models.PROTECT
    )
    payment_type = models.CharField(
        max_length=20,
        choices=PAYMENT_TYPES,
        default=PAYMENT
    )
    status = models.CharField(
        max_length=20,
        default=TRANS_PENDING
    )

    description = models.TextField()

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     profile = UserProfile.operations.get_profile_by_msisdn(self.msisdn)
    #     self.wallet_account = profile.wallet_account if profile else None

    class Meta:
        db_table = 'wallet_payments_log'