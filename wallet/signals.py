import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Transaction, AuditLog
from utils.constants import *

ussd_logger = logging.getLogger("main")

ALLOWED_STATUSES = [TRANS_PENDING, TRANS_FAILED]


@receiver(post_save, sender=Transaction)
def add_double_entry(sender, instance, created, **kwargs):
    # create audit logs
    # Debit
    debit_amount = -1 * instance.amount  # this is a negative
    credit_amount = instance.amount
    # We only double entry when transaction is created and when/if it fails  i.e. status is PENDING or FAILED
    if instance.debited_account and instance.credited_account:
        if instance.status in ALLOWED_STATUSES:
            if created:
                # Only do this when instance is created
                if instance.status == TRANS_PENDING:
                    # Debit
                    AuditLog.objects.create(
                        transaction=instance,
                        transaction_type=DEBIT,
                        account=instance.debited_account,
                        amount=debit_amount
                    )
                    # Credit
                    AuditLog.objects.create(
                        transaction=instance,
                        transaction_type=CREDIT,
                        account=instance.credited_account,
                        amount=credit_amount
                    )
            else:
                if instance.status == TRANS_FAILED:
                    # reverse the above
                    # Credit the debited account
                    AuditLog.objects.create(
                        transaction=instance,
                        transaction_type=CREDIT,
                        account=instance.debited_account,
                        amount=credit_amount
                    )
                    # Debit the credited account
                    AuditLog.objects.create(
                        transaction=instance,
                        transaction_type=DEBIT,
                        account=instance.credited_account,
                        amount=debit_amount
                    )

        # change balances on debited and credited accounts accordingly
        if instance.status == TRANS_PENDING:
            # when transaction is created,
            # deduct actual balance of the debited account
            # increase the available balance of the credited account
            instance.debited_account.actual_balance += debit_amount
            instance.credited_account.available_balance += credit_amount
            message = f"PENDING transaction transaction id {instance.transaction_id} and reference id " \
                      f"{instance.x_reference_id} of amount {instance.currency}: {instance.amount} from account " \
                      f"{instance.debited_account} to account {instance.credited_account}"
            ussd_logger.info(message)

        elif instance.status == TRANS_SUCCESS:
            # when transaction is successful,
            # deduct the available balance of debited account
            # increase actual balance and available of credited account
            instance.debited_account.available_balance += debit_amount
            instance.credited_account.actual_balance += credit_amount
            message = f"SUCCESSFUL transaction transaction id {instance.transaction_id} and reference id " \
                      f"{instance.x_reference_id} of amount {instance.currency}: {instance.amount} from account " \
                      f"{instance.debited_account} to account {instance.credited_account}"
            ussd_logger.info(message)
        else:
            # if the transaction has failed, we kinda roll back
            # deduct the available balance of the credited account
            # increase the actual balance of the debited account
            instance.debited_account.actual_balance += credit_amount
            instance.credited_account.available_balance += debit_amount
            message = f"FAILED transaction transaction id {instance.transaction_id} and reference id " \
                      f"{instance.x_reference_id} of amount {instance.currency}: {instance.amount} from account " \
                      f"{instance.debited_account} to account {instance.credited_account}"
            ussd_logger.info(message)
        instance.debited_account.save()
        instance.credited_account.save()
