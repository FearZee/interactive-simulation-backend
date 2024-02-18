import uuid

from pydantic import BaseModel


class ScheduleScheme(BaseModel):
    reference: uuid.UUID
    day: str
    heat_factor: float

    class Config:
        from_attributes = True


class CreateScheduleScheme(BaseModel):
    day: str
    heat_factor: float
