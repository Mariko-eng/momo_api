from celery import shared_task
from django_celery_beat.models import IntervalSchedule, PeriodicTask
import logging

logger  = logging.getLogger("momo")


@shared_task
def printSomething():
    logger.info("Mariko!")
    # print("Do Somehting!")

def create_interval_scheduler(interval : int):
    schedule, created = IntervalSchedule.objects.get_or_create(
        every=interval,
        period = IntervalSchedule.SECONDS
    )
    return schedule

def create_perioidic_print_task():
    if PeriodicTask.objects.filter(name = "test task").exists():
        obj = PeriodicTask.objects.filter(name = "test task").first()
        obj.delete()

    PeriodicTask.objects.get_or_create(
        interval=create_interval_scheduler(5),  # run every 5 seconds,
        name = "test task",
        task = "momo.tasks.printSomething"
    )
