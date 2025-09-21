# backend/app/api/v1/endpoints/sync.py
from fastapi import APIRouter, status, BackgroundTasks
from app.services import sync_service

router = APIRouter()

@router.post("/run-sync", status_code=status.HTTP_202_ACCEPTED, tags=["Sync"])
async def trigger_sync(background_tasks: BackgroundTasks):
    """
    Triggers the background task to sync MongoDB with Pinecone.
    """
    background_tasks.add_task(sync_service.run_sync)
    return {"message": "Synchronization task has been started in the background."}