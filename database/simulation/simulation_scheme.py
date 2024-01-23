import uuid

from pydantic import BaseModel


class SimulationScheme(BaseModel):
    reference: uuid.UUID
    day: int

    class Config:
        from_attribute = True


class SimulationResponseScheme(BaseModel):
    reference: uuid.UUID
    day: int

    photovoltaic_reference: uuid.UUID
    battery_reference: uuid.UUID
    weather_reference: uuid.UUID
    energy_market_reference: uuid.UUID

    class Config:
        from_attributes = True
