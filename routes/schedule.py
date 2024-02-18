import uuid

from fastapi import APIRouter, Depends

from database.schedule.schedule_service import (
    get_schedule_by_reference,
    logic,
    get_schedule_by_reference_with_devices, get_schedule_with_usage,
)
from routes.get_db import get_db

schedule_router = APIRouter()


@schedule_router.get("/schedule/{schedule_reference}")
async def get_schedule(schedule_reference: uuid.UUID, db=Depends(get_db)):
    return get_schedule_by_reference(db=db, schedule_reference=schedule_reference)


@schedule_router.put("/schedule/{simulation_reference}")
async def method_create_schedule(simulation_reference: uuid.UUID, db=Depends(get_db)):
    return logic(db=db, simulation_reference=simulation_reference)


@schedule_router.get("/schedule/{schedule_reference}/devices")
async def get_schedule(schedule_reference: uuid.UUID, db=Depends(get_db)):
    return get_schedule_by_reference_with_devices(
        db=db, schedule_reference=schedule_reference
    )


@schedule_router.get("/schedule/{schedule_reference}/usage")
async def get_schedule_usage_by_reference(schedule_reference: uuid.UUID, db=Depends(get_db)):
    return get_schedule_with_usage(db=db, schedule_reference=schedule_reference)
