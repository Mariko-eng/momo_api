import logging
import uuid
import base64
import requests

from django.conf import settings
from .models import Product, APIUser,AccessToken
from utils.constants import *
from .models import REQUEST_TO_PAY, REQUEST_TO_PAY_DELIVERY_NOTIFICATION
from .models import REQUEST_TO_PAY_TRANSACTION_STATUS
from .models import REQUEST_TO_WITHDRAW, REQUEST_TO_WITHDRAW_STATUS
from .models import DEPOSIT_TRANSACTION_STATUS,REFUND,GET_REFUND_STATUS
from .models import TRANSFER, GET_TRANSFER_STATUS
from .models import Collection, COLLECTIONS_PRODUCT
from .models import Disbursement,DISBURSEMENT_PRODUCT
from .models import SAND_BOX, PRODUCTION,  ACCESS_TOKEN
from wallet.models import Transaction, PaymentsLog, RequestLogs, generate_tid
from utils.callbacks import mm_update_status

from utils.token_services import is_access_token_expired

logger = logging.getLogger('main')

CALL_SUCCESS = 'success'
CONTENT_APPLICATION_JSON = "application/json"
CONTENT_FORM_DATA = "application/x-www-form-urlencoded"
ZERO_AUTH2_TOKEN = '0auth2_token'
DEFAULT_ACCOUNT_HOLDER_TYPE = "MSISDN"

def process_response(request):
    if request.status_code in SUCCESS_CODES:
        try:
            response = request.json()
        except:
            response = request.text
        return dict(status=CALL_SUCCESS, status_code=request.status_code, data=response)
    elif request.status_code in SPECIAL_ERROR_STATUS_CODES:
        try:
            error_data = request.json()
        except:
            error_data = request.text
        error_log = f"Call failed due to: {error_data}"
        logger.error(error_log)
        return dict(status=CALL_ERROR, status_code=request.status_code, data=error_log)
    else:
        error_log = f"Call failed with status code {request.status_code}: {request.text}"
        logger.error(error_log)
        return dict(status=CALL_ERROR,
                    status_code=request.status_code,
                    data=f"Call failed with status code"
                            f":{request.status_code}")
    
def add_log_request(response, end_point, request_type, payload=None):

    if isinstance(response["data"], dict):
        response_body = response["data"]
    else:
        response_body = dict(data=response["data"])

    log_data = dict(status_code=response["status_code"], 
                    status=response["status"], 
                    end_point= end_point,
                    request_type=request_type, 
                    response_body= str(response_body))
    if payload:
        log_data.update(dict(request_body = payload))

    request_log = RequestLogs.objects.create(**log_data)
    return(request_log)

    # request_log = RequestLogs.objects.create(**log_data)
    # return request_log

class MomoUserProvisioning():
    
    def __init__(self, product: Product):
        self.product = product


    def create_user(self):
        """
            create an api user for momo api authentication
        """
        # request_type = CREATE_USER
        # payload = dict(providerCallbackHost=settings.MTN_MOMO_CALLBACK_URL)
        # request_headers = {
        #     "X-Reference-Id": x_reference_id,
        #    "Ocp-Apim-Subscription-Key": self.product.primary_key
        # }

        url = f"{settings.MTN_MOMO_BASE_URL}/{settings.MTN_MOMO_API_VERSION}/apiuser"
        
        x_reference_id = str(uuid.uuid4())

        headers = {
            'X-Reference-Id': x_reference_id,
            'Content-Type': CONTENT_APPLICATION_JSON,
            'Cache-Control': 'no-cache',
            'Ocp-Apim-Subscription-Key': self.product.primary_key
        }

        # Request body
        data = {
            "providerCallbackHost": settings.MTN_MOMO_CALLBACK_URL
        }

        response = requests.post(url, headers=headers, json=data)
        response = process_response(response)

        logger.info("Create user request made to External MOMO API")
        status = response['status']
        if status == CALL_SUCCESS:
            # Save the User to database
            if APIUser.objects.filter(
                product = self.product, 
                target_environment=SAND_BOX if settings.MTN_MOMO_TARGET_ENV == 'sandbox' else PRODUCTION,
                ocp_apim_subscription_key=self.product.primary_key).exists():
                
                api_user = APIUser.objects.filter(
                    product = self.product, 
                    target_environment=SAND_BOX if settings.MTN_MOMO_TARGET_ENV == 'sandbox' else PRODUCTION,
                    ocp_apim_subscription_key=self.product.primary_key
                    ).first()
            else:
                api_user = APIUser.objects.create(
                    product = self.product, 
                    target_environment=SAND_BOX if settings.MTN_MOMO_TARGET_ENV == 'sandbox' else PRODUCTION,
                    ocp_apim_subscription_key=self.product.primary_key)
            
            api_user.x_reference_id = x_reference_id
            api_user.callback_host = settings.MTN_MOMO_CALLBACK_URL
            api_user.save()

            msg = f"API User with x_reference_id: {x_reference_id} has been created"
            print(msg)
            logger.info(msg)
            return dict(status=CALL_SUCCESS, data=msg, status_code=201, api_user=api_user.pk)
        return response

    @staticmethod
    def get_user(api_user: APIUser):
        """
            Get api created user
        """
        # request_type = GET_API_USER
        # request_headers = {
        #     "X-Reference-Id": api_user.x_reference_string,
        #     "Ocp-Apim-Subscription-Key": api_user.product.primary_key
        # }

        url = f"{settings.MTN_MOMO_BASE_URL}/{settings.MTN_MOMO_API_VERSION}/apiuser/{api_user.x_reference_string}"

        headers = {
            'Content-Type': CONTENT_APPLICATION_JSON,
            'Cache-Control': 'no-cache',
            'Ocp-Apim-Subscription-Key': api_user.product.primary_key,
        }

        # Request body
        data = {}

        response = requests.get(url, headers=headers, json=data)
        response = process_response(response)

        return response['data']

    @staticmethod
    def generate_api_key(api_user: APIUser):

        """
            generate api key
        """
        # request_type = GENERATE_API_KEY
        # request_headers = {
        #     "X-Reference-Id": api_user.x_reference_string,
        #     "Ocp-Apim-Subscription-Key": api_user.product.primary_key
        # }

        url = f"{settings.MTN_MOMO_BASE_URL}/{settings.MTN_MOMO_API_VERSION}/apiuser/{api_user.x_reference_string}/apikey"

        headers = {
            'Content-Type': CONTENT_APPLICATION_JSON,
            'Cache-Control': 'no-cache',
            'Ocp-Apim-Subscription-Key': api_user.product.primary_key,
        }

        # Request body
        data = {}

        response = requests.post(url, headers=headers, json=data)
        response = process_response(response)

        if response["status"] == CALL_SUCCESS:
            response_data = response['data']
            # add API key to user object
            api_user.api_key = response_data['apiKey']
            api_user.save()
            logger.info(f"Generated API KEY {api_user.api_key} for api User {api_user.x_reference_string} in "
                             f"{settings.MTN_MOMO_TARGET_ENV} env")
            # return api_user.api_key
            return dict(status=CALL_SUCCESS, data="API KEY CREATED!", status_code=201, api_key=api_user.api_key)
        return response

    def bc_authorize(self, api_user: APIUser, product_name):
        """
            This operation is uder to claim a consent for the requested scopes
        """
        url = f"{settings.MTN_MOMO_BASE_URL}/{product_name}/{settings.MTN_MOMO_API_VERSION}/bc-authorize"

        headers = {
            "X-Target-Environment": SAND_BOX if settings.MTN_MOMO_TARGET_ENV == 'sandbox' else PRODUCTION,
            "X-Callback-Url": api_user.callback_host,
            "Ocp-Apim-Subscription-Key": api_user.product.primary_key,
            "Content-Type": CONTENT_FORM_DATA
        }

        # Request body
        data = {}

        response = requests.post(url, headers=headers, json=data)
        response = process_response(response)
        # TODO this is not clear on the docs, let's come to it later

    @staticmethod
    def generate_access_token(api_user: APIUser, product_name: object, token_type: object = ACCESS_TOKEN) -> object:
        """
            generate access token
        """
        # request_type = GENERATE_ACCESS_TOKEN
        fields = dict(api_user=api_user, expired=False)
        if AccessToken.objects.filter(**fields).exists():
            token = AccessToken.objects.get(**fields)
            # return one if we already have it, and it's not expired
            if not is_access_token_expired(token): 
                return token

        reference_id_and_api_key  = str(api_user.x_reference_id) +':'+ api_user.api_key
        encoded_bytes = base64.b64encode(reference_id_and_api_key.encode('utf-8'))
        encoded_str = encoded_bytes.decode('utf-8')

        if token_type == ACCESS_TOKEN:
            url = f"{settings.MTN_MOMO_BASE_URL}/{product_name}/token/"
            request_headers = {
                'Authorization': 'Basic '+ encoded_str,
                "Ocp-Apim-Subscription-Key": api_user.product.primary_key
            }
        else:
            url = f"{settings.MTN_MOMO_BASE_URL}/{product_name}/0auth2/token/"
            request_headers = {
                'Authorization': 'Basic '+ encoded_str,
                "X-Target-Environment": SAND_BOX if settings.MTN_MOMO_TARGET_ENV == 'sandbox' else PRODUCTION,
                "Ocp-Apim-Subscription-Key": api_user.product.primary_key
            }

        # Request body
        data = {}

        request = requests.post(url, headers=request_headers, json=data)
        response = process_response(request)

        if response["status"] == CALL_SUCCESS:
            response_data = response["data"]
            response_data.update(dict(api_user=api_user))
            try:
                token = AccessToken.objects.get(api_user=api_user)
                for key, value in response_data.items():
                    setattr(token, key, value)
                token.expired = False
                token.save()
            except:
                token = AccessToken.objects.create(**response_data)
            return token
        return response["data"]


class BaseService(object):
    model = Product
    api_user = None
    product = None
    momo_user_provider = None
    access_token = None
    base_url = settings.MTN_MOMO_BASE_URL
    api_version = settings.MTN_MOMO_API_VERSION
    environment = SAND_BOX if settings.MTN_MOMO_TARGET_ENV == 'sandbox' else PRODUCTION

    def __init__(self):
        try:
            self.set_product()
            self.set_api_user()
            self.set_access_token()
        except Exception as error:
            logger.exception(error)

    def set_product(self):
        product = self.model.objects.get_product()
        if product:
            self.product = product
            self.momo_user_provider = MomoUserProvisioning(self.product)
        else:
            raise Exception(
                f"No active MOMO product configured for product of class"
            )

    def set_api_user(self):
        user = APIUser.users.get_product_user(self.product)
        if user:
            self.api_user = user
        else:
            raise Exception(
                f"No active api user configured for this momo product {self.product.product_type}"
            )

    def set_access_token(self):
        token_type = ACCESS_TOKEN if settings.MTN_MOMO_TARGET_ENV == 'sandbox' else ZERO_AUTH2_TOKEN
        response = self.momo_user_provider.generate_access_token(self.api_user, self.product.product_type, token_type)

        if isinstance(response, AccessToken):
            self.access_token = response
            return self.access_token
        else:
            raise Exception(
                f"Failed to generate access toke due to: {response}"
            )

    def get_user_info(self, account_holder_msisdn):
        """
            This operation returns personal information of the account holder.
            The operation does not need any consent by the account holder.
            Returns the following user info
            {
                "sub": "0",
                "name": "Sand Box",
                "given_name": "Sand",
                "family_name": "Box",
                "birthdate": "1976-08-13",
                "locale": "sv_SE",
                "gender": "MALE",
                "updated_at": 1662393300
            }
        """
        # request_type = GET_USER_INFO
        url = f"{self.base_url}/{self.product.product_type}/{self.api_version}/accountholder/msisdn/" \
              f"{account_holder_msisdn}/basicuserinfo"

        request_headers = {
            "Authorization": f"Bearer {self.access_token.access_token}",
            "X-Target-Environment": self.environment,
            "Ocp-Apim-Subscription-Key": self.product.primary_key
        }

        response = requests.get(url, headers=request_headers)
        response = process_response(response)

        return response['data']

    def get_account_balance(self, iso_currency=None):
        """
            returns a tuple of available balance and currency
            returns error string if request fails
            example response ("10000", "UGX")
        """
        # request_type = GET_ACCOUNT_BALANCE
        if iso_currency:
            url = f"{self.base_url}/{self.product.product_type}/{self.api_version}/account/balance/{iso_currency}"
        else:
            url = f"{self.base_url}/{self.product.product_type}/{self.api_version}/account/balance"
        request_headers = {
            "Authorization": f"Bearer {self.access_token.access_token}",
            "X-Target-Environment": self.environment,
            "Ocp-Apim-Subscription-Key": self.product.primary_key
        }

        response = requests.get(url, headers=request_headers)
        response = process_response(response)

        if response['status'] == CALL_SUCCESS:
            return response['data']['availableBalance'], response['data']['currency']
        return response['data']

    def validate_account_holder_status(self, account_holder_id, account_holder_type=DEFAULT_ACCOUNT_HOLDER_TYPE):
        """
            Operation is used to check if an account holder is registered and active in the system.
            returns a boolean
        """
        url = f"{self.base_url}/{self.product.product_type}/{self.api_version}/accountholder/{account_holder_type}/" \
              f"{account_holder_id}/active"
        # request_type = VALIDATE_ACCOUNT_HOLDER_STATUS
        request_headers = {
            "Authorization": f"Bearer {self.access_token.access_token}",
            "X-Target-Environment": self.environment,
            "Ocp-Apim-Subscription-Key": self.product.primary_key
        }

        response = requests.get(url, headers=request_headers)
        response = process_response(response)

        if response["status"] == CALL_SUCCESS:
            return response["data"]["result"]
        else:
            return response["data"]


class MomoCollectionService(BaseService):
    model = Collection
    product_type = COLLECTIONS_PRODUCT

    def payments(self, payload: dict):
        """
            This operation is used to request a payment from a consumer (Payer).
            The payer will be asked to authorize the payment.
            The transaction will be executed once the payer has authorized the payment.
            The request to pay will be in status PENDING until the transaction is authorized or declined by the payer
            or it is timed out by the system.
            Status of the transaction can be validated by using the GET /requesttopay/<resourceId>
            The payload to this function is a dictionary similar to this
            {
                "msisdn":"9999999",
                "amount":"1000"
            }
            return x_reference_id string or error dict
        """
        request_type = REQUEST_TO_PAY
        url = f"{self.base_url}/{self.product_type}/{self.api_version}/requesttopay"
        x_reference_id = str(uuid.uuid4())
        request_headers = {
            "Authorization": f"Bearer {self.access_token.access_token}",
            "X-Target-Environment": self.environment,
            "Ocp-Apim-Subscription-Key": self.product.primary_key,
            "X-Reference-Id": x_reference_id
        }
        if self.environment != "sandbox":
            request_type.update({"X-Callback-Url": self.api_user.callback_host})
        transaction_id = generate_tid()
        amount = payload["amount"]
        msisdn = payload["msisdn"]

        transaction_type = payload["transaction_type"]
        # account_to_credit = payload["account_to_credit"]
        payer_msg = f"Payment {transaction_id} of {settings.DEFAULT_CURRENCY}:{amount:,} from {msisdn}"
        
        request_body = dict(
            amount=amount,
            currency=settings.DEFAULT_CURRENCY,
            externalId=transaction_id,
            payer=dict(
                partyIdType="MSISDN",
                partyId=msisdn
            ),
            payerMessage=payer_msg,
            payeeNote=f"Receive a payment of {settings.DEFAULT_CURRENCY}:{amount:,} from {msisdn}"
        )

        request = requests.post(url, headers=request_headers, json=request_body)

        response = process_response(request)
        request_log = add_log_request(response, url, request_type, request_body)

        transaction = None
        if response.get("status") == CALL_SUCCESS:
            # This is a single transaction
            # Note that we don't have an account to debit
            transaction = Transaction.objects.create(
                transaction_id=transaction_id,
                x_reference_id=x_reference_id,
                external_request=request_log,
                # external_request=None,
                transaction_type=transaction_type,
                # credited_account=account_to_credit,
                amount=amount,
                msisdn=msisdn,
                description=payer_msg
            )
            # Add Payment Log
            description = f"A deposit of {settings.DEFAULT_CURRENCY}: {amount} from {msisdn} has been initiated"
            PaymentsLog.objects.create(
                amount=amount,
                msisdn=msisdn,
                transaction=transaction,
                payment_type=DEPOSIT,
                description=description,
                status=transaction.status
            )

        return [response, transaction]

    def request_to_pay_delivery_notification(self, x_reference_id, message):
        """
            This operation is used to send additional Notification to an End User.
            return success string else error dict
        """
        request_type = REQUEST_TO_PAY_DELIVERY_NOTIFICATION
        url = f"{self.base_url}/{self.product_type}/{self.api_version}/requesttopay/{x_reference_id}/deliverynotification"
        request_headers = {
            "Authorization": f"Bearer {self.access_token}",
            "X-Target-Environment": self.environment,
            "Ocp-Apim-Subscription-Key": self.product.primary_key,
            "notificationMessage": message
        }
        request_body = dict(notificationMessage=message)

        request = requests.post(url, headers=request_headers, json=request_body)
        response = process_response(request)
        # add_log_reequest(response, url, request_type, request_body)


        if response['status'] == CALL_SUCCESS:
            return CALL_SUCCESS
        else:
            return response

    def payment_status_inquiry(self, transaction_id, send_notification=False):
        """
            This operation is used to get the status of a request to pay.
            X-Reference-Id that was parsed in the post is used as reference to the request.

            returns transaction status dict as e.g.
            {
              "amount": 100,
              "currency": "UGX",
              "financialTransactionId": 23503452,
              "externalId": 947354,
              "payer": {
                "partyIdType": "MSISDN",
                "partyId": 4656473839.0
              },
              "status": "SUCCESSFUL"
            }
            If send_notification is parsed, a notification is sent to the user
        """
        request_type = REQUEST_TO_PAY_TRANSACTION_STATUS
        if Transaction.objects.filter(transaction_id = transaction_id).exists():
            transaction = Transaction.objects.filter(transaction_id = transaction_id).first()
        else:
            return dict(data="Transaction not found!", status_code=400)
        
        url = f"{self.base_url}/{self.product_type}/{self.api_version}/requesttopay/{transaction.x_reference_id}"
        request_headers = {
            "Authorization": f"Bearer {self.access_token}",
            "X-Target-Environment": self.environment,
            "Ocp-Apim-Subscription-Key": self.product.primary_key,
        }

        request = requests.get(url, headers=request_headers)
        # print(request.json())
        response = process_response(request)

        
        if response['status'] == CALL_SUCCESS:
            transaction = mm_update_status(response["data"], MTN)
            response["transaction"] = transaction
            if send_notification:
                # TODO construct appropriate message in 160 x-ters
                message = f"Transaction"
                self.request_to_pay_delivery_notification(transaction.x_reference_id, message)
        return response

    def request_to_withdraw(self, payload):
        """
            This operation is used to request a withdrawal (cash-out) from a consumer (Payer). The payer will be asked
            to authorize the withdrawal. The transaction will be executed once the payer has authorized the withdraw
            request format look more like
            {
              "payeeNote": "string",
              "externalId": "string",
              "amount": "string",
              "currency": "string",
              "payer": {
                "partyIdType": "MSISDN",
                "partyId": "string"
              },
              "payerMessage": "string"
            }
        """
        request_type = REQUEST_TO_WITHDRAW
        url = f"{self.base_url}/{self.product_type}/{self.api_version}/requesttowithdraw"
        x_reference_id = str(uuid.uuid4())
        request_headers = {
            "Authorization": f"Bearer {self.access_token}",
            "X-Target-Environment": self.environment,
            "X-Reference-Id": x_reference_id,
            "Ocp-Apim-Subscription-Key": self.product.primary_key
        }
        if self.environment != "sandbox":
            request_type.update({"X-Callback-Url": self.api_user.callback_host})

        request = requests.get(url, headers=request_headers)
        response = process_response(request)

        if response["status"] == CALL_SUCCESS:
            # TODO x_reference_id Schedule this for the transaction status checker daemon.
            pass
        return response

    def request_to_withdraw_transaction_status(self, x_reference_id):
        """
            This operation is used to get the status of a request to withdraw.
            X-Reference-Id that was passed in the post is used as reference to the request.
        """
        request_type = REQUEST_TO_WITHDRAW_STATUS
        url = f"{self.base_url}/{self.product_type}/{self.base_url}/requesttowithdraw/{x_reference_id}"
        request_headers = {
            "Authorization": f"Bearer {self.access_token}",
            "X-Target-Environment": self.environment,
            "Ocp-Apim-Subscription-Key": self.product.primary_key
        }
    
        request = requests.get(url, headers=request_headers)
        response = process_response(request)

        if response["status"] == CALL_SUCCESS:
            # TODO update request log response params
            # TODO x_reference_id Schedule this for the transaction status checker daemon.
            # TODO record in transaction table
            pass
        return response


class MomoDisbursementService(BaseService):
    model = Disbursement
    """
        Represents the momo disbursement product API
    """
    product_type = DISBURSEMENT_PRODUCT

    def disburse(self, payload):
        """
            Transfer operation is used to transfer an amount from the own account to a payee account.
            Status of the transaction can validated by using the GET /transfer/{referenceId}

            Payload must include the following
            {
                "amount":"10000",
                "msisdn":"256787622512",
                "account_to_debit":transaction_object
            }
        """
        request_type = TRANSFER
        url = f"{self.base_url}/{self.product_type}/{self.api_version}/transfer"
        x_reference_id = str(uuid.uuid4())
        request_headers = {
            "Authorization": f"Bearer {self.access_token}",
            "X-Target-Environment": self.environment,
            "X-Reference-Id": x_reference_id,
            "Ocp-Apim-Subscription-Key": self.product.primary_key
        }
        if self.environment != "sandbox":
            request_type.update({"X-Callback-Url": self.api_user.callback_host})
            
        msisdn = payload["msisdn"]
        amount = payload["amount"]
        # account_to_debit = payload["account_to_debit"]
        transaction_id = generate_tid()
        payer_msg = f"Disbursement transaction {transaction_id} of {settings.DEFAULT_CURRENCY}:" \
                    f"{amount:,} from Collections to {msisdn}"
        msg = f"Disbursement transaction {transaction_id} of {settings.DEFAULT_CURRENCY}:" \
              f"{amount:,} to {msisdn}"
        request_body = dict(
            amount=amount,
            currency=settings.DEFAULT_CURRENCY,
            externalId=transaction_id,
            payee=dict(
                partyIdType="MSISDN",
                partyId=msisdn
            ),
            payerMessage=payer_msg,
            payeeNote=f"To receive a payment of {settings.DEFAULT_CURRENCY}:{amount:,} from {msisdn}"
        )

        request = requests.post(url, headers=request_headers, json=request_body)
        response = process_response(request)

        request_log = add_log_request(response, url, request_type, request_body)

        transaction = None
        if response['status'] == CALL_SUCCESS:
            transaction = Transaction.objects.create(
                transaction_id=transaction_id,
                x_reference_id=x_reference_id,
                external_request=request_log,
                transaction_type=DISBURSEMENT,
                amount=amount,
                msisdn=msisdn,
                # debited_account=account_to_debit,
                description=msg
            )
        return [response, transaction]

    def disbursement_status_inquiry(self, transaction):
        """
            This operation is used to get the status of a transfer. X-Reference-Id that was passed in the post is used as reference to the request.
            response structure
            {
              "amount": "string",
              "currency": "string",
              "financialTransactionId": "string",
              "externalId": "string",
              "payee": {
                "partyIdType": "MSISDN",
                "partyId": "string"
              },
              "payerMessage": "string",
              "payeeNote": "string",
              "status": "PENDING",
              "reason": {
                "code": "PAYEE_NOT_FOUND",
                "message": "string"
              }
            }
        """
        request_type = GET_TRANSFER_STATUS
        url = f"{self.base_url}/{self.product_type}/{self.api_version}/transfer/{transaction.x_reference_id}"
        request_headers = {
            "Authorization": f"Bearer {self.access_token}",
            "X-Target-Environment": self.environment,
            "Ocp-Apim-Subscription-Key": self.product.primary_key
        }

        request = requests.get(url, headers=request_headers)
        response = process_response(request)

        if response["status"] == CALL_SUCCESS:
            transaction = mm_update_status(response["data"], MTN)
            response["transaction"] = transaction
        return response


    def refund(self, payload):
        """
            refund operation is used to refund an amount from the owner’s account to a payee account.
            Status of the transaction can be validated by using the GET /refund/{referenceId}

            Payload must be a dict with these mandatory fields :
            {
              "amount": "string",
              "transaction": "Transaction to refund",
            }
        """
        request_type = REFUND
        x_reference_id = str(uuid.uuid4())
        url = f"{self.base_url}/{self.product_type}/{self.api_version}/refund"
        request_headers = {
            "Authorization": f"Bearer {self.access_token}",
            "X-Target-Environment": self.environment,
            "X-Reference-Id": x_reference_id,
            "Ocp-Apim-Subscription-Key": self.product.primary_key
        }
        if self.environment != "sandbox":
            request_type.update({"X-Callback-Url": self.api_user.callback_host})

        transaction_id = payload["transaction_id"]

        transaction = Transaction.objects.get(id = transaction_id)

        amount = float(transaction.amount)
        msisdn = payload["msisdn"]
        new_transaction_id = generate_tid()

        # account_to_debit = payload["account_to_debit"]
        payer_msg = f"Refund payment {new_transaction_id} of {settings.DEFAULT_CURRENCY}:{amount:,} from" \
                    f" {settings.COMPANY_NAME} to {msisdn}"
        request_body = dict(
            amount=amount,
            currency=settings.DEFAULT_CURRENCY,
            externalId=new_transaction_id,
            payerMessage=payer_msg,
            payeeNote=f"Receive a refund payment of {settings.DEFAULT_CURRENCY}:"
                      f"{amount:,} from {settings.COMPANY_NAME}",
            referenceIdToRefund=transaction.x_reference_id
        )

        request = requests.post(url, headers=request_headers, payload=request_body)
        response = process_response(request)

        request_log = add_log_request(response, url, request_type, request_body)

        new_transaction = None
        if response["status"] == CALL_SUCCESS:
            # This is a single transaction
            # Note that we don't have a credit account in the system
            new_transaction = Transaction.objects.create(
                transaction_id=new_transaction_id,
                x_reference_id=x_reference_id,
                external_request=request_log,
                transaction_type=REFUND,
                amount=amount,
                msisdn=msisdn,
                # debited_account=account_to_debit,
                description=payer_msg
            )
        return [response, new_transaction]


    def refund_status(self, transaction):
        """
            This operation is used to get the status of a refund. X-Reference-Id that was passed in the post is used as reference to the request.
        """
        request_type = GET_REFUND_STATUS
        url = f"{self.base_url}/{self.product_type}/{self.api_version}/refund/{transaction.x_reference_id}"
        request_headers = {
            "Authorization": f"Bearer {self.access_token}",
            "X-Target-Environment": self.environment,
            "Ocp-Apim-Subscription-Key": self.product.primary_key
        }
        
        request = requests.get(url, headers=request_headers)
        response = process_response(request)

        if response["status"] == CALL_SUCCESS:
            transaction = mm_update_status(response["data"], MTN)
            response["transaction"] = transaction
        return response

