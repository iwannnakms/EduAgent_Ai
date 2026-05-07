import os
from celery import Celery

os.environ["CELERY_BROKER_URL"] = "redis://localhost:6379/2"
app = Celery("test", broker="redis://localhost:6379/0")
print(app.conf.broker_url)
