from celery import Celery
from science import attribute_event

# Setting up Celery
celery_app = Celery(
    "tasks",
    broker="redis://localhost:6379/0", # Redis for tasks queuing
    backend="redis://localhost:6379/0", # Redis for passing/storing results
    task_serializer="pickle",
    result_serializer="pickle",
    accept_content=["json", "pickle"]
)

@celery_app.task(name="attribution")
def attribution(event):
    return attribute_event(event)