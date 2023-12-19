from enum import Enum

TRANS_SUCCESS = "SUCCESS"
TRANS_PENDING = "PENDING"
TRANS_FAILED = "FAILED"
DEBIT = "debit"
CREDIT = 'credit'
SYSTEM = "system"
PAYMENT = 'payment'
DEPOSIT = 'deposit'
DISBURSEMENT = 'disbursement'
REFUND = 'refund'

CONSUMER = "consumer"  # represents a consumer who pays through or to us
PRODUCT = "product"  # represents a product account e.g collections account
EMPLOYEE = "employee"  # such accounts will receive payments

TELECOM = 'telecom'
WALLET = "wallet"  # this represents the

MTN = 'mtn'
AIRTEL = 'airtel'

MTN_PREFIX = ["77", "78"]
AIRTEL_PREFIX = ["70", "75"]

CONTENT_APPLICATION_JSON = "application/json"
CONTENT_FORM_DATA = "application/x-www-form-urlencoded"

AGENT = 'Mondo'
CALL_SUCCESS = 'success'
CALL_ERROR = 'error'
DEFAULT_HEADERS = {
    "user-agent": AGENT,
    "Content-Type": CONTENT_APPLICATION_JSON,
    'Accept': '*/*'
}
GET = "GET"
POST = "POST"
HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_202_ACCEPTED = 202
SUCCESS_CODES = [HTTP_200_OK, HTTP_201_CREATED, HTTP_202_ACCEPTED]
SPECIAL_ERROR_STATUS_CODES = [409, 404]

# For Airtel codes
INCORRECT_PIN = "Incorrect Pin"
INSUFFICIENT_BALANCE = "Insufficient Balance"
LESS_MIN_AMOUNT = "Less Thank Minimum allowed amount"
NO_USER_PIN = "User didn't enter PIN"
EXCEED_LIMIT = "Exceeded allowed transaction limit"
TRANSACTION_REFUSED = "Transaction Refused"
DO_NOT_HONOR = "Do not honor"
NOT_PERMITTED_TO_PAYEE = "Transaction not permitted to Payee"
DUPLICATE_TRANSACTION = "Transaction with same information already exists in this system"
TRANSACTION_TIMED_OUT = "Transaction Timed Out"
INVALID_INITIATOR = "Initiator is invalid"
INCORRECT_MSISDN = "Mobile number entered is incorrect"
WALLET_DOES_NOT_EXIST = "The wallet is not configured."
MISSING_PARAMS = "Mandatory parameters are missing either in the header or body."
AMOUNT_NOT_ALLOWED = "Amount entered is not allowed for this transaction."
MAXIMUM_TRANSACTION_LIMIT = "Maximum transaction limit reached for the day"
INVALID_AMOUNT = "Amount entered is out of range with respect to defined limits"
INSUFFICIENT_FUNDS = "Insufficient Funds"


class ResponseCode(Enum):
    DP00800001000 = "Something went wrong"
    DP00800001001 = TRANS_SUCCESS
    DP00800001002 = INCORRECT_PIN
    DP00800001003 = EXCEED_LIMIT
    DP00800001004 = LESS_MIN_AMOUNT
    DP00800001005 = NO_USER_PIN
    DP00800001006 = TRANS_PENDING
    DP00800001007 = INSUFFICIENT_BALANCE
    DP00800001008 = TRANSACTION_REFUSED
    DP00800001009 = DO_NOT_HONOR
    DP00800001010 = NOT_PERMITTED_TO_PAYEE
    DP00900001000 = AMOUNT_NOT_ALLOWED
    DP00900001001 = "Transaction is Successful"
    DP00900001003 = MAXIMUM_TRANSACTION_LIMIT
    DP00900001004 = INVALID_AMOUNT
    DP00900001007 = INSUFFICIENT_FUNDS
    DP00900001009 = "Initiatee of the transaction is invalid"
    DP00900001010 = "Payer is not an allowed user"
    DP00900001011 = DUPLICATE_TRANSACTION
    DP00900001012 = INCORRECT_MSISDN
    DP00900001013 = TRANSACTION_REFUSED
    DP00900001014 = TRANSACTION_TIMED_OUT
    DP008001013 = TRANSACTION_REFUSED
    DP00800001024 = TRANSACTION_TIMED_OUT
    ROUTER001 = WALLET_DOES_NOT_EXIST
    ROUTER003 = MISSING_PARAMS
    ROUTER005 = "Country route is not configured"
    ROUTER006 = "Invalid country code provided."
    ROUTER007 = "Not authorized to perform any operations in the provided country."
    ROUTER112 = "Invalid currency provided."
    ROUTER114 = "An error occurred while validating the pin."
    ROUTER115 = "Pin you have entered is incorrect."
    ROUTER116 = "The encrypted value of the pin is incorrect. Kindly re-check the encryption mechanism."
    ROUTER117 = "An error occurred while generating the response."
    ESB000001 = "Something went wrong"
    ESB000004 = "An error occurred while initiating the payment"
    ESB000008 = "Field validation"
    ESB000011 = "Failed"
    ESB000014 = "An error occurred while fetching the transaction status"
    ESB000033 = "Invalid MSISDN Length"
    ESB000034 = "Invalid Country Name"
    ESB000035 = "Invalid Currency Code"
    ESB000036 = "Invalid MSISDN Length. MSISDN Length should be {0} and should start with 0"
    ESB000039 = "Vendor is not configured to do transaction in the country UG"
    ESB000041 = "External Transaction ID already exists."
    ESB000045 = "No Transaction Found With Provided Transaction Id."
