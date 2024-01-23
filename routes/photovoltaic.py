import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.battery.battery_service import get_battery_by_reference
from database.energy_market.energy_market_service import get_energy_market_by_reference
from database.photovoltaic.photovoltaic_scheme import CreatePhotovoltaicScheme
from database.photovoltaic.photovoltaic_service import (
    create_photovoltaic,
    calculate_solar_output_for_day,
    get_output_by_day,
)
from routes.get_db import get_db

pv_router = APIRouter()


@pv_router.get("/pv/battery/{battery_reference}")
async def getBattery(battery_reference: uuid.UUID, db: Session = Depends(get_db)):
    return get_battery_by_reference(db=db, battery_reference=battery_reference)


@pv_router.get("/pv/marketPrice/{marketPriceReference}")
async def getBattery(marketPriceReference: uuid.UUID, db: Session = Depends(get_db)):
    return get_energy_market_by_reference(db=db, reference=marketPriceReference)


@pv_router.get("/pv/{photovoltaic_id}/{day}")
async def get_pv(photovoltaic_id: uuid.UUID, day: int, db: Session = Depends(get_db)):
    return get_output_by_day(db=db, day=day, photovoltaic_reference=photovoltaic_id)


@pv_router.post("/pv/")
async def create_pv(
    photovoltaic: CreatePhotovoltaicScheme, db: Session = Depends(get_db)
):
    return create_photovoltaic(db=db, photovoltaic=photovoltaic)


@pv_router.post("/pv/{photovoltaic_id}/{day}")
async def create_pv(
    photovoltaic_id: uuid.UUID, day: int, db: Session = Depends(get_db)
):
    db_pv = calculate_solar_output_for_day(
        db=db, day=day, photovoltaic_reference=photovoltaic_id
    )
    return db_pv
