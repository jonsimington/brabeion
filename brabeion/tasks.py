from celery.task import Task

from johnny.utils import celery_enable_all
celery_enable_all()


class AsyncBadgeAward(Task):
    ignore_result = True
    
    def run(self, badge, state, **kwargs):
        badge.actually_possibly_award(**state)
