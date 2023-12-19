from django.db import models

MTN = 'mtn'
AIRTEL = 'airtel'

COLLECTIONS_PRODUCT = 'collection'
DISBURSEMENT_PRODUCT = 'disbursement'
REMITTANCE_PRODUCT = 'remittance'
 

class CollectionManager(models.Manager):
    def get_product(self):
        try:
            fields = dict(product_type=COLLECTIONS_PRODUCT)
            return super().get_queryset().filter(**fields).first()
        except:
            return None

    def get_queryset(self):
        return super().get_queryset().filter(product_type=COLLECTIONS_PRODUCT)


class DisbursementManager(models.Manager):
    def get_product(self):
        try:
            fields = dict(product_type=DISBURSEMENT_PRODUCT)
            return super().get_queryset().filter(**fields).first()
        except:
            return None

    def get_queryset(self):
        return super().get_queryset().filter(product_type=DISBURSEMENT_PRODUCT)


class APIUserManager(models.Manager):

    def get_product_user(self, product):
        try:
            fields = dict(product=product, is_active=True)
            return super().get_queryset().filter(**fields).first()
        except:
            return None


class AccountManager(models.Manager):
    def get_account_by_product(self, product):
        try:
            return super().get_queryset().get(product=product)
        except:
            return None

    def get_account_by_application(self, application):
        try:
            return super().get_queryset().get(application=application)
        except:
            return None

    def get_account_by_user(self, user):
        return super().get_queryset().filter(user=user)

    def get_account_by_user_and_type(self, user, acc_type):
        try:
            return super().get_queryset().get(user=user, account_type=acc_type)
        except:
            return None

    def get_collections_account_by_telecom(self, telecom):
        try:
            if telecom == AIRTEL:
                return super().get_queryset().get(telecom=AIRTEL, account_type="product")
            else:
                return super().get_queryset().get(telecom=MTN, account_type="product",
                                                  product__product_type=COLLECTIONS_PRODUCT)
        except:
            return None
