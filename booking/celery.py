from celery import Celery
from celery import Celery
from celery import Celery, CeleryConfig

app = Celery('booking_project')

app.conf.beat_schedule = {
    "adjust-time-slots-every-5-minutes": {
        "task": "your_app.tasks.adjust_slot_availability",
        "schedule": 300.0,  # Every 5 minutes
    }
},

