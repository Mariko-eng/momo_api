"""
Written by Keeya Emmanuel Lubowa
On 14th Sept, 2022
Email ekeeya@oddjobs.tech
"""
import uuid

from django.conf import settings

from airtel.interfaces import BaseAirtelAuth
from airtel.models import AirtelApplication, GENERATE_TOKEN, AirtelAccessToken, GET_AIRTEL_USER, \
    COLLECTIONS_MAKE_PAYMENT, REFUND, DISBURSE, DISBURSE_STATUS, PAYMENT_STATUS
from momo.constants import GET_ACCOUNT_BALANCE
from utils.HttpRequests import make_api_call
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5 as Cipher_PKCS1_v1_5
from base64 import b64decode, b64encode
import hashlib
import hmac
import base64
import json

from utils.airtel_utils import process_response_code
from utils.callbacks import mm_update_status
from utils.constants import *
from utils.token_services import is_access_token_expired
from wallet.models import generate_tid, Transaction, generate_ref_id
from wallet.utils import WalletActions

TF = "TF"  # Transaction Failed
TS = "TS"  # Transaction Success


class AirtelAccessProvisioning(BaseAirtelAuth):

    def __init__(self, application):
        self.application = application

    def generate_access_token(self):
        """
            generate access token
        """

        fields = dict(application=self.application, expired=False)
        if AirtelAccessToken.objects.filter(**fields).exists():
            token = AirtelAccessToken.objects.get(**fields)
            # return one if we already have it, and it's not expired
            if not is_access_token_expired(token):
                return token

        url = f"{settings.AIRTEL_BASE_URL}/auth/oauth2/token"

        request_type = GENERATE_TOKEN
        payload = dict(
            client_id=self.application.client_id,
            client_secret=self.application.client_secret_key,
            grant_type=self.application.grant_type
        )
        options = dict(url=url, request_type=request_type, payload=payload)
        response, request_log = make_api_call(options, POST)
        if response["status"] == CALL_SUCCESS:
            response_data = response['data']
            try:
                token = AirtelAccessToken.objects.get(application=self.application)
                for key, value in response_data.items():
                    setattr(token, key, value)
                token.save()
            except:
                response_data["application"] = self.application
                token = AirtelAccessToken.objects.create(**response_data)
            return token
        return response["data"]

    def pin_encryption(self, pin):
        """
            Must encrypt pin before sending it in the body
        """
        public_key = self.application.pin_enc_public_key
        key_der = b64decode(public_key)
        key_pub = RSA.importKey(key_der)
        cipher = Cipher_PKCS1_v1_5.new(key_pub)
        cipher_text = cipher.encrypt(pin.encode())
        enc_pin = b64encode(cipher_text)
        return enc_pin

    def is_valid_callback_request(self, request_data, hash_msg) -> bool:
        raw = json.dumps(request_data)
        message = bytes(raw, 'utf-8')
        secret = bytes(self.application.hash_key, 'utf-8')
        signature = base64.b64encode(hmac.new(secret, msg=message, digestmod=hashlib.sha3_256).digest())
        return signature == hash_msg


class BaseService(object):
    model = AirtelApplication
    access_token = None
    application = None
    request_headers = {}

    def __init__(self):
        self.set_application()
        self.set_access_token()
        self.set_request_headers()

    def set_application(self):
        self.application = AirtelApplication.apps.get_app()

    @staticmethod
    def allowed_msisdn(msisdn):
        tel = str(msisdn)
        if len(tel) < 9:
            return None
        elif tel[0] == "0":
            return msisdn[1:]
        elif tel[:3] == settings.DEFAULT_COUNTRY_CODE:
            return tel[3:]
        elif tel[:4] == f"+{settings.DEFAULT_COUNTRY_CODE}":
            return tel[4:]
        else:
            return msisdn

    def set_access_token(self):
        provisioner = AirtelAccessProvisioning(self.application)
        response = provisioner.generate_access_token()
        if isinstance(response, AirtelAccessToken):
            self.access_token = response.access_token
            return self.access_token
        else:
            raise Exception(
                f"Failed to generate access toke due to: {response}"
            )

    def set_request_headers(self):
        self.request_headers = {
            "Authorization": f"Bearer {self.access_token}",
            "X-Country": settings.DEFAULT_COUNTRY,
            "X-Currency": settings.DEFAULT_CURRENCY
        }

    def encrypted_pin(self, pin):
        provisioner = AirtelAccessProvisioning(self.application)
        return provisioner.pin_encryption(pin)

    def get_airtel_user(self, msisdn):
        """
            KYC
            returns these responses
            {
                "data": {
                    "first_name": "Dealer",
                    "grade": "SUBS",
                    "is_barred": false,
                    "is_pin_set": true,
                    "last_name": "Test1",
                    "msisdn": 123456789,
                    "reg_status": "SUBS",
                    "registration": {
                      "status": "SUBS"
                    }
                  },
                  "status": {
                    "code": "200",
                    "message": "CALL_SUCCESS",
                    "result_code": "ESB000010",
                    "success": true
                  }
            }
        """
        request_type = GET_AIRTEL_USER
        url = f"{settings.AIRTEL_BASE_URL}/standard/v1/users/{msisdn}"
        options = dict(url=url, request_headers=self.request_headers, request_type=request_type)
        response, request_log = make_api_call(options)
        return response

    def get_account_balance(self):
        """
            Endpoint to return collections account balance
            returns
            {
                "data": {
                    "balance": "37,600.00",
                    "currency": "MGA",
                    "account_status" : "Active"
                  },
                  "status": {
                    "code": "200",
                    "message": "CALL_SUCCESS",
                    "result_code": "ESB000010",
                    "success": true
                  }
            }
        """
        request_type = GET_ACCOUNT_BALANCE
        url = f"{settings.AIRTEL_BASE_URL}/standard/v1/users/balance"
        options = dict(url=url, request_headers=self.request_headers, request_type=request_type)
        response, request_log = make_api_call(options)
        return response

    @staticmethod
    def handle_callback(transaction, payload):
        """
            when airtel posts on our callback, we update the transactions

            callback request body
            {
              "transaction": {
                "id": "BBZMiscxy",
                "message": "Paid UGX 5,000 to TECHNOLOGIES LIMITED Charge UGX 140, Trans ID MP210603.1234.L06941.",
                "status_code": "TS",
                "airtel_money_id": "MP210603.1234.L06941"
              }
            }
        """

        pass


class AirtelCollections(BaseService):
    """
        Implements airtel's collections product API functions
    """

    # def get_collections_account(self):
    #     actions = WalletActions(AIRTEL)
    #     return actions.get_product_wallet_account(self.application)

    def payments(self, payload: dict):
        """
            This API is used to request a payment from a consumer(Payer).
            The consumer(payer) will be asked to authorize the payment.
            After authorization, the transaction will be executed.

            payload should look something like
            {
                "msisdn":"755387533",
                "amount":10000
            }
            return a response similar to this

            {
              "data": {
                "transaction": {
                  "id": "125635757467364",
                  "status": "Success"
                }
              },
              "status": {
                "code": "200",
                "message": "CALL_SUCCESS",
                "result_code": "ESB000010",
                "response_code": "DP00800001006",
                "success": true
              }
            }
        """
        request_type = COLLECTIONS_MAKE_PAYMENT
        url = f"{settings.AIRTEL_BASE_URL}/merchant/v1/payments/"
        reference = generate_ref_id()
        transaction_id = generate_tid()
        msisdn = BaseService.allowed_msisdn(payload['msisdn'])
        amount = payload["amount"]
        data = dict(
            reference=reference,
            subscriber=dict(
                country=settings.DEFAULT_COUNTRY,
                currency=settings.DEFAULT_CURRENCY,
                msisdn=msisdn),
            transaction=dict(
                amount=amount,
                country=settings.DEFAULT_COUNTRY,
                currency=settings.DEFAULT_CURRENCY,
                id=transaction_id
            )
        )
        options = dict(url=url, request_headers=self.request_headers, payload=data, request_type=request_type)
        response, request_log = make_api_call(options, POST)
        transaction = None
        if response["status"] == CALL_SUCCESS:
            extra_options = process_response_code(response["data"])
            options = dict(transaction_id=transaction_id,
                           x_reference_id=reference,
                           external_request=request_log,
                           msisdn=payload['msisdn'],
                           transaction_type=PAYMENT,
                           amount=amount)
            options.update(extra_options)
            transaction = Transaction.objects.create(**options)
        return [response, transaction]

    def payment_status_inquiry(self, transaction):
        """
            This API gets the transaction status corresponding to the requested External Id.
            takes a transaction id

            response is similar to below
            transaction object
        """
        request_type = PAYMENT_STATUS
        url = f"{settings.AIRTEL_BASE_URL}/standard/v1/payments/{transaction.transaction_id}"
        options = dict(url=url, request_headers=self.request_headers, request_type=request_type)
        response, request_log = make_api_call(options)
        if response["status"] == CALL_SUCCESS:
            transaction = mm_update_status(response["data"], AIRTEL)
            response["transaction"] = transaction
        return response

    def refund(self, payload):
        """
            This API is used to make full refunds to consumers.
            takes a transaction ID from the above payments operation

            response is similar to:

            {
                  "data": {
                    "transaction": {
                      "airtel_money_id": "CI210104.1549.C00029",
                      "status": "SUCCESS"
                    }
                  },
                  "status": {
                    "code": "200",
                    "message": "SUCCESS",
                    "result_code": "ESB000010",
                    "success": true
                  }
            }

        """
        request_type = REFUND
        url = f"{settings.AIRTEL_BASE_URL}/standard/v1/payments/refund"
        transaction = payload.get("transaction")
        new_transaction_id = generate_tid()
        account_to_debit = payload["account_to_debit"]
        payload = dict(transaction=dict(airtel_money_id=transaction.transaction_id))
        options = dict(url=url, request_headers=self.request_headers, payload=payload, request_type=request_type)
        response, request_log = make_api_call(options, POST)
        new_transaction = None
        if response["status"] == CALL_SUCCESS:
            # This is a single transaction
            # Note that we don't have a credit account in the system
            new_transaction = Transaction.objects.create(
                transaction_id=new_transaction_id,
                external_request=request_log,
                transaction_type=REFUND,
                amount=transaction.amount,
                msisdn=transaction.msisdn,
                debited_account=account_to_debit
            )
        return [response, new_transaction]


class AirtelDisbursement(BaseService):
    """
        Implements airtel's disbursements product API functions
    """

    def disburse(self, payload):
        """
            This API is used to transfer an amount from the own account to a payee account.
            Payload must contain body
            {
                "msisdn":"755387533",
                "amount":1000,
                "pin":"123434"
            }
            Returns the following response

            {
              "data": {
                "transaction": {
                  "reference_id": "18*****3354",
                  "airtel_money_id": "partner-ABCD07026984141",
                  "id": "ABCD07026984141"
                }
              },
              "status": {
                "code": "200",
                "message": "Trans.ID :  CI2****************02. You have sent *****   to 999****39,B*******MA . Your available balance is ** 5****.21.",
                "result_code": "ESB000010",
                "response_code": "DP00900001001",
                "success": true
              }
            }
        """
        request_type = DISBURSE
        url = f"{settings.AIRTEL_BASE_URL}/standard/v1/disbursements/"
        msisdn = BaseService.allowed_msisdn(payload['msisdn'])
        amount = payload["amount"]
        account_to_debit = payload["account_to_debit"]
        transaction_id = generate_tid()
        pin = payload["pin"]
        reference = str(uuid.uuid4())
        request_body = dict(
            payee=dict(msisdn=msisdn),
            reference=reference,
            pin=self.encrypted_pin(pin),
            transaction=dict(
                amount=float(amount),
                id=transaction_id
            )
        )
        payer_msg = f"Disbursement transaction {transaction_id} of {settings.DEFAULT_CURRENCY}:" \
                    f"{amount:,} from {account_to_debit} to {msisdn}"
        options = dict(url=url, request_headers=self.request_headers, payload=request_body, request_type=request_type)
        response, request_log = make_api_call(options, POST)
        transaction = None
        if response["status"] == CALL_SUCCESS:
            transaction = Transaction.objects.create(
                transaction_id=transaction_id,
                x_reference_id=reference,
                external_request=request_log,
                transaction_type=DISBURSEMENT,
                amount=amount,
                msisdn=payload['msisdn'],
                debited_account=account_to_debit,
                description=payer_msg
            )
        return [response, transaction]

    def disbursement_status_inquiry(self, transaction):
        """
            This API endpoint returns the disbursement transaction status
            Takes in the transaction id
            returns
            {
              "data": {
                "transaction": {
                  "id": "ABCD07026984141",
                  "message": "Your Request is submitted Successfully.",
                  "status": "TS"
                }
              },
              "status": {
                "code": "200",
                "message": "CALL_SUCCESS",
                "result_code": "ESB000010",
                "response_code": "DP00900001001",
                "success": true
              }
            }
        """
        request_type = DISBURSE_STATUS
        url = f"{settings.AIRTEL_BASE_URL}/standard/v1/disbursements/{transaction.transaction_id}"
        options = dict(url=url, request_headers=self.request_headers, request_type=request_type)
        response, request_log = make_api_call(options)
        if response["status"] == CALL_SUCCESS:
            transaction = mm_update_status(response["data"], AIRTEL)
            response["transaction"] = transaction
        return response
