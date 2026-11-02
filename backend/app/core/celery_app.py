from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "documind_worker",
    broker=settings.CELERY_BROKER_URL or settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)


@celery_app.task(name="tasks.process_document_async")
def process_document_async(document_id: str, organization_id: str, file_path: str, mime_type: str):
    from app.agents.graph import execute_document_workflow
    from app.agents.state import DocuMindState
    state = DocuMindState(
        document_id=document_id,
        organization_id=organization_id,
        file_path=file_path,
        mime_type=mime_type
    )
    return execute_document_workflow(state)

