import uuid

from fastapi import APIRouter, Depends

from database.weather.weather_service import get_weather_by_reference
from routes.get_db import get_db

weather_router = APIRouter()


@weather_router.get("/weather/{weather_reference}")
async def get_weather(weather_reference: uuid.UUID, db=Depends(get_db)):
    return get_weather_by_reference(db, weather_reference)
