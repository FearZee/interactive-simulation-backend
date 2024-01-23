from pydantic import BaseModel


class BatteryScheme(BaseModel):
    capacity: float
    charge: float

    class Config:
        from_attributes = True


class UpdateBatteryScheme(BaseModel):
    charge: float
