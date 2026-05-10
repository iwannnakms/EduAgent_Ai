from app.core.celery_app import celery_app
import time

task = celery_app.send_task("tasks.heartbeat")
print(task.id)
print(task.status)
time.sleep(2)
print(task.status)
