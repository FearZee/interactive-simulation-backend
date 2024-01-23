import uuid

from pydantic import BaseModel


class PhotovoltaicScheme(BaseModel):
    kilowatt_peak: float

    class Config:
        from_attributes = True


class CreatePhotovoltaicScheme(BaseModel):
    kilowatt_peak: float


class EnergyOutputScheme(BaseModel):
    day: int
    energy: dict
    photovoltaic_reference: uuid.UUID

    class Config:
        from_attributes = True
