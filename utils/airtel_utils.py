from .constants import ResponseCode,TRANS_FAILED

def process_response_code(data):
    code = data["status"]["response_code"]
    options = dict()
    if code in [ResponseCode.DP00800001001.name, ResponseCode.DP00800001006.name]:
        options["status"] = ResponseCode[code].value
    else:
        options["status"] = TRANS_FAILED
        message = data.get("status", None).get("message", None)
        if message.strip() == "":
            message = None
        options["description"] = message if message else ResponseCode[code].value
    return options


def airtel_clean_msisdn(msisdn):
    """expect a standard msisdn in format msisdn"""
    return msisdn[3:]
