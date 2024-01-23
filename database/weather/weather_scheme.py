import uuid

from pydantic import BaseModel


class WeatherScheme(BaseModel):
    reference: uuid.UUID
    day: int
    weather: dict

    class Config:
        from_attributes = True
