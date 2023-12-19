import logging
import requests
from django.conf import settings
from requests import ConnectionError, ReadTimeout

from utils.constants import *
from wallet.models import RequestLogs

logger = logging.getLogger('main')


def generate_header(custom_headers: dict):
    headers = DEFAULT_HEADERS

    for key, value in custom_headers.items():
        headers.update({key: value})

    return headers


class HttpAdaptor(object):
    def __init__(self, method=GET, *args, **kwargs):
        self.url = None
        self.request_param = None
        self.method = method
        self.headers = DEFAULT_HEADERS
        self.request_headers = None
        self.payload = dict()
        self.request_type = None
        self.auth = ()
        for kwarg in kwargs:
            setattr(self, kwarg, kwargs[kwarg])

        self.log_request()

    def set_headers(self, custom_headers):
        self.headers = generate_header(custom_headers)

    def log_request(self):
        msg = f"Request made to of type {self.request_type} made to URL: {self.url} with payload {self.payload}:"
        logger.info(msg)

    @property
    def send_request(self):
        try:
            if self.request_headers:
                # append request headers to default header if parsed
                self.headers = generate_header(self.request_headers)

            options = dict(headers=self.headers, timeout=(
                settings.API_CONNECTION_TIMEOUT, settings.API_RESPONSE_TIMEOUT))
            if len(self.auth) > 0:
                options.update(dict(auth=self.auth))
            if self.method == "GET":
                request = requests.get(self.url, **options)
            else:
                options.update(dict(json=self.payload))
                request = requests.post(self.url, **options)
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
                error_log = f"Call at url {self.url} failed due to: {error_data}"
                logger.error(error_log)
                return dict(status=CALL_ERROR, status_code=request.status_code, data=error_log)
            else:
                error_log = f"Call at url {self.url} failed with status code {request.status_code}: {request.text}"
                logger.error(error_log)
                return dict(status=CALL_ERROR,
                            status_code=request.status_code,
                            data=f"Call at url {self.url}  failed with status code"
                                 f":{request.status_code}")
        except ReadTimeout as error:
            error_log = f"API call to {self.url} not return a response: {str(error)}"
            logger.error(error_log)
            return dict(status=CALL_ERROR, status_code=500, data=error_log)
        except ConnectionError as error:
            error_log = f"Connection to API server and url {self.url}  refused: {str(error)}"
            logger.error(error_log)
            return dict(status=CALL_ERROR, status_code=500, data=error_log)
        except Exception as error:
            error_log = f"Error occurred due to : {str(error)}"
            logger.error(error_log)
            logger.exception(error)
            return dict(status=CALL_ERROR, status_code=500, data=error_log)


def make_api_call(options: dict, method=GET):
    if method == GET:
        client = HttpAdaptor(**options)
    else:
        client = HttpAdaptor(POST, **options)
    response = client.send_request
    if isinstance(response["data"], dict):
        response_body = response["data"]
    else:
        response_body = dict(data=response["data"])
    log_data = dict(status_code=response["status_code"], status=response["status"], end_point=options["url"],
                    request_type=options['request_type'], response_body=response_body)
    if "payload" in options:
        log_data.update(dict(request_body=options["payload"]))
    request_log = RequestLogs.objects.create(**log_data)
    return [response, request_log]
