"""Celery Utils"""

from celery import Task
from celery.schedules import maybe_schedule
from django_celery_beat.models import PeriodicTask, PeriodicTasks
from django_celery_beat.schedulers import DatabaseScheduler

from django.db.transaction import atomic


class CorrelatorScheduler(DatabaseScheduler):
    """Correlator Database Scheduler Class"""

    def setup_schedule(self):
        self.logger.info("CorrelatorScheduler: Setting up Schedule")
        with atomic():
            self.cleanup_obsolete_tasks()
        return super().setup_schedule()

    def cleanup_obsolete_tasks(self):
        """Deletes celery tasks that are no onger defined"""
        obsolete_tasks = PeriodicTask.objects.exclude(task__startswith="celery.").exclude(
            name__in=self.app.conf.beat_schedule.keys()
        )
        if obsolete_tasks:
            obsolete_tasks_list = list(obsolete_tasks.values_list("name", flat=True))
            self.logger.warning("CorrelatorScheduler: Obsolete tasks to be deleted: %s", obsolete_tasks_list)
            obsolete_tasks.delete()
            PeriodicTasks.update_changed()


class CorrelatorPeriodicTask(Task):  # pylint: disable=abstract-method
    """Correlator Periodic Task Class"""

    run_every = None
    relative = False

    def __init__(self) -> None:
        if not hasattr(self, "run_every") or self.run_every is None:
            raise NotImplementedError("Periodic Tasks must have a run_every attribute.")
        self.run_every = maybe_schedule(self.run_every, self.relative)
        super().__init__()

    @classmethod
    def on_bound(cls, app):
        app.conf.beat_schedule[cls.name] = {"task": cls.name, "schedule": cls.run_every, "relative": cls.relative}
        return super().on_bound(app)
