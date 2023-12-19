"""
Written by Keeya Emmanuel Lubowa
On 15th Sept, 2022
Email ekeeya@oddjobs.tech

This class helps us call endpoints without bothering on which telecom we are using
"""
import logging

from airtel.utils import AirtelCollections, AirtelDisbursement
from momo.utils import MomoCollectionService, MomoDisbursement
from utils.ussd import standard_urn
from .models import get_telecom, UserProfile, PAYMENT, DISBURSEMENT, PaymentsLog, WalletAccount, REFUND, \
    DEPOSIT

logger = logging.getLogger('main')
AIRTEL = "airtel"
MTN = "mtn"

SUPPORTED_TELECOMS = [AIRTEL, MTN]


def get_wallet_accounts_by_msisdn(msisdn):
    msisdn = standard_urn(msisdn)
    profile = UserProfile.operations.get_profile_by_msisdn(msisdn)
    return [profile.wallet_account, profile.telecom_account]


class Unity(object):
    """
        Allows us make calls without worrying on which how different telecoms work
    """

    def __init__(self, msisdn, payload=None):
        self.msisdn = standard_urn(msisdn)  # make it the format we support
        self.set_telecom()
        self.payload = payload
        if self.telecom == AIRTEL:
            self.collections_service = AirtelCollections()
            self.disbursement_service = AirtelDisbursement()
        else:
            self.collections_service = MomoCollectionService()
            self.disbursement_service = MomoDisbursement()
        self.collections = Unity.Collections(self)
        self.disbursement = Unity.Disbursement(self)

    def innerCollectionsFactory(self):
        return Unity.Collections(self)

    def innerDisbursementFactory(self):
        return Unity.Disbursement(self)

    @classmethod
    def get_collections_account(cls, telecom):
        return WalletAccount.accounts.get_collections_account_by_telecom(telecom)

    @classmethod
    def get_transaction_msisdn(cls, transaction):
        try:
            payment_log = PaymentsLog.objects.get(transaction=transaction)
            msisdn = payment_log.msisdn
            return msisdn
        except:
            error = f"Transaction id {transaction.transaction_id} is not attached to any msisdn"
            raise Exception(error)

    @classmethod
    def get_external_transaction_status(cls, transaction):
        # transactions with these types are the only ones that depend on external APIs
        transaction_types = [PAYMENT, DISBURSEMENT, DEPOSIT, REFUND]
        if transaction.transaction_type in transaction_types:
            # This means we have a payment log from where we can get the msisdn involved
            try:
                msisdn = cls.get_transaction_msisdn(transaction)
                transaction_type = transaction.transaction_type
                if msisdn:
                    service = cls(msisdn)
                    if transaction_type in [PAYMENT, DEPOSIT]:
                        response = service.collections_service.payment_status_inquiry(transaction)
                    elif transaction_type == REFUND:
                        if service.telecom == MTN:
                            response = service.disbursement.get_refund_status(transaction)
                        else:
                            response = service.collections.get_refund_status(transaction)
                    else:
                        response = service.disbursement.disbursement_status_inquiry(transaction)
                    return response
            except Exception as error:
                logger.exception(error)
        return dict(status="error", data="Internal Server error")

    def set_telecom(self):
        self.telecom = get_telecom(self.msisdn)

    class Collections(object):
        """
            Handles all collections services for both airtel and mtn
        """

        def __init__(self, outer):
            self.outer = outer

        def get_collections_account(self):
            return self.outer.collections_service.get_collections_account()

        def payment(self):
            try:
                return self.outer.collections_service.payments(self.outer.payload)
            except Exception as error:
                logger.exception(error)
                return [None, None]

        def payment_status_inquiry(self, transaction_id, message=None):
            return self.outer.collections_service.payment_status_inquiry(transaction_id, message)

        def get_refund_status(self, transaction):
            if self.outer.telecom == AIRTEL:
                response = self.outer.collections_service.payment_status_inquiry(transaction)
            else:
                response = self.outer.disbursement_service.refund_status(transaction)
            return response

        def refund(self):
            return self.outer.collections_service.refund(self.outer.payload)

        def handle_callback(self, payload):
            return self.outer.collections_service.mm_update_status(payload)

    class Disbursement(object):
        """
            Handle all disbursements from both airtel and mtn
        """

        def __init__(self, outer):
            self.outer = outer

        def disburse(self):
            return self.outer.disbursement_service.disburse(self.outer.payload)

        def refund(self):
            return self.outer.disbursement_service.refund(self.outer.payload)

        def get_refund_status(self, transaction):
            response = self.outer.disbursement_service.refund_status(transaction)
            return response

        def disbursement_status_inquiry(self, transaction):
            return self.outer.disbursement_service.disbursement_status_inquiry(transaction)

    class Miscellaneous(object):
        """
            Other wallet activities
        """

        def __init__(self, outer):
            self.outer = outer
