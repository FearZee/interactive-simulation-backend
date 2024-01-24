import uuid

from pydantic import BaseModel


class ScheduleScheme(BaseModel):
    reference: uuid.UUID
    day: str

    class Config:
        from_attributes = True


class CreateScheduleScheme(BaseModel):
    day: str

    class Config:
        from_attributes = True
