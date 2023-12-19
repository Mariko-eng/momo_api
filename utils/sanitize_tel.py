def ussd_support_tel(msisdn):
    if msisdn[:4] == "tel:":
        # clean this to just 256772354367
        return msisdn[5:]
    else:
        return msisdn