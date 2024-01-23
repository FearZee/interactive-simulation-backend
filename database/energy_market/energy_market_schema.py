from pydantic import BaseModel


class EnergyMarketSchema(BaseModel):
    day: int
    price: dict

    class Config:
        from_attributes = True
