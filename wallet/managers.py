from django.conf import settings
from django.db import models

from utils.constants import MTN, MTN_PREFIX, AIRTEL, AIRTEL_PREFIX


class UserProfileManager(models.Manager):
    def filter_by_user(self, user):
        fields = dict(user=user, is_active=True)
        return super().get_queryset().filter(**fields)

    def filter_by_telecom(self, telecom):
        query_set = self.model.operations.none()
        if telecom == MTN:
            for prefix in MTN_PREFIX:
                p = f"{settings.DEFAULT_COUNTRY_CODE}{prefix}"
                query_set = query_set | super().get_queryset().filter(telephone__startswith=p)
        elif telecom == AIRTEL:
            for prefix in AIRTEL_PREFIX:
                p = f"{settings.DEFAULT_COUNTRY_CODE}{prefix}"
                query_set = query_set | super().get_queryset().filter(telephone__startswith=p)
        return query_set

    def with_accounts(self):
        return super().get_queryset().filter(wallet_account__isnull=False)

    def get_profile_by_msisdn(self, msisdn):
        try:
            return super().get_queryset().get(telephone=msisdn)
        except:
            return None


class TransactionsManager(models.Manager):
    def transaction_msisdn(self):
        pass
