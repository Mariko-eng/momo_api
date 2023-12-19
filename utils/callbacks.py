import logging

from django.conf import settings
from utils.airtel_utils import process_response_code
from utils.constants import *
from wallet.models import Transaction
from wallet.models import PaymentsLog
#from wallet.models import WalletAccount
from wallet.models import generate_tid, generate_ref_id


logger = logging.getLogger('main')

TRANS_SUCCESS_LIST = ["SUCCESSFUL", CALL_SUCCESS, "Success", True]

def book_keeping(transaction_id, status, message):
    try: 
        transaction = Transaction.objects.get(transaction_id=transaction_id)
        if transaction.status not in [TRANS_SUCCESS, TRANS_FAILED]:
            log = PaymentsLog.objects.get(transaction=transaction)
            if status in TRANS_SUCCESS_LIST:
                if log.payment_type == DEPOSIT:
                    print("log.payment_type == DEPOSIT")
                elif log.payment_type == PAYMENT:
                    print("log.payment_type == PAYMENT")
                else:
                    print("log.payment_type")

                if status in TRANS_SUCCESS_LIST:
                    log.status = TRANS_SUCCESS
                    log.save()
                else:
                    log.status = status
                    log.save()
                transaction.status = TRANS_SUCCESS
                transaction.save()
            else:
                if status == TRANS_FAILED:
                    print("status == TRANS_FAILED")
                transaction.status = status
                transaction.description = message
                transaction.save()
        return transaction
    except Exception as error:
        logger.exception(error)
        return None
    


# def book_keeping1(transaction_id, status, message):
#     try:
#         transaction = Transaction.objects.get(transaction_id=transaction_id)
#         if transaction.status not in [TRANS_SUCCESS, TRANS_FAILED]:
#             log = PaymentsLog.objects.get(transaction=transaction)
#             collections_account = WalletAccount.accounts.get_collections_account_by_telecom(MTN)
#             if status in TRANS_SUCCESS_LIST:
#                 if log.payment_type == DEPOSIT:
#                     # then we have to do some extra bookkeeping

#                     # let's modify the both available and actual balances of the collections account b'se we
#                     # are literary putting this money here
#                     collections_account.available_balance += transaction.amount
#                     collections_account.actual_balance += transaction.amount
#                     tid = generate_tid()
#                     reference = generate_ref_id()

#                     credit_account = log.wallet_account
#                     message = f"Deposit transfer of {settings.DEFAULT_CURRENCY}: " \
#                               f"{transaction.amount:,} from account {collections_account} to account " \
#                               f"{credit_account} wallet"
#                     # # First debit the collections account and credit the wallet account of this msisdn
#                     # # Just record a new transaction, and the signal will handle the accounting
#                     if collections_account and credit_account:
#                         trans = Transaction.objects.create(
#                             transaction_id=tid,
#                             x_reference_id=reference,
#                             transaction_type="system",
#                             amount=transaction.amount,
#                             msisdn=transaction.msisdn,
#                             # debited_account=collections_account,
#                             # credited_account=credit_account,
#                             description=message,
#                             status=TRANS_PENDING  # let's first make it pending, so that can create audit logs
#                             # with  our signal from signals.add_double_entry
#                         )
#                         trans.status = TRANS_SUCCESS
#                         trans.save()
#                         # If it is a deposit, the collections available balance should be returned after the
#                         # signal has done its accounting because we actually leave the money on the
#                         # collections account
#                         collections_account.available_balance += transaction.amount
#                 elif log.payment_type == PAYMENT:
#                     # For payments increase both the available and actual balances of the collections account
#                     collections_account.available_balance += transaction.amount
#                     collections_account.actual_balance += transaction.amount
#                 else:
#                     # In case of a refund or a disbursement deduct the transaction from available balance,
#                     # Note that we have already deducted from actual balance in the API serializers
#                     collections_account.available_balance -= transaction.amount

#                 if status in TRANS_SUCCESS_LIST:
#                     log.status = TRANS_SUCCESS
#                     log.save()
#                 else:
#                     log.status = status
#                     log.save()
#                 transaction.status = TRANS_SUCCESS
#                 transaction.save()
#             else:
#                 if status == TRANS_FAILED:
#                     # on failure, we need to do certain special actions for refunds and disbursements
#                     # since we do not have a revert in the signal for such kind of transacitions,
#                     # lets undo what we did in the serializers by returning the actual balance
#                     if log.payment_type in [REFUND, DISBURSEMENT]:
#                         collections_account.actual_balance += transaction.amount
#                 transaction.status = status
#                 transaction.description = message
#                 transaction.save()
#             # collections_account.save()
#         return transaction
#     except Exception as error:
#         logger.exception(error)
#         return None


def mm_update_status(payload, telecom=None):
    """
        Request body from momo looks like this for MTN
        {
            "financialTransactionId": "799607689",
            "externalId": "TID6434323267362343",
            "amount": "35",
            "currency": "EUR",
            "payer": {
                "partyIdType": "MSISDN",
                "partyId": "787411859"
            },
            "status": "SUCCESSFUL"
        }
        and for Airtel
        {
              "data": {
                "transaction": {
                  "airtel_money_id": "C3648.00993.538XX.XX67",
                  "id": "8334msn88",
                  "message": "success",
                  "status": "TS"
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
    if telecom == MTN:
        transaction_id = payload["externalId"]
        status = payload["status"]
        message = payload["payerMessage"]
    else:
        transaction_id = payload["data"]["transaction"]["id"]
        extra_options = process_response_code(payload["status"]["response_code"])
        status = extra_options.get("status")
        message = extra_options.get("description")
    transaction = book_keeping(transaction_id, status, message)
    return transaction


def airtel_callback(payload):
    """
    Airtel makes this request body to our callback URL
        {
          "transaction": {
            "id": "BBZMiscxy",
            "message": "Paid UGX 5,000 to TECH LIMITED, Trans ID MP210603.1234.L06941.",
            "status_code": "TS",
            "airtel_money_id": "MP210603.1234.L06941"
          },
        "hash":"zITVAAGYSlzl1WkUQJn81kbpT5drH3koffT8jCkcJJA="
        }
    """
    STATUSES = dict(TS=TRANS_SUCCESS, TF=TRANS_FAILED)
    transaction_id = payload["transaction"]["id"]
    status = STATUSES[payload["transaction"]["status_code"]]
    message = payload["transaction"]["message"]
    # TODO authenticate callback
    transaction = book_keeping(transaction_id, status, message)
    return transaction
