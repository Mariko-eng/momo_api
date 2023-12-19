"""
Written by Keeya Emmanuel Lubowa
On 22nd Sept, 2022
Email ekeeya@oddjobs.tech

These are celery background takes
"""
import logging

from celery import shared_task
import requests
from django.conf import settings
from django_celery_beat.models import IntervalSchedule, PeriodicTask

from utils.constants import TRANS_PENDING, SYSTEM, CALL_ERROR
from .models import Transaction
# from mondo.wallet.unity import Unity

logger = logging.getLogger('main')
#options = dict(timeout=(settings.API_CONNECTION_TIMEOUT, settings.API_RESPONSE_TIMEOUT))


def get_or_create_interval(interval: int):
    schedule, created = IntervalSchedule.objects.get_or_create(
        every=interval,  # in seconds
        period=IntervalSchedule.SECONDS,
    )
    return schedule


def update_status(transaction):
    response = Unity.get_external_transaction_status(transaction)
    if response["status"] == CALL_ERROR:
        logger.error(f"Failed to update the status of transaction {transaction.transaction_id}")
    else:
        logger.info(f"Successfully to update the status of transaction {transaction.transaction_id}")


@shared_task
def update_transaction_statuses():
    """
        This task will check the database and call the /api/wallet/v1/transaction/status.json?transaction_id=TID82XJ2TGC12EPXW381663590722
        on every external transaction that is in PENDING mode
    """

    pending_transactions = Transaction.objects.filter(status=TRANS_PENDING).exclude(transaction_type=SYSTEM)
    [update_status(transaction) for transaction in pending_transactions]


def creat_status_updater_task():
    PeriodicTask.objects.get_or_create(
        interval=get_or_create_interval(5),  # run every 5 seconds,
        name="Update Pending transactions",
        task="mondo.wallet.tasks.update_transaction_statuses"
    )
